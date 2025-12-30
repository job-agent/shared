"""OpenTelemetry tracer configuration and initialization.

Provides centralized tracer management with support for console exporters
and configurable sampling strategies.
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    ParentBasedTraceIdRatio,
    ParentBased,
    TraceIdRatioBased,
    Sampler,
)

from telemetry.config import TelemetryConfig


class TracerManager:
    """Manages OpenTelemetry tracing and auto-instrumentation.

    This class encapsulates tracer provider lifecycle management, including
    initialization, shutdown, auto-instrumentation setup, and tracer retrieval.

    Example:
        config = TelemetryConfig.from_env()
        manager = TracerManager(config)
        manager.init()

        tracer = manager.get_tracer(__name__)
        with tracer.start_as_current_span("my_operation"):
            # ... do work

        manager.shutdown()
    """

    def __init__(
        self,
        config: TelemetryConfig,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize the TracerManager.

        Args:
            config: Telemetry configuration.
            logger: Optional logger instance. Defaults to module logger.
        """
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._tracer_provider: Optional[TracerProvider] = None
        self._initialized: bool = False

    @property
    def is_initialized(self) -> bool:
        """Check if tracing has been initialized."""
        return self._initialized

    def init(self) -> None:
        """Initialize OpenTelemetry tracing and auto-instrumentation.

        This method should be called once at application startup, before any
        tracing operations.

        Note:
            Calling this method multiple times is safe; subsequent calls are no-ops.
        """
        if self._initialized:
            self._logger.debug("Telemetry already initialized, skipping")
            return

        if not self._config.enabled:
            self._logger.info("Telemetry is disabled via configuration")
            self._initialized = True
            return

        # Create resource with service attributes
        resource = Resource.create(
            {
                SERVICE_NAME: self._config.service_name,
                SERVICE_VERSION: self._config.service_version,
                "deployment.environment": self._config.deployment_environment,
            }
        )

        # Create sampler
        sampler = self._create_sampler()

        # Create and configure tracer provider
        self._tracer_provider = TracerProvider(resource=resource, sampler=sampler)

        # Add console exporter if enabled
        if self._config.console_exporter_enabled:
            console_exporter = ConsoleSpanExporter()
            self._tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
            self._logger.info("Console span exporter enabled")

        # Set as global tracer provider
        trace.set_tracer_provider(self._tracer_provider)

        # Initialize auto-instrumentation
        self._init_auto_instrumentation()

        self._initialized = True
        self._logger.info(
            "Telemetry initialized for service '%s' with sampler '%s'",
            self._config.service_name,
            self._config.traces_sampler,
        )

    def _create_sampler(self) -> Sampler:
        """Create a sampler based on configuration.

        Returns:
            Configured sampler instance.
        """
        sampler_name = self._config.traces_sampler.lower()
        ratio = (
            self._config.traces_sampler_arg if self._config.traces_sampler_arg is not None else 1.0
        )

        # Clamp ratio to valid range
        ratio = max(0.0, min(1.0, ratio))

        if sampler_name == "always_on":
            return ALWAYS_ON
        elif sampler_name == "always_off":
            return ALWAYS_OFF
        elif sampler_name == "traceidratio":
            return TraceIdRatioBased(ratio)
        elif sampler_name == "parentbased_always_on":
            return ParentBased(root=ALWAYS_ON)
        elif sampler_name == "parentbased_always_off":
            return ParentBased(root=ALWAYS_OFF)
        elif sampler_name == "parentbased_traceidratio":
            return ParentBasedTraceIdRatio(ratio)
        else:
            self._logger.warning(
                "Unknown sampler '%s', defaulting to parentbased_always_on",
                sampler_name,
            )
            return ParentBased(root=ALWAYS_ON)

    def _init_auto_instrumentation(self) -> None:
        """Initialize automatic instrumentation for supported libraries.

        This enables tracing for:
        - SQLAlchemy database operations
        - Pika RabbitMQ operations
        - HTTP requests via the requests library
        """
        # SQLAlchemy instrumentation
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

            SQLAlchemyInstrumentor().instrument()
            self._logger.debug("SQLAlchemy instrumentation enabled")
        except ImportError:
            self._logger.debug("SQLAlchemy instrumentation not available")
        except Exception as e:
            self._logger.warning("Failed to initialize SQLAlchemy instrumentation: %s", e)

        # Pika (RabbitMQ) instrumentation
        try:
            from opentelemetry.instrumentation.pika import PikaInstrumentor

            PikaInstrumentor().instrument()
            self._logger.debug("Pika instrumentation enabled")
        except ImportError:
            self._logger.debug("Pika instrumentation not available")
        except Exception as e:
            self._logger.warning("Failed to initialize Pika instrumentation: %s", e)

        # Requests HTTP client instrumentation
        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor

            RequestsInstrumentor().instrument()
            self._logger.debug("Requests instrumentation enabled")
        except ImportError:
            self._logger.debug("Requests instrumentation not available")
        except Exception as e:
            self._logger.warning("Failed to initialize Requests instrumentation: %s", e)

    def shutdown(self) -> None:
        """Shutdown telemetry, flushing any pending data.

        This should be called during application shutdown to ensure
        all traces are exported.
        """
        if self._tracer_provider is not None:
            try:
                self._tracer_provider.shutdown()
                self._logger.info("Telemetry shutdown complete")
            except Exception as e:
                self._logger.warning("Error during telemetry shutdown: %s", e)
            finally:
                self._tracer_provider = None

        self._initialized = False

    def get_tracer(self, name: str) -> trace.Tracer:
        """Get a tracer instance for creating spans.

        Args:
            name: Name for the tracer, typically __name__ of the calling module.

        Returns:
            Tracer instance. Returns a no-op tracer if telemetry is not initialized.
        """
        return trace.get_tracer(name)
