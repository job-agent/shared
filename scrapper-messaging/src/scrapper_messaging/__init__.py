"""Messaging package providing RabbitMQ connectivity and consumers."""

from .connection import RabbitMQConnection
from .consumer import (
    DEFAULT_QUEUE_NAME,
    QueueConfig,
    ScrapperConsumer,
    ScrapperConsumerDependencies,
)
from .contracts import IRabbitMQConnection
from telemetry import (
    inject_trace_context,
    extract_trace_context,
    create_span_from_context,
)

__all__ = [
    "RabbitMQConnection",
    "ScrapperConsumer",
    "IRabbitMQConnection",
    "QueueConfig",
    "ScrapperConsumerDependencies",
    "DEFAULT_QUEUE_NAME",
    # Telemetry utilities for distributed tracing
    "inject_trace_context",
    "extract_trace_context",
    "create_span_from_context",
]
