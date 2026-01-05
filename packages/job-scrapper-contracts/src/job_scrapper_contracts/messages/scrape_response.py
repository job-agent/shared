"""Message contract for scrape jobs response."""

from typing import List, Optional, TypedDict

from job_scrapper_contracts.models.job import JobDict


class ScrapeJobsResponse(TypedDict, total=False):
    """Response message for scraping jobs.

    Attributes:
        jobs: List of scraped jobs as JobDict objects
        success: Whether the scraping operation was successful
        error: Error message if the operation failed
        jobs_count: Number of jobs scraped
        is_complete: Whether this is the final response (True) or a batch result (False)
        total_jobs: Total number of jobs scraped across all batches (only in final response)
    """

    jobs: List[JobDict]
    success: bool
    error: Optional[str]
    jobs_count: int
    is_complete: bool
    total_jobs: Optional[int]
