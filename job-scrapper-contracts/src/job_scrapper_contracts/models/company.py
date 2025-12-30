from dataclasses import dataclass
from typing import Optional, TypedDict


class CompanyDict(TypedDict):
    name: str
    website: Optional[str]


@dataclass
class Company:
    """Company or organization information"""

    name: str
    website: Optional[str] = None
