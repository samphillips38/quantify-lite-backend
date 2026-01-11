"""
Provider-specific account implementations.
Each class encapsulates the parsing logic for its respective provider's API format.
"""
from typing import Optional
from app.models import Account


class RaisinAccount(Account):
    """
    Account implementation for Raisin platform.
    Handles parsing of Raisin API response format.
    """
    
    @classmethod
    def _get_account_type(cls, instrument: dict) -> str:
        """Determines the account type from the Raisin instrument data."""
        product_type = instrument.get("product_type", "").lower()
        if product_type == "term":
            return "fixed_term"
        elif product_type == "overnight":
            return "easy_access"
        elif product_type == "notice":
            return "notice"
        return "other"
    
    @classmethod
    def _extract_notice_period_months(cls, item: dict) -> int:
        """
        Extracts notice period from Raisin account data and converts to months.
        For NOTICE accounts, the notice period is typically in the withdrawal conditions.
        Returns 0 if no notice period is found or if it's not a notice account.
        """
        product_type = item.get("product_type", "").lower()
        if product_type != "notice":
            return 0
        
        conditions = item.get("conditions", {})
        withdrawal = conditions.get("withdrawal", {})
        
        # Check for notice_period in withdrawal conditions
        notice_period = withdrawal.get("notice_period")
        if notice_period:
            # If it's a dict with unit and period
            if isinstance(notice_period, dict):
                unit = notice_period.get("unit", "").lower()
                period = notice_period.get("period")
                if period:
                    if unit in ["month", "months"]:
                        return int(period)
                    elif unit in ["day", "days"]:
                        # Convert days to months (using 30.44 days per month average)
                        return int(period / 30.44)
            # If it's a number (assume days)
            elif isinstance(notice_period, (int, float)):
                return int(notice_period / 30.44)
            # If it's a string representation
            elif isinstance(notice_period, str):
                try:
                    days = float(notice_period)
                    return int(days / 30.44)
                except (ValueError, TypeError):
                    pass
        
        # Check term field structure (some notice accounts might have it here)
        term = item.get("term")
        if term and isinstance(term, dict):
            unit = term.get("unit")
            period = term.get("period")
            if period and unit:
                unit_lower = str(unit).lower() if unit else ""
                if unit_lower in ["month", "months"]:
                    return int(period)
                elif unit_lower in ["day", "days"]:
                    return int(period / 30.44)
        
        # Default: if it's a notice account but no period found, assume 1 month (30 days)
        # This is a fallback - in practice, notice periods should be specified
        return 1
    
    @classmethod
    def from_api_data(cls, data: dict) -> Optional[Account]:
        """
        Creates a RaisinAccount from Raisin API response data.
        
        Args:
            data: Dictionary from Raisin API 'entries' array
            
        Returns:
            RaisinAccount instance or None if data is invalid
        """
        try:
            aer = float(data.get("interest_rates", {}).get("interest_rate_effective", 0))
            if aer <= 0:
                return None  # Skip accounts with invalid interest rates
            
            account_type = cls._get_account_type(data)
            
            # Determine term_months based on account type
            if account_type == "notice":
                term_months = cls._extract_notice_period_months(data)
            else:
                # For fixed term accounts, use term_normalized
                term_months = 0
                if data.get("term_normalized"):
                    term_months = data.get("term_normalized", {}).get("months", 0)
            
            # Extract URL from pre_contractual_documents
            url = None
            for doc in data.get("pre_contractual_documents", []):
                if doc.get("document_type") == "PRODUCT_INFORMATION_SHEET":
                    url = doc.get("url")
                    break
            
            return cls(
                name=f"{data.get('deposit_taking_bank', {}).get('name', '')} {data.get('product_type', '')}".strip(),
                interest_rate=aer / 100,
                account_type=account_type,
                platform="Raisin",
                min_investment=float(data.get("conditions", {}).get("minimum_balance", 0)),
                max_investment=float(data.get("conditions", {}).get("maximum_balance", float('inf'))),
                term=term_months,
                url=url
            )
        except (ValueError, TypeError, KeyError) as e:
            # Log error in production, but for now just skip invalid entries
            print(f"Error parsing Raisin account data: {e}")
            return None


class HLAccount(Account):
    """
    Account implementation for Hargreaves Lansdown platform.
    Handles parsing of HL API response format.
    """
    
    @classmethod
    def _get_account_type(cls, instrument: dict) -> str:
        """Determines the account type from the HL instrument data."""
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
    
    @classmethod
    def from_api_data(cls, data: dict) -> Optional[Account]:
        """
        Creates an HLAccount from HL API response data.
        
        Args:
            data: Dictionary from HL API 'instruments' array
            
        Returns:
            HLAccount instance or None if data is invalid or should be skipped
        """
        # Skip items that are not published
        if data.get("status") != "PUBLISHED":
            return None
        
        try:
            aer = data.get("aer", 0) or 0
            if aer <= 0:
                return None  # Skip accounts with invalid interest rates
            
            return cls(
                name=f"{data.get('bankName', '')} {data.get('bankInstrumentName', '')}".strip(),
                interest_rate=aer / 100,
                account_type=cls._get_account_type(data),
                platform="Hargreaves Lansdown",
                min_investment=data.get("minBalance") or data.get("minInvestment") or 0,
                max_investment=data.get("maxBalance") or float('inf'),
                term=data.get("term", 0) or 0,
                url=None
            )
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error parsing HL account data: {e}")
            return None


class FlagstoneAccount(Account):
    """
    Account implementation for Flagstone platform.
    Handles parsing of Flagstone API response format.
    """
    
    @classmethod
    def _get_account_type(cls, item: dict) -> str:
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
    
    @classmethod
    def from_api_data(cls, data: dict) -> Optional[Account]:
        """
        Creates a FlagstoneAccount from Flagstone API response data.
        
        Args:
            data: Dictionary from Flagstone API 'productItems' array
            
        Returns:
            FlagstoneAccount instance or None if data is invalid or should be skipped
        """
        try:
            # Use the first product issue that is not closed to new clients
            product_issues = [pi for pi in data.get("productIssues", []) 
                             if not pi.get("isClosedToNewClients", False)]
            if not product_issues:
                return None
            
            issue = product_issues[0]
            aer = issue.get("aer", 0)
            if aer <= 0:
                return None  # Skip accounts with invalid interest rates
            
            min_investment = issue.get("depositPerClientMinimum", 0)
            max_investment = issue.get("depositPerClientMaximum", float('inf'))
            
            account_type = cls._get_account_type(data)
            term = data.get("termLength", 0)
            
            # For notice accounts, use noticeLength as term if termLength is 0
            if account_type == "notice":
                term = data.get("noticeLength", 0)
            
            # Extract URL from terms and conditions
            url = None
            if issue.get("tAndCs"):
                url = issue["tAndCs"].get("uri")
            
            return cls(
                name=f"{data.get('financialInstitution', {}).get('name', '')} {data.get('termType', '')}".strip(),
                interest_rate=aer / 100,
                account_type=account_type,
                platform="Flagstone",
                min_investment=min_investment,
                max_investment=max_investment,
                term=term,
                url=url
            )
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error parsing Flagstone account data: {e}")
            return None

