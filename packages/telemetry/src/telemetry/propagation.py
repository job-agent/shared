"""Trace context propagation utilities for distributed tracing.

Provides classes to inject and extract trace context from message headers,
enabling distributed tracing across RabbitMQ message boundaries.

Usage:
    # Create a propagator (can reuse the same instance)
    propagator = TracePropagator()

    # When publishing a message
    headers = {}
    propagator.inject(headers)
    channel.basic_publish(..., properties=pika.BasicProperties(headers=headers))

    # When consuming a message
    context = propagator.extract(properties.headers)
    with propagator.create_span_from_context("process_message", context):
        # Processing continues the trace
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Generator, Mapping, Optional

from opentelemetry import propagate, trace
from opentelemetry.context import Context
from opentelemetry.propagators.textmap import Setter, Getter
from opentelemetry.trace import Span, SpanKind


class DictSetter(Setter[Dict[str, str]]):
    """Setter for injecting trace context into a dictionary."""

    def set(self, carrier: Dict[str, str], key: str, value: str) -> None:
        """Set a key-value pair in the carrier dictionary."""
        carrier[key] = value


class DictGetter(Getter[Mapping[str, Any]]):
    """Getter for extracting trace context from a dictionary."""

    def get(self, carrier: Mapping[str, Any], key: str) -> Optional[list[str]]:
        """Get a value from the carrier dictionary."""
        value = carrier.get(key)
        if value is None:
            return None
        if isinstance(value, list):
            return [str(v) for v in value]
        return [str(value)]

    def keys(self, carrier: Mapping[str, Any]) -> list[str]:
        """Get all keys from the carrier dictionary."""
        return list(carrier.keys())


class TracePropagator:
    """Handles trace context propagation for distributed tracing.

    This class provides methods to inject and extract trace context from
    message headers, enabling distributed tracing across service boundaries.

    Example:
        propagator = TracePropagator()

        # Producer side
        headers = {"custom": "header"}
        propagator.inject(headers)
        # headers now contains traceparent, tracestate, etc.

        # Consumer side
        context = propagator.extract(properties.headers)
        with propagator.create_span_from_context("process_message", context) as span:
            span.set_attribute("queue", "job.scrape.request")
            # Process the message
    """

    def __init__(
        self,
        setter: Optional[Setter[Dict[str, str]]] = None,
        getter: Optional[Getter[Mapping[str, Any]]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize the TracePropagator.

        Args:
            setter: Custom setter for injecting context. Defaults to DictSetter.
            getter: Custom getter for extracting context. Defaults to DictGetter.
            logger: Optional logger instance. Defaults to module logger.
        """
        self._setter = setter or DictSetter()
        self._getter = getter or DictGetter()
        self._logger = logger or logging.getLogger(__name__)

    def inject(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject current trace context into message headers.

        This should be called before publishing a message to propagate
        the current trace context to the message consumer.

        Args:
            headers: Dictionary to inject trace context into. Modified in place.

        Returns:
            The headers dictionary with trace context added.

        Example:
            headers = {"custom": "header"}
            propagator.inject(headers)
            # headers now contains traceparent, tracestate, etc.
        """
        propagate.inject(headers, setter=self._setter)
        self._logger.debug("Injected trace context: %s", headers)
        return headers

    def extract(self, headers: Optional[Mapping[str, Any]]) -> Context:
        """Extract trace context from message headers.

        This should be called when consuming a message to continue
        the trace from the message producer.

        Args:
            headers: Message headers containing trace context.
                     Can be None if no headers are present.

        Returns:
            Context object containing the extracted trace context.
            Returns an empty context if headers is None or contains no trace data.

        Example:
            context = propagator.extract(properties.headers)
            with tracer.start_as_current_span("process", context=context):
                # Processing continues the trace
        """
        if headers is None:
            self._logger.debug("No headers provided for trace context extraction")
            return Context()

        context = propagate.extract(headers, getter=self._getter)
        self._logger.debug("Extracted trace context from headers: %s", headers)
        return context

    @contextmanager
    def create_span_from_context(
        self,
        name: str,
        context: Optional[Context] = None,
        kind: SpanKind = SpanKind.CONSUMER,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Generator[Span, None, None]:
        """Create a span that continues from an extracted trace context.

        This is a convenience method for creating a span that continues
        a distributed trace from a message consumer.

        Args:
            name: Name of the span.
            context: Trace context extracted from message headers.
            kind: Kind of span (default CONSUMER for message processing).
            attributes: Optional attributes to add to the span.

        Yields:
            The created span.

        Example:
            context = propagator.extract(properties.headers)
            with propagator.create_span_from_context("process_scrape_request", context) as span:
                span.set_attribute("queue", "job.scrape.request")
                # Process the message
        """
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span(
            name,
            context=context,
            kind=kind,
            attributes=attributes,
        ) as span:
            yield span
