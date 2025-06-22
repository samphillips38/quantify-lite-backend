import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.account_data_service import get_accounts
from app.services.optimization_service import optimize_savings
from app.models import OptimizationInput, SavingsGoal

def run_debug_optimizer():
    """
    Runs the optimization service with test data for debugging purposes.
    """
    # 1. Get account data
    accounts = get_accounts()
    if not accounts:
        print("No accounts found. Exiting.")
        return

    # 2. Define optimization input
    # You can change these values to test different scenarios
    earnings = 125000.0  # Example: Higher rate taxpayer
    savings_goals = [
        SavingsGoal(amount=20000.0, horizon=0),
        # SavingsGoal(amount=30000.0, horizon=0),
    ]
    total_investment = sum(goal.amount for goal in savings_goals)
    isa_allowance_used = 5000.0 # Example: User has already used £5,000 of their ISA allowance.
    
    optimization_input = OptimizationInput(
        total_investment=total_investment,
        savings_goals=savings_goals,
        earnings=earnings,
        isa_allowance_used=isa_allowance_used
    )

    print(f"\n--- Running Optimizer with Test Data ---")
    print(f"  - Total Investment: £{total_investment:,.2f}")
    print(f"  - Annual Earnings: £{earnings:,.2f}")
    print(f"  - ISA Allowance Used: £{isa_allowance_used:,.2f}")
    print("  - Savings Goals:")
    for goal in savings_goals:
        print(f"    - Amount: £{goal.amount:,.2f}, Horizon: {goal.horizon} months")
    print("----------------------------------------\n")

    # 3. Run the optimization
    result = optimize_savings(optimization_input, accounts)

    # 4. Print the results
    print("\n--- Optimization Results ---")
    if result.status == "Optimal":
        print(f"Status: {result.status}")
        print(f"Total Estimated Post-Tax Return: £{result.total_return:,.2f}")
        print("\nInvestment Allocation:")
        for investment in result.investments:
            isa_tag = " (ISA)" if investment.is_isa else ""
            print(f"  - {investment.account_name}{isa_tag}: £{investment.amount:,.2f} @ {investment.aer}% AER [{investment.term}]")
    else:
        print(f"Optimization failed. Status: {result.status}")
    print("-------------------------\n")


if __name__ == "__main__":
    run_debug_optimizer() 