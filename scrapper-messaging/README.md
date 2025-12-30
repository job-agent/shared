# scrapper-messaging

RabbitMQ messaging components for job scrapper services. This package provides a reusable
RabbitMQ consumer that bridges incoming scrape requests to a scrapper service implementation.

## Overview

This package is used by both `scrappers` and `scrappers-mock` to:

- Listen for job scrape requests on RabbitMQ queues
- Decode incoming JSON request payloads
- Invoke the scrapper service with batched job streaming
- Publish responses back to the caller via RPC pattern

## Installation

```bash
pip install -e .[dev]
```

Or use the reinstall script:

```bash
./scripts/reinstall_packages.sh
```

## Dependencies

- `pika>=1.3.2` - RabbitMQ client
- `job-scrapper-contracts` - Shared data models (`Job`, `ScrapeJobsRequest`, `ScrapeJobsResponse`)

## Usage

### Basic Consumer Setup

```python
from scrapper_messaging import ScrapperConsumer
from your_scrapper import YourScrapperService

# Create your service implementing ScrapperServiceInterface
service = YourScrapperService()

# Create and start the consumer
consumer = ScrapperConsumer.from_url(service)
consumer.start()
```

The consumer reads the RabbitMQ URL from the `RABBITMQ_URL` environment variable by default,
or you can pass it explicitly:

```python
consumer = ScrapperConsumer.from_url(service, "amqp://user:pass@localhost:5672/vhost")
```

### Queue Configuration

The default queue name is `job.scrape.request`. You can customize queue settings:

```python
from scrapper_messaging import ScrapperConsumer, QueueConfig, ScrapperConsumerDependencies

deps = ScrapperConsumerDependencies(
    queue_config=QueueConfig(
        queue_name="custom.queue.name",
        durable=True,
        prefetch_count=1,
        exchange="my-exchange",
        routing_key="my-routing-key",
    )
)

consumer = ScrapperConsumer.from_url(service, dependencies=deps)
```

### Using the Connection Directly

```python
from scrapper_messaging import RabbitMQConnection

# As a context manager
with RabbitMQConnection("amqp://localhost") as conn:
    channel = conn.connect()
    # Use channel for custom operations

# Or manually
conn = RabbitMQConnection()
channel = conn.connect()
# ...
conn.close()
```

## Package Structure

```
src/scrapper_messaging/
├── __init__.py                 # Public exports
├── connection/                 # RabbitMQ connection management
│   └── rabbitmq_connection.py  # RabbitMQConnection class
├── consumer/                   # Message consumer
│   ├── scrapper_consumer.py    # ScrapperConsumer class
│   ├── scrapper_consumer_config.py  # ScrapperConsumerDependencies
│   └── queue_config.py         # QueueConfig dataclass
├── contracts/                  # Interface definitions
│   ├── rabbitmq_connection_interface.py   # IRabbitMQConnection
│   ├── jobs_service_invoker_interface.py  # IJobsServiceInvoker
│   ├── response_publisher_interface.py    # IResponsePublisher
│   └── scrape_request_decoder_interface.py # IScrapeRequestDecoder
├── request_decoder/            # JSON payload decoding
│   └── json_scrape_request_decoder.py
├── response_publisher/         # RabbitMQ response publishing
│   └── rabbitmq_response_publisher.py
└── service_invoker/            # Scrapper service invocation
    └── scrapper_service_invoker.py
```

## Public API

### Classes

| Class | Description |
|-------|-------------|
| `ScrapperConsumer` | Main consumer that listens for scrape requests and delegates to a service |
| `RabbitMQConnection` | Manages RabbitMQ connection lifecycle with context manager support |
| `QueueConfig` | Queue declaration options (name, durability, prefetch, exchange, routing key) |
| `ScrapperConsumerDependencies` | Bundles factory functions for consumer wiring |

### Interfaces

| Interface | Description |
|-----------|-------------|
| `IRabbitMQConnection` | Contract for RabbitMQ connections |
| `IJobsServiceInvoker` | Contract for invoking the scrapper service |
| `IResponsePublisher` | Contract for publishing responses |
| `IScrapeRequestDecoder` | Contract for decoding request payloads |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RABBITMQ_URL` | RabbitMQ connection URL (e.g., `amqp://user:pass@host:5672/vhost`) |

## Development

### Running Tests

Run unit tests from the package directory:

```bash
cd scrapper-messaging
pytest
```

Run smoke tests (type checking) from the shared root:

```bash
cd shared
python -m pytest smoke_tests -m smoke -v
```

Smoke tests are located in `shared/smoke_tests/` and cover all shared packages
(`job-scrapper-contracts`, `scrapper-messaging`) using parametrized tests.

### Linting and Formatting

```bash
./scripts/lint_and_format.sh
```

This runs `ruff check --fix` and `ruff format`.

## Message Flow

1. Platform sends a `ScrapeJobsRequest` to the `job.scrape.request` queue
2. `ScrapperConsumer` receives the message with `correlation_id` and `reply_to` properties
3. `JSONScrapeRequestDecoder` parses the JSON payload
4. `ScrapperServiceInvoker` calls the service's `scrape_jobs()` method with batch streaming
5. Jobs are emitted in batches via `RabbitMQResponsePublisher` to the `reply_to` queue
6. Final response includes `is_complete=True` and `total_jobs` count
