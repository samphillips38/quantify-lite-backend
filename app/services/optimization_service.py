from pyomo.environ import ConcreteModel, Var, Objective, Constraint, SolverFactory, NonNegativeReals, value, ConstraintList
from app.models import OptimizationInput, Account, OptimizationResult, Investment, Summary
from typing import List

# Raisin referral link
RAISIN_REFERRAL_LINK = "https://www.raisin.com/en-gb/referral/?raf=a0495aca4e4081660f489a2c0d43c67087de8602&utm_source=transactional&utm_campaign=mandrill_customer-referral"

def _get_provider_signup_url(platform: str) -> str:
    """
    Returns the sign-up URL for a given platform.
    If platform is not recognized, returns a generic search URL.
    """
    provider_urls = {
        "Hargreaves Lansdown": "https://www.hl.co.uk/register",
        "Raisin": "https://www.raisin.co.uk/register",
        "Flagstone": "https://www.flagstoneim.com/register"
    }
    return provider_urls.get(platform, f"https://www.google.com/search?q={platform.replace(' ', '+')}+sign+up")

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
    other_savings_income = input_data.other_savings_income or 0.0
    total_tax_free_allowance_remaining = max(0, total_tax_free_allowance - other_savings_income)
    isa_allowance_remaining = 20000.0 - (input_data.isa_allowance_used or 0.0)

    # 2. Remove any accounts from excluded providers
    excluded_providers = input_data.excluded_providers or []
    if excluded_providers:
        excluded_lower = {p.lower() for p in excluded_providers}
        accounts = [acc for acc in accounts if acc.platform.lower() not in excluded_lower]
        print(f"After excluding providers {excluded_providers}: {len(accounts)} accounts remaining.")

    # 3. Remove any accounts with term greater than the maximum savings goal
    max_horizon = max(g.horizon for g in input_data.savings_goals)
    eligible_accounts = [
        acc for acc in accounts
        if acc.term == 0 or acc.term <= max_horizon
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
    # For fixed_term accounts: term must exactly match the goal horizon
    # For notice accounts: notice period (term) must be <= goal horizon (can give notice early)
    # For easy_access accounts (term=0): can be used for any horizon
    model.horizon_constraints = ConstraintList()
    unique_horizons = sorted(list(set(g.horizon for g in input_data.savings_goals)))

    for horizon_months in unique_horizons:
        cumulative_goal_amount = sum(g.amount for g in input_data.savings_goals if g.horizon == horizon_months)
        
        # For each horizon, find accounts that can provide funds at that time:
        # - Easy access (term=0): always available
        # - Fixed term: term must exactly match horizon
        # - Notice: notice period (term) must be <= horizon (can give notice early)
        relevant_accounts = []
        for acc in eligible_accounts:
            if acc.term == 0:  # Easy access
                relevant_accounts.append(acc.name)
            elif acc.account_type == "notice":  # Notice accounts: can give notice early
                if acc.term <= horizon_months:
                    relevant_accounts.append(acc.name)
            elif acc.account_type == "fixed_term":  # Fixed term: must match exactly
                if acc.term == horizon_months:
                    relevant_accounts.append(acc.name)
            # For other account types, use exact match (backward compatibility)
            elif acc.term == horizon_months:
                relevant_accounts.append(acc.name)

        expr = sum(model.investments[acc_name] for acc_name in relevant_accounts) == cumulative_goal_amount
        model.horizon_constraints.add(expr)

    # 3. Non-ISA interest split for tax calculation
    def non_isa_interest_rule(m):
        total_non_isa_interest = sum(m.investments[acc.name] * acc.interest_rate for acc in non_isa_accounts)
        return m.taxable_interest + m.tax_free_interest_non_isa == total_non_isa_interest
    model.non_isa_interest_constraint = Constraint(rule=non_isa_interest_rule)

    # 4. Total tax-free allowance limit (PSA + Starting Rate for Savings) - current savings income
    def tax_free_limit_rule(m):
        return m.tax_free_interest_non_isa <= total_tax_free_allowance_remaining
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
                # Format term display based on account type
                if acc.term == 0:
                    term_display = "Easy access"
                elif acc.account_type == "notice":
                    term_display = f"Notice: {acc.term} months"
                else:
                    term_display = f"{acc.term} months"
                
                investment_amount = round(amount, 2)
                base_url = acc.url or _get_provider_signup_url(acc.platform)
                # Apply referral link to all Raisin accounts
                final_url = RAISIN_REFERRAL_LINK if acc.platform == "Raisin" else base_url
                
                investments.append(Investment(
                    account_name=acc.name,
                    amount=investment_amount,
                    aer=round(acc.interest_rate * 100, 2),
                    term=term_display,
                    is_isa='isa' in acc.account_type,
                    url=final_url,
                    platform=acc.platform,
                    account_type=acc.account_type
                ))
                total_gross_return += amount * acc.interest_rate
        
        # Calculate post-tax return for the final result
        non_isa_gross_return = sum(inv.amount * (inv.aer / 100) for inv in investments if not inv.is_isa)
        untaxable_non_isa_return = value(model.tax_free_interest_non_isa)
        taxable_return = max(0, non_isa_gross_return - untaxable_non_isa_return)
        tax_paid = taxable_return * tax_rate
        total_net_return = total_gross_return - tax_paid

        total_investment = input_data.total_investment
        net_effective_aer = (total_net_return / total_investment) * 100 if total_investment > 0 else 0
        
        # Calculate equivalent pre-tax rate
        # This is the rate needed on a normal savings account to get the same after-tax return
        if total_investment > 0 and tax_rate < 1.0:
            equivalent_pre_tax_rate = ((total_net_return - untaxable_non_isa_return) / (1 - tax_rate) + untaxable_non_isa_return) / total_investment * 100
        else:
            equivalent_pre_tax_rate = net_effective_aer  # Fallback to net AER if calculation not possible

        summary = Summary(
            total_investment=round(total_investment, 2),
            gross_annual_interest=round(total_gross_return, 2),
            net_annual_interest=round(total_net_return, 2),
            net_effective_aer=round(net_effective_aer, 2),
            tax_due=round(tax_paid, 2),
            tax_band=tax_info['band'],
            personal_savings_allowance=tax_info['psa'],
            tax_rate=tax_rate,
            tax_free_allowance_remaining=round(total_tax_free_allowance_remaining, 2),
            equivalent_pre_tax_rate=round(equivalent_pre_tax_rate, 2)
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