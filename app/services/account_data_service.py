import requests
from app.models import Account
from typing import List

# In a real application, this would fetch data from a financial API
# You would need to handle API keys, error handling, and data parsing.
# For example:
# API_URL = "https://api.example.com/savings-accounts"
# API_KEY = os.environ.get("SAVINGS_API_KEY")

def get_accounts() -> List[Account]:
    """
    Fetches savings account data.
    Currently returns mock data.
    """
    print("Fetching account data (using mock data for now)...")
    
    # Mock data representing different account types
    mock_accounts = [
        Account(name="Easy Access Saver", interest_rate=0.05, account_type="variable_access", max_investment=250000),
        Account(name="Fixed Rate Bond 1 Year", interest_rate=0.065, account_type="fixed_term", max_investment=100000),
        Account(name="Easy Access ISA", interest_rate=0.055, account_type="variable_access_isa", max_investment=20000),
        Account(name="Fixed Rate ISA 2 Year", interest_rate=0.07, account_type="fixed_term_isa", max_investment=20000),
        Account(name="Super Saver", interest_rate=0.04, account_type="variable_access", min_investment=1000, max_investment=500000),
    ]
    
    print(f"Found {len(mock_accounts)} accounts.")
    return mock_accounts

# Example of what a real implementation might look like
# def get_accounts_from_api() -> List[Account]:
#     try:
#         headers = {"Authorization": f"Bearer {API_KEY}"}
#         response = requests.get(API_URL, headers=headers)
#         response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
#         
#         accounts_data = response.json()
#         
#         accounts = []
#         for item in accounts_data:
#             account = Account(
#                 name=item.get('name'),
#                 interest_rate=item.get('interest_rate'),
#                 account_type=item.get('account_type'),
#                 min_investment=item.get('min_investment', 0),
#                 max_investment=item.get('max_investment', float('inf'))
#             )
#             accounts.append(account)
#         return accounts
#
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching account data from API: {e}")
#         return [] # Return empty list or handle error as appropriate 