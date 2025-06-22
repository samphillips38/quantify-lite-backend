import requests
from app.models import Account
from typing import List
import os

# In a real application, this would fetch data from a financial API
# You would need to handle API keys, error handling, and data parsing.
# For example:
# API_URL = "https://api.example.com/savings-accounts"
# API_KEY = os.environ.get("SAVINGS_API_KEY")

API_URL = "https://www.hl.co.uk/ajax/saving/latest-rates"

def _get_account_type(instrument: dict) -> str:
    """Determines the account type from the instrument data."""
    base_type = ""
    if instrument.get("instrumentCode") == "FIXED_TERM_FIXED_DATES":
        base_type = "fixed_term"
    elif instrument.get("instrumentCode") == "EASY_ACCESS":
        base_type = "variable_access"
    else:
        base_type = "other"

    if instrument.get("productCode") == "53":
        return f"{base_type}_isa"
    return base_type

def get_accounts() -> List[Account]:
    """
    Fetches savings account data from the HL API.
    """
    print("Fetching account data from HL API...")
    
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        
        accounts = []
        for item in data.get("instruments", []):
            # Skip items that are not published
            if item.get("status") != "PUBLISHED":
                continue

            aer = item.get("aer", 0) or 0

            account = Account(
                name=f"{item.get('bankName', '')} {item.get('bankInstrumentName', '')}".strip(),
                interest_rate=aer / 100,
                account_type=_get_account_type(item),
                min_investment=item.get("minBalance") or item.get("minInvestment") or 0,
                max_investment=item.get("maxBalance") or float('inf')
            )
            accounts.append(account)
        
        print(f"Found {len(accounts)} accounts.")
        return accounts

    except requests.exceptions.RequestException as e:
        print(f"Error fetching account data from API: {e}")
        return [] # Return empty list or handle error as appropriate

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