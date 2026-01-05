# Telemetry Package

OpenTelemetry telemetry module for distributed tracing and metrics in the job-agent platform.

## Installation

```bash
pip install -e shared/telemetry
```

## Usage

### Module-level Functions (Backward Compatible)

```python
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
```

### Class-based API (For DI and Testability)

```python
from telemetry import TelemetryConfig, TracerManager, MeterManager, TracePropagator

config = TelemetryConfig.from_env(service_name="my-service")
tracer_manager = TracerManager(config)
meter_manager = MeterManager(config)
propagator = TracePropagator()

tracer_manager.init()
meter_manager.init()

# Use tracer
tracer = tracer_manager.get_tracer(__name__)
with tracer.start_as_current_span("operation"):
    pass

# Propagate trace context across services
headers = {}
propagator.inject(headers)
# ... send headers with message ...

# On receiving side
context = propagator.extract(received_headers)
with propagator.create_span_from_context("process_message", context):
    pass

tracer_manager.shutdown()
meter_manager.shutdown()
```
