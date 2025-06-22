import requests
from app.models import Account
from typing import List
import os

# In a real application, this would fetch data from a financial API
# You would need to handle API keys, error handling, and data parsing.
# For example:
# API_URL = "https://api.example.com/savings-accounts"
# API_KEY = os.environ.get("SAVINGS_API_KEY")

HL_API_URL = "https://www.hl.co.uk/ajax/saving/latest-rates"
RAISIN_API_URL = "http://api2.raisin.co.uk/dbs/v1/public/products?distributor_id=Raisin&distribution_channel_id=raisin_direct_retail_gbr"

def _get_account_type(instrument: dict) -> str:
    """Determines the account type from the instrument data."""
    base_type = ""
    if instrument.get("instrumentCode") == "FIXED_TERM_FIXED_DATES":
        base_type = "fixed_term"
    elif instrument.get("instrumentCode") == "EASY_ACCESS":
        base_type = "easy_access"
    else:
        base_type = "other"

    if instrument.get("productCode") == "53":
        return f"{base_type}_isa"
    return base_type

def _get_raisin_account_type(instrument: dict) -> str:
    """Determines the account type from the Raisin instrument data."""
    product_type = instrument.get("product_type", "").lower()
    if product_type == "term":
        return "fixed_term"
    elif product_type == "overnight":
        return "easy_access"
    
    # Note: No clear ISA indicator in the sample data, so we're not creating ISA types for Raisin.
    return "other"

def _get_hl_accounts() -> list[Account]:
    """
    Fetches savings account data from the HL API.
    """
    print("Fetching account data from HL API...")
    
    try:
        response = requests.get(HL_API_URL)
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
                max_investment=item.get("maxBalance") or float('inf'),
                term=item.get("term", 0) or 0,
                url=None
            )
            accounts.append(account)
        
        print(f"Found {len(accounts)} HL accounts.")
        return accounts

    except requests.exceptions.RequestException as e:
        print(f"Error fetching account data from HL API: {e}")
        return [] # Return empty list or handle error as appropriate

def _get_raisin_accounts() -> list[Account]:
    """
    Fetches savings account data from the Raisin API.
    """
    print("Fetching account data from Raisin API...")
    
    try:
        response = requests.get(RAISIN_API_URL)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        
        accounts = []
        for item in data.get("entries", []):
            aer = float(item.get("interest_rates", {}).get("interest_rate_effective", 0))

            term_months = 0
            if item.get("term_normalized"):
                term_months = item.get("term_normalized", {}).get("months", 0)

            url = None
            for doc in item.get("pre_contractual_documents", []):
                if doc.get("document_type") == "PRODUCT_INFORMATION_SHEET":
                    url = doc.get("url")
                    break

            account = Account(
                name=f"{item.get('deposit_taking_bank', {}).get('name', '')} {item.get('product_type', '')}".strip(),
                interest_rate=aer / 100,
                account_type=_get_raisin_account_type(item),
                min_investment=float(item.get("conditions", {}).get("minimum_balance", 0)),
                max_investment=float(item.get("conditions", {}).get("maximum_balance", float('inf'))),
                term=term_months,
                url=url
            )
            accounts.append(account)
        
        print(f"Found {len(accounts)} Raisin accounts.")
        return accounts

    except requests.exceptions.RequestException as e:
        print(f"Error fetching account data from Raisin API: {e}")
        return []

def get_accounts() -> List[Account]:
    """
    Fetches savings account data from all available sources.
    """
    hl_accounts = _get_hl_accounts()
    raisin_accounts = _get_raisin_accounts()
    
    all_accounts = hl_accounts + raisin_accounts
    print(f"Found a total of {len(all_accounts)} accounts.")
    
    return all_accounts

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