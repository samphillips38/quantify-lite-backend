from pyomo.environ import ConcreteModel, Var, Objective, Constraint, SolverFactory, NonNegativeReals, value, ConstraintList
from app.models import OptimizationInput, Account, OptimizationResult, Investment
from typing import List

def optimize_savings(input_data: OptimizationInput, accounts: List[Account]) -> OptimizationResult:
    """
    Optimises savings allocation using Pyomo.
    """
    print("Starting optimization...")

    model = ConcreteModel()

    # --- Define variables ---
    # Create a variable for each account representing the amount to invest
    model.investments = Var([acc.name for acc in accounts], domain=NonNegativeReals)

    # --- Define Objective Function ---
    # Maximize the total interest earned
    def objective_rule(m):
        return sum(m.investments[acc.name] * acc.interest_rate for acc in accounts)
    model.objective = Objective(rule=objective_rule, sense=-1) # sense=-1 for maximization

    # --- Define Constraints ---
    # 1. Total investment constraint
    def total_investment_rule(m):
        return sum(m.investments[acc.name] for acc in accounts) <= input_data.total_investment
    model.total_investment_constraint = Constraint(rule=total_investment_rule)

    # 2. Individual account investment limits
    model.investment_limits = ConstraintList()
    for acc in accounts:
        # Min investment constraint
        # model.investment_limits.add(model.investments[acc.name] >= acc.min_investment) For now ignore min investment
        # Max investment constraint
        model.investment_limits.add(model.investments[acc.name] <= acc.max_investment)

    # 3. ISA investment limit (example constraint, e.g. £20,000 per year)
    isa_accounts = [acc.name for acc in accounts if 'isa' in acc.account_type]
    if isa_accounts:
        def isa_limit_rule(m):
            return sum(m.investments[acc_name] for acc_name in isa_accounts) <= 20000
        model.isa_limit_constraint = Constraint(rule=isa_limit_rule)
    
    print("Pyomo model created. Solving...")

    # --- Solve the model ---
    # Make sure you have a solver installed, e.g., glpk or cbc
    # On ubuntu: sudo apt-get install glpk-utils
    # pyomo can install cbc: pip install pyomo[cbc]
    # On mac: brew install glpk
    solver = SolverFactory('glpk') 
    results = solver.solve(model)
    
    print(f"Solver status: {results.solver.status}, termination condition: {results.solver.termination_condition}")

    # --- Process results ---
    if str(results.solver.termination_condition) == "optimal":
        investments = []
        total_return = 0
        for acc in accounts:
            amount = value(model.investments[acc.name])
            if amount > 1e-6: # Only include accounts with non-trivial investment
                is_isa = 'isa' in acc.account_type
                term = "Easy access"
                if '1 month' in acc.name:
                    term = "1 month"
                elif '3 months' in acc.name:
                    term = "3 months"
                elif '6 months' in acc.name:
                    term = "6 months"
                elif '1 year' in acc.name:
                    term = "1 year"
                elif '2 years' in acc.name:
                    term = "2 years"
                elif '3 years' in acc.name:
                    term = "3 years"
                elif '5 years' in acc.name:
                    term = "5 years"

                url = acc.url if acc.url else f"https://www.google.com/search?q={acc.name.replace(' ', '+')}"

                investments.append(Investment(
                    account_name=acc.name,
                    amount=round(amount, 2),
                    aer=round(acc.interest_rate * 100, 2),
                    term=term,
                    is_isa=is_isa,
                    url=url,
                    platform=acc.platform
                ))
                total_return += amount * acc.interest_rate
        
        return OptimizationResult(
            investments=investments,
            total_return=round(total_return, 2),
            status="Optimal"
        )
    else:
        return OptimizationResult(
            investments=[],
            total_return=0,
            status=f"Optimization failed. Status: {results.solver.termination_condition}"
        ) 