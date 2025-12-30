"""Smoke tests for the job-scrapper-contracts package."""

import pytest


@pytest.mark.smoke
def test_import_job_scrapper_contracts_module() -> None:
    """Verify job_scrapper_contracts module can be imported."""
    import job_scrapper_contracts

    assert job_scrapper_contracts is not None


@pytest.mark.smoke
def test_public_api_exports() -> None:
    """Verify all public API exports are accessible."""
    from job_scrapper_contracts import (
        Job,
        Company,
        Salary,
        Location,
        JobDict,
        CompanyDict,
        SalaryDict,
        LocationDict,
        ScrapperServiceInterface,
        ScrapeJobsFilter,
        ScrapeJobsRequest,
        ScrapeJobsResponse,
    )

    assert Job is not None
    assert Company is not None
    assert Salary is not None
    assert Location is not None
    assert JobDict is not None
    assert CompanyDict is not None
    assert SalaryDict is not None
    assert LocationDict is not None
    assert ScrapperServiceInterface is not None
    assert ScrapeJobsFilter is not None
    assert ScrapeJobsRequest is not None
    assert ScrapeJobsResponse is not None


@pytest.mark.smoke
def test_job_is_dataclass() -> None:
    """Verify Job is a dataclass with expected fields."""
    from dataclasses import fields
    from job_scrapper_contracts import Job

    field_names = {f.name for f in fields(Job)}
    assert "job_id" in field_names
    assert "title" in field_names
    assert "url" in field_names
    assert "company" in field_names


@pytest.mark.smoke
def test_scrape_jobs_filter_is_typeddict() -> None:
    """Verify ScrapeJobsFilter is a TypedDict."""
    from job_scrapper_contracts import ScrapeJobsFilter

    # TypedDicts have __annotations__
    assert hasattr(ScrapeJobsFilter, "__annotations__")
    annotations = ScrapeJobsFilter.__annotations__
    assert "min_salary" in annotations or "employment_location" in annotations


@pytest.mark.smoke
def test_scrapper_service_interface_is_abstract() -> None:
    """Verify ScrapperServiceInterface is an abstract base class."""
    from job_scrapper_contracts import ScrapperServiceInterface
    import abc

    assert issubclass(ScrapperServiceInterface, abc.ABC)
