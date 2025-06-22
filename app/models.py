from dataclasses import dataclass
from typing import List

@dataclass
class Account:
    name: str
    interest_rate: float
    account_type: str # e.g., 'fixed_term', 'variable_access', 'fixed_term_isa', 'variable_access_isa'
    min_investment: float = 0
    max_investment: float = float('inf')

@dataclass
class OptimizationInput:
    total_investment: float
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

@dataclass
class OptimizationResult:
    investments: List[Investment]
    total_return: float
    status: str 