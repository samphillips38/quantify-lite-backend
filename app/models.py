from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Account:
    name: str
    interest_rate: float
    account_type: str # e.g., 'fixed_term', 'easy_access', 'fixed_term_isa', 'easy_access_isa'
    platform: str
    min_investment: float = 0
    max_investment: float = float('inf')
    term: int = 0 # Term in months, 0 for easy access
    url: Optional[str] = None

@dataclass
class SavingsGoal:
    amount: float
    horizon: int # Horizon in months

@dataclass
class OptimizationInput:
    total_investment: float
    savings_goals: List[SavingsGoal]
    earnings: Optional[float] = None
    isa_allowance_remaining: Optional[float] = 20000.0
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
class OptimizationResult:
    investments: List[Investment]
    total_return: float
    status: str 