from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Account:
    """
    Base class for all savings accounts from different providers.
    This class defines the common structure that all account types share.
    Subclasses should implement the from_api_data() class method to parse
    provider-specific data formats.
    """
    name: str
    interest_rate: float
    account_type: str  # e.g., 'fixed_term', 'easy_access', 'notice', 'fixed_term_isa', 'easy_access_isa'
    platform: str
    min_investment: float = 0
    max_investment: float = float('inf')
    term: int = 0  # Term in months for fixed_term accounts, notice period in months for notice accounts, 0 for easy access
    url: Optional[str] = None

    @classmethod
    def from_api_data(cls, data: dict) -> Optional['Account']:
        """
        Factory method to create an Account instance from provider-specific API data.
        Subclasses must override this method to parse their specific data format.
        
        Args:
            data: Raw API response data in provider-specific format
            
        Returns:
            Account instance if data is valid, None if account should be skipped
            
        Raises:
            NotImplementedError: If called on base Account class
        """
        raise NotImplementedError("Subclasses must implement from_api_data()")

@dataclass
class SavingsGoal:
    amount: float
    horizon: int # Horizon in months

@dataclass
class OptimizationInput:
    total_investment: float
    savings_goals: List[SavingsGoal]
    earnings: Optional[float] = None
    isa_allowance_used: Optional[float] = 0.0
    other_savings_income: Optional[float] = 0.0
    # Other constraints can be added here
    # e.g., max_isa_investment: float = 20000

@dataclass
class Investment:
    account_name: str
    amount: float
    aer: float
    term: str
    is_isa: bool
    url: str
    platform: str

@dataclass
class Summary:
    total_investment: float
    gross_annual_interest: float
    net_annual_interest: float
    net_effective_aer: float
    tax_due: float
    tax_band: str
    personal_savings_allowance: float
    tax_rate: float
    tax_free_allowance_remaining: float
    equivalent_pre_tax_rate: float

@dataclass
class OptimizationResult:
    investments: List[Investment]
    summary: Summary
    status: str 
    optimization_record_id: Optional[int] = None
