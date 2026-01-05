"""Smoke tests for the telemetry package."""


def test_import_telemetry_module() -> None:
    """Verify telemetry module can be imported."""
    import telemetry

    assert telemetry is not None


def test_public_api_exports() -> None:
    """Verify all public API exports are accessible."""
    from telemetry import (
        TelemetryConfig,
        TracerManager,
        MeterManager,
        TracePropagator,
        DictSetter,
        DictGetter,
        init_telemetry,
        shutdown_telemetry,
        get_tracer,
        get_meter,
        inject_trace_context,
        extract_trace_context,
        create_span_from_context,
    )

    assert TelemetryConfig is not None
    assert TracerManager is not None
    assert MeterManager is not None
    assert TracePropagator is not None
    assert DictSetter is not None
    assert DictGetter is not None
    assert callable(init_telemetry)
    assert callable(shutdown_telemetry)
    assert callable(get_tracer)
    assert callable(get_meter)
    assert callable(inject_trace_context)
    assert callable(extract_trace_context)
    assert callable(create_span_from_context)


def test_telemetry_config_from_env() -> None:
    """Verify TelemetryConfig can be created from environment."""
    from telemetry import TelemetryConfig

    config = TelemetryConfig.from_env(service_name="test-service")
    assert config.service_name == "test-service"


def test_get_tracer_returns_tracer() -> None:
    """Verify get_tracer returns a tracer object."""
    from telemetry import get_tracer

    tracer = get_tracer("test-module")
    assert tracer is not None
    assert hasattr(tracer, "start_as_current_span")


def test_get_meter_returns_meter() -> None:
    """Verify get_meter returns a meter object."""
    from telemetry import get_meter

    meter = get_meter("test-module")
    assert meter is not None
    assert hasattr(meter, "create_counter")


def test_inject_extract_trace_context() -> None:
    """Verify trace context can be injected and extracted."""
    from telemetry import inject_trace_context, extract_trace_context

    headers: dict[str, str] = {}
    result = inject_trace_context(headers)
    assert result is headers

    context = extract_trace_context(headers)
    assert context is not None


def test_extract_trace_context_handles_none() -> None:
    """Verify extract_trace_context handles None headers gracefully."""
    from telemetry import extract_trace_context

    context = extract_trace_context(None)
    assert context is not None
