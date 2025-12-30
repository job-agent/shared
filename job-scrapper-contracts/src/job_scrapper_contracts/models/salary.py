from dataclasses import dataclass
from typing import Optional, TypedDict


class SalaryDict(TypedDict):
    currency: str
    min_value: Optional[float]
    max_value: Optional[float]


@dataclass
class Salary:
    """Salary information for a job"""

    currency: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
