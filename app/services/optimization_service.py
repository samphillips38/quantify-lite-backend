from pyomo.environ import ConcreteModel, Var, Objective, Constraint, SolverFactory, NonNegativeReals, value, ConstraintList
from app.models import OptimizationInput, Account, OptimizationResult, Investment, Summary
from typing import List

def _get_tax_info(earnings: float) -> dict:
    """
    Determines Personal Savings Allowance and tax rate based on earnings.
    Note: This is a simplified model for UK tax (excluding Scotland).
    """
    if earnings is None: # If earnings not provided, assume basic rate tax payer for conservative estimate.
        return {'psa': 1000, 'tax_rate': 0.20, 'band': 'Basic Rate'}
    if earnings <= 50270:
        # Basic rate taxpayer
        return {'psa': 1000, 'tax_rate': 0.20, 'band': 'Basic Rate'}
    elif earnings <= 125140:
        # Higher rate taxpayer
        return {'psa': 500, 'tax_rate': 0.40, 'band': 'Higher Rate'}
    else:
        # Additional rate taxpayer
        return {'psa': 0, 'tax_rate': 0.45, 'band': 'Additional Rate'}


def _get_starting_rate_for_savings(earnings: float) -> float:
    """
    Calculates the Starting Rate for Savings band based on non-savings income.
    https://www.gov.uk/apply-tax-free-interest-on-savings
    """
    if earnings is None:
        return 0.0

    personal_allowance = 12570
    max_starting_rate_band = 5000

    if earnings >= (personal_allowance + max_starting_rate_band):
        # If income is £17,570 or more, no starting rate is available.
        return 0.0

    if earnings <= personal_allowance:
        # If income is below the personal allowance, the full band is available.
        return float(max_starting_rate_band)

    # If income is between PA and PA + max_starting_rate_band, the band is reduced.
    reduction = earnings - personal_allowance
    starting_rate_band = max(0.0, max_starting_rate_band - reduction)
    return starting_rate_band


def optimize_savings(input_data: OptimizationInput, accounts: List[Account]) -> OptimizationResult:
    """
    Optimises savings allocation using Pyomo.
    """
    print("Starting optimization...")

    # --- Pre-computation ---
    # 1. Determine tax information
    tax_info = _get_tax_info(input_data.earnings)
    psa = tax_info['psa']
    tax_rate = tax_info['tax_rate']
    starting_rate_for_savings = _get_starting_rate_for_savings(input_data.earnings)
    total_tax_free_allowance = psa + starting_rate_for_savings
    isa_allowance_remaining = 20000.0 - (input_data.isa_allowance_used or 0.0)

    # 2. Determine investment horizon from savings goals
    goal_horizons_years = [g.horizon / 12.0 for g in input_data.savings_goals]
    max_horizon_years = max(goal_horizons_years) if goal_horizons_years else 0
    
    # The term for filtering accounts is the max of 1 year or the longest goal horizon.
    investment_term_years = max(1, max_horizon_years)

    # 3. Filter accounts based on the investment term
    eligible_accounts = [
        acc for acc in accounts 
        if acc.term == 0 or (acc.term / 12) <= investment_term_years
    ]

    if not eligible_accounts:
        return OptimizationResult(
            investments=[],
            summary=None,
            status="No eligible accounts found for the given investment horizon."
        )

    model = ConcreteModel()

    # --- Define variables ---
    model.investments = Var([acc.name for acc in eligible_accounts], domain=NonNegativeReals)
    model.taxable_interest = Var(domain=NonNegativeReals)
    model.tax_free_interest_non_isa = Var(domain=NonNegativeReals)

    # --- Define Objective Function ---
    # Maximize post-tax annual interest
    non_isa_accounts = [acc for acc in eligible_accounts if 'isa' not in acc.account_type]
    isa_accounts = [acc for acc in eligible_accounts if 'isa' in acc.account_type]

    def objective_rule(m):
        total_isa_interest = sum(m.investments[acc.name] * acc.interest_rate for acc in isa_accounts)
        post_tax_non_isa_interest = m.tax_free_interest_non_isa + m.taxable_interest * (1 - tax_rate)
        final_remaining_isa_allowance = isa_allowance_remaining - sum(m.investments[acc.name] for acc in isa_accounts)
        return total_isa_interest + post_tax_non_isa_interest + final_remaining_isa_allowance * 2e-7
    model.objective = Objective(rule=objective_rule, sense=-1) # Maximising, with a small penalty (< £0.004) for using up the ISA allowance

    # --- Define Constraints ---
    # 1. Total investment constraint: must invest the full amount
    def total_investment_rule(m):
        return sum(m.investments[acc.name] for acc in eligible_accounts) == input_data.total_investment
    model.total_investment_constraint = Constraint(rule=total_investment_rule)

    # 2. Horizon-based investment constraints.
    # These constraints ensure that funds are available at the required time for each goal.
    model.horizon_constraints = ConstraintList()
    unique_horizons = sorted(list(set(g.horizon for g in input_data.savings_goals)))

    for horizon_months in unique_horizons:
        cumulative_goal_amount = sum(g.amount for g in input_data.savings_goals if g.horizon == horizon_months)
        
        relevant_accounts = [acc.name for acc in eligible_accounts if acc.term == horizon_months]

        expr = sum(model.investments[acc_name] for acc_name in relevant_accounts) == cumulative_goal_amount
        model.horizon_constraints.add(expr)

    # 3. Non-ISA interest split for tax calculation
    def non_isa_interest_rule(m):
        total_non_isa_interest = sum(m.investments[acc.name] * acc.interest_rate for acc in non_isa_accounts)
        return m.taxable_interest + m.tax_free_interest_non_isa == total_non_isa_interest
    model.non_isa_interest_constraint = Constraint(rule=non_isa_interest_rule)

    # 4. Total tax-free allowance limit (PSA + Starting Rate for Savings)
    def tax_free_limit_rule(m):
        return m.tax_free_interest_non_isa <= total_tax_free_allowance
    model.tax_free_limit = Constraint(rule=tax_free_limit_rule)

    # 5. Individual account investment limits
    model.investment_limits = ConstraintList()
    for acc in eligible_accounts:
        model.investment_limits.add(model.investments[acc.name] <= acc.max_investment)

    # 6. ISA investment limit
    if isa_accounts:
        def isa_limit_rule(m):
            return sum(m.investments[acc_name] for acc_name in [acc.name for acc in isa_accounts]) <= isa_allowance_remaining
        model.isa_limit_constraint = Constraint(rule=isa_limit_rule)
    
    print("Pyomo model created. Solving...")

    solver = SolverFactory('glpk') 
    results = solver.solve(model)
    
    print(f"Solver status: {results.solver.status}, termination condition: {results.solver.termination_condition}")

    if str(results.solver.termination_condition) == "optimal":
        investments = []
        total_gross_return = 0
        for acc in eligible_accounts:
            amount = value(model.investments[acc.name])
            if amount > 1e-6:
                investments.append(Investment(
                    account_name=acc.name,
                    amount=round(amount, 2),
                    aer=round(acc.interest_rate * 100, 2),
                    term=f"{acc.term} months" if acc.term > 0 else "Easy access",
                    is_isa='isa' in acc.account_type,
                    url=acc.url or f"https://www.google.com/search?q={acc.name.replace(' ', '+')}",
                    platform=acc.platform
                ))
                total_gross_return += amount * acc.interest_rate
        
        # Calculate post-tax return for the final result
        non_isa_gross_return = sum(inv.amount * (inv.aer / 100) for inv in investments if not inv.is_isa)
        taxable_return = max(0, non_isa_gross_return - total_tax_free_allowance)
        tax_paid = taxable_return * tax_rate
        total_net_return = total_gross_return - tax_paid

        total_investment = input_data.total_investment
        net_effective_aer = (total_net_return / total_investment) * 100 if total_investment > 0 else 0

        summary = Summary(
            total_investment=round(total_investment, 2),
            gross_annual_interest=round(total_gross_return, 2),
            net_annual_interest=round(total_net_return, 2),
            net_effective_aer=round(net_effective_aer, 2),
            tax_due=round(tax_paid, 2),
            tax_band=tax_info['band'],
            personal_savings_allowance=tax_info['psa']
        )

        return OptimizationResult(
            investments=investments,
            summary=summary,
            status="Optimal"
        )
    else:
        return OptimizationResult(
            investments=[],
            summary=None,
            status=f"Optimization failed. Status: {results.solver.termination_condition}"
        ) 