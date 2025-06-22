import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.account_data_service import get_accounts
from app.services.optimization_service import optimize_savings
from app.models import OptimizationInput

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
    # You can change this value to test different scenarios
    total_investment = 100000.0  
    optimization_input = OptimizationInput(total_investment=total_investment)
    print(f"\nRunning optimizer with total investment: £{total_investment:,.2f}\n")

    # 3. Run the optimization
    result = optimize_savings(optimization_input, accounts)

    # 4. Print the results
    print("\n--- Optimization Results ---")
    if result.status == "Optimal":
        print(f"Status: {result.status}")
        print(f"Total Estimated Return: £{result.total_return:,.2f}")
        print("\nInvestment Allocation:")
        for investment in result.investments:
            print(f"  - {investment.account_name}: £{investment.amount:,.2f} @ {investment.aer}% AER")
    else:
        print(f"Optimization failed. Status: {result.status}")
    print("-------------------------\n")


if __name__ == "__main__":
    run_debug_optimizer() 