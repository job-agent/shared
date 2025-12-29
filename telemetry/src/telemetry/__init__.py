"""OpenTelemetry telemetry module for distributed tracing and metrics.

This module provides centralized telemetry configuration for the job-agent platform.
It supports console output by default and can be extended to support OTLP exporters.

Usage (module-level functions for backward compatibility):
    from telemetry import init_telemetry, get_tracer, get_meter, shutdown_telemetry

    # Initialize at application startup
    init_telemetry(service_name="telegram-bot")

    # Get a tracer for creating spans
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("my_operation"):
        # ... do work

    # Get a meter for creating metrics
    meter = get_meter(__name__)
    counter = meter.create_counter("requests")
    counter.add(1)

    # Shutdown on application exit
    shutdown_telemetry()

Usage (class-based for DI and testability):
    from telemetry import TelemetryConfig, TracerManager, MeterManager, TracePropagator

    config = TelemetryConfig.from_env(service_name="my-service")
    tracer_manager = TracerManager(config)
    meter_manager = MeterManager(config)
    propagator = TracePropagator()

    tracer_manager.init()
    meter_manager.init()
    # ... use managers ...
    tracer_manager.shutdown()
    meter_manager.shutdown()
"""

from typing import Any, Dict, Mapping, Optional

from opentelemetry import metrics, trace
from opentelemetry.context import Context
from opentelemetry.trace import SpanKind

from telemetry.config import TelemetryConfig
from telemetry.tracer import TracerManager
from telemetry.meter import MeterManager
from telemetry.propagation import TracePropagator, DictSetter, DictGetter


# Module-level managers for backward-compatible function API
_tracer_manager: Optional[TracerManager] = None
_meter_manager: Optional[MeterManager] = None
_propagator: Optional[TracePropagator] = None


def _get_propagator() -> TracePropagator:
    """Get or create the module-level propagator instance."""
    global _propagator
    if _propagator is None:
        _propagator = TracePropagator()
    return _propagator


def init_telemetry(
    service_name: Optional[str] = None,
    config: Optional[TelemetryConfig] = None,
) -> None:
    """Initialize OpenTelemetry tracing and metrics.

    This function should be called once at application startup, before any
    tracing or metrics operations.

    Args:
        service_name: Override service name for this initialization.
        config: Optional pre-built configuration (defaults to reading from env).

    Note:
        Calling this function multiple times is safe; subsequent calls are no-ops.
    """
    global _tracer_manager, _meter_manager

    if config is None:
        config = TelemetryConfig.from_env(service_name)

    if _tracer_manager is None:
        _tracer_manager = TracerManager(config)
    _tracer_manager.init()

    if _meter_manager is None:
        _meter_manager = MeterManager(config)
    _meter_manager.init()


def shutdown_telemetry() -> None:
    """Shutdown telemetry, flushing any pending data.

    This should be called during application shutdown to ensure
    all traces and metrics are exported.
    """
    global _tracer_manager, _meter_manager

    if _tracer_manager is not None:
        _tracer_manager.shutdown()
        _tracer_manager = None

    if _meter_manager is not None:
        _meter_manager.shutdown()
        _meter_manager = None


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance for creating spans.

    Args:
        name: Name for the tracer, typically __name__ of the calling module.

    Returns:
        Tracer instance. Returns a no-op tracer if telemetry is not initialized.
    """
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Get a meter instance for creating metrics instruments.

    Args:
        name: Name for the meter, typically __name__ of the calling module.

    Returns:
        Meter instance. Returns a no-op meter if metrics is not initialized.
    """
    return metrics.get_meter(name)


def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """Inject current trace context into message headers.

    This should be called before publishing a message to propagate
    the current trace context to the message consumer.

    Args:
        headers: Dictionary to inject trace context into. Modified in place.

    Returns:
        The headers dictionary with trace context added.

    Example:
        headers = {"custom": "header"}
        inject_trace_context(headers)
        # headers now contains traceparent, tracestate, etc.
    """
    return _get_propagator().inject(headers)


def extract_trace_context(headers: Optional[Mapping[str, Any]]) -> Context:
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
        context = extract_trace_context(properties.headers)
        with tracer.start_as_current_span("process", context=context):
            # Processing continues the trace
    """
    return _get_propagator().extract(headers)


def create_span_from_context(
    name: str,
    context: Optional[Context] = None,
    kind: SpanKind = SpanKind.CONSUMER,
    attributes: Optional[Dict[str, Any]] = None,
):
    """Create a span that continues from an extracted trace context.

    This is a convenience function for creating a span that continues
    a distributed trace from a message consumer.

    Args:
        name: Name of the span.
        context: Trace context extracted from message headers.
        kind: Kind of span (default CONSUMER for message processing).
        attributes: Optional attributes to add to the span.

    Returns:
        Context manager that yields the created span.

    Example:
        context = extract_trace_context(properties.headers)
        with create_span_from_context("process_scrape_request", context) as span:
            span.set_attribute("queue", "job.scrape.request")
            # Process the message
    """
    return _get_propagator().create_span_from_context(name, context, kind, attributes)


__all__ = [
    # Classes for DI/testability
    "TelemetryConfig",
    "TracerManager",
    "MeterManager",
    "TracePropagator",
    "DictSetter",
    "DictGetter",
    # Module-level functions for backward compatibility
    "init_telemetry",
    "shutdown_telemetry",
    "get_tracer",
    "get_meter",
    "inject_trace_context",
    "extract_trace_context",
    "create_span_from_context",
]
