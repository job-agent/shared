from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TypedDict

from .company import Company, CompanyDict
from .location import Location, LocationDict
from .salary import Salary, SalaryDict


class JobDictRequired(TypedDict):
    """Required fields for job listing dictionary"""

    job_id: int
    title: str
    url: str
    description: str
    company: CompanyDict
    date_posted: str
    valid_through: str
    employment_type: str
    source: str


class JobDict(JobDictRequired, total=False):
    """Job listing dictionary structure with optional fields"""

    category: str
    salary: SalaryDict
    experience_months: float
    location: LocationDict
    industry: str


@dataclass
class Job:
    """Job listing data model"""

    job_id: int
    title: str
    url: str
    description: str
    company: Company
    date_posted: datetime
    valid_through: datetime
    employment_type: str
    source: str
    category: Optional[str] = None
    salary: Optional[Salary] = None
    experience_months: Optional[float] = None
    location: Optional[Location] = None
    industry: Optional[str] = None

    def __str__(self) -> str:
        return f"Job(id={self.job_id}, title='{self.title}', company='{self.company.name}')"

    def to_dict(self) -> JobDict:
        """Convert job to dictionary"""

        result: JobDict = {
            "job_id": self.job_id,
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "company": {"name": self.company.name, "website": self.company.website},
            "date_posted": self.date_posted.isoformat(),
            "valid_through": self.valid_through.isoformat(),
            "employment_type": self.employment_type,
            "source": self.source,
        }

        if self.salary:
            salary_dict: SalaryDict = {
                "currency": self.salary.currency,
                "min_value": self.salary.min_value,
                "max_value": self.salary.max_value,
            }
            result["salary"] = salary_dict

        if self.location:
            location_dict: LocationDict = {
                "region": self.location.region,
                "is_remote": self.location.is_remote,
                "can_apply": self.location.can_apply,
            }
            result["location"] = location_dict

        if self.experience_months is not None:
            result["experience_months"] = self.experience_months

        if self.industry:
            result["industry"] = self.industry

        if self.category:
            result["category"] = self.category

        return result
