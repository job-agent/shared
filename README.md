# Shared Packages

Shared packages for job-agent platform microservices. These packages are used by
`scrappers`, `scrappers-mock`, and other services.

## Packages

| Package | Description |
|---------|-------------|
| `job-scrapper-contracts` | Data models and interfaces for job scraping |
| `scrapper-messaging` | RabbitMQ messaging components |
| `telemetry` | OpenTelemetry distributed tracing |

## Installation

Install all shared packages in development mode:

```bash
pip install -e packages/job-scrapper-contracts[dev]
pip install -e packages/scrapper-messaging[dev]
pip install -e packages/telemetry[dev]
```

## Running Tests

### Unit Tests

Run all unit tests from the shared root:

```bash
pytest
```

Run tests for a specific package:

```bash
pytest packages/job-scrapper-contracts
pytest packages/scrapper-messaging
pytest packages/telemetry
```

### Smoke Tests

Smoke tests verify type checking and basic package health. They are centralized in
`smoke_tests/` and cover all shared packages using parametrized tests.

```bash
python -m pytest smoke_tests -m smoke -v
```

The `smoke` marker is defined in `pyproject.toml`.

## Test Structure

```
shared/
├── packages/
│   ├── job-scrapper-contracts/    # Package with unit tests
│   ├── scrapper-messaging/        # Package with unit tests
│   └── telemetry/                 # Package with unit tests
└── smoke_tests/                   # Centralized smoke tests
    ├── conftest.py                # Shared fixtures
    └── test_type_checking.py      # Type checking tests (parametrized)
```

## Code Quality

Run linting and formatting:

```bash
./scripts/lint_and_format.sh
```
