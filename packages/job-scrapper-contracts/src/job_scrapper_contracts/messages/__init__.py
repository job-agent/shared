"""Message contracts for RabbitMQ communication between job-agent-backend and scrapper-service."""

from job_scrapper_contracts.messages.scrape_request import ScrapeJobsRequest
from job_scrapper_contracts.messages.scrape_response import ScrapeJobsResponse

__all__ = ["ScrapeJobsRequest", "ScrapeJobsResponse"]
