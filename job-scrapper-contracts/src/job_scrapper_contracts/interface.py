from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from .models import Job
from .scrape_filter import ScrapeJobsFilter


class ScrapperServiceInterface(ABC):
    @abstractmethod
    def scrape_jobs(
        self,
        filters: ScrapeJobsFilter,
        timeout: int,
        batch_size: int,
        on_jobs_batch: Optional[Callable[[List[Job], bool], None]],
    ) -> List[Job]:
        pass
