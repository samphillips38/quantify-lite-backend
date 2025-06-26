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
FLAGSTONE_API_URL = "https://clients.direct.flagstoneim.com/api/earlyaccess/product-availability?pageNumber=1&pageSize=16&accountType=0&OrderBy=ProductIssue.Aer&OrderAscending=False"

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

def _get_flagstone_account_type(item: dict) -> str:
    """Determines the account type from the Flagstone data."""
    term_type = item.get("termType", "").lower()
    if term_type == "fixedterm":
        return "fixed_term"
    elif term_type == "instantaccess":
        return "easy_access"
    elif term_type == "notice":
        return "notice"
    else:
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
                platform="Hargreaves Lansdown",
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
                platform="Raisin",
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

def _get_flagstone_accounts() -> list[Account]:
    """
    Fetches savings account data from the Flagstone API.
    """
    print("Fetching account data from Flagstone API...")
    try:
        response = requests.get(FLAGSTONE_API_URL, headers={
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Cookie': 'ai_user=hqfKBdgZwHz/aobb407XJe|2025-06-26T00:53:03.693Z; _hp2_props.788385597=%7B%22AppVersion%22%3A%22clients-1.1.1088%22%7D; _hjSessionUser_1267098=eyJpZCI6IjBiOTc2MDc1LWE0YTEtNTYzMS1hOWMwLWQ1NzE2ZDA4YjI1ZSIsImNyZWF0ZWQiOjE3NTA4OTkxODY0ODgsImV4aXN0aW5nIjp0cnVlfQ==; _gcl_au=1.1.1383932666.1750900396; _ga=GA1.1.2132377510.1750900397; __adal_ca=so%3DGoogle%26me%3Dorganic%26ca%3D%28not%2520set%29%26co%3D%28not%2520set%29%26ke%3D%28not%2520set%29%26cg%3DOrganic; __adal_cw=1750900396829; _uc_referrer=https%3A//www.google.com/; _uc_last_referrer=https%3A//www.google.com/; _uc_initial_landing_page=https%3A//www.flagstoneim.com/; _fbp=fb.1.1750900396883.283680187126926992; __adal_id=d43fb037-6e2e-4fee-9b59-8ac91f186b7f.1750900397.2.1750900448.1750900397.2991b1c8-4015-4a0d-8658-dc72da8e2427; _hp2_id.788385597=%7B%22userId%22%3A%224572292114282934%22%2C%22pageviewId%22%3A%224994901359487215%22%2C%22sessionId%22%3A%227553574703643701%22%2C%22identity%22%3Anull%2C%22trackerVersion%22%3A%224.0%22%7D; _uetsid=bd748d00522a11f0af017122d7169282; _uetvid=bd758be0522a11f080d359d6b3af7ef2; ABTasty=uid=jw9vbx2s7k5xxtt0&fst=1750899187505&pst=-1&cst=1750899187505&ns=1&pvt=6&pvis=6&th=; _ga_D0D2SJSVPD=GS2.1.s1750900396$o1$g1$t1750900449$j7$l0$h0; _ga_XYXYXYXYXY=GS2.1.s1750900396$o1$g1$t1750900450$j6$l0$h197157914; ai_session=8/hi9via9LBkmEhWaYefCX|1750917516395|1750917517041',
            'Referer': 'https://clients.direct.flagstoneim.com/?utm_source=google&utm_medium=cpc&utm_campaign=Search_Cash-Platform_All&utm_content=AG-Cash-Management-PlatformKWD-cash-management-platformMT-Phrase&gclid=CjwKCAjwvO7CBhAqEiwA9q2YJYmw8X5DFB0vNjlM3vHYVDjjllms7ekUB-lTZuI5Nw5dwgGm45gtgRoCrGQQAvD_BwE&_gl=1*1uoxwna*_gcl_aw*R0NMLjE3NTA4OTkwNDAuQ2p3S0NBand2TzdDQmhBcUVpd0E5cTJZSlltdzhYNURGQjB2TmpsTTN2SFlWRGpqbGxtczdla1VCLWxUWnVJNU53NWR3Z0dtNDVndGdSb0NyR1FRQXZEX0J3RQ..*_gcl_au*MTY0NTc2MTEzLjE3NTA4OTkwNDA.*_ga*MTQyNDc2NDk3LjE3NTA4OTkwNDA.*_ga_D0D2SJSVPD*czE3NTA4OTkwMzkkbzEkZzAkdDE3NTA4OTkwMzkkajYwJGwwJGgw',
            'Request-Id': '|636c765f1b614091976da6954123b08c.f833d4d3da394b6c',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'traceparent': '00-636c765f1b614091976da6954123b08c-f833d4d3da394b6c-01',
            'x-csrf': '1',
        })
        response.raise_for_status()
        data = response.json()
        accounts = []
        for item in data.get("productItems", []):
            # Use the first product issue that is not closed to new clients
            product_issues = [pi for pi in item.get("productIssues", []) if not pi.get("isClosedToNewClients", False)]
            if not product_issues:
                continue
            issue = product_issues[0]
            aer = issue.get("aer", 0)
            min_investment = issue.get("depositPerClientMinimum", 0)
            max_investment = issue.get("depositPerClientMaximum", float('inf'))
            term = item.get("termLength", 0)
            # For notice accounts, use noticeLength as term if termLength is 0
            if _get_flagstone_account_type(item) == "notice":
                term = item.get("noticeLength", 0)
            url = None
            if issue.get("tAndCs"):
                url = issue["tAndCs"].get("uri")
            account = Account(
                name=f"{item.get('financialInstitution', {}).get('name', '')} {item.get('termType', '')}".strip(),
                interest_rate=aer / 100,
                account_type=_get_flagstone_account_type(item),
                platform="Flagstone",
                min_investment=min_investment,
                max_investment=max_investment,
                term=term,
                url=url
            )
            accounts.append(account)
        print(f"Found {len(accounts)} Flagstone accounts.")
        return accounts
    except requests.exceptions.RequestException as e:
        print(f"Error fetching account data from Flagstone API: {e}")
        return []

def get_accounts() -> List[Account]:
    """
    Fetches savings account data from all available sources.
    """
    hl_accounts = _get_hl_accounts()
    raisin_accounts = _get_raisin_accounts()
    flagstone_accounts = _get_flagstone_accounts()
    all_accounts = hl_accounts + raisin_accounts + flagstone_accounts
    print(f"Found a total of {len(all_accounts)} accounts.")
    return all_accounts
