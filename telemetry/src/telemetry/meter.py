"""OpenTelemetry meter configuration and initialization.

Provides centralized meter management with support for console exporters
and periodic metric reading.
"""

import logging
from typing import Optional

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

from telemetry.config import TelemetryConfig


class MeterManager:
    """Manages OpenTelemetry metrics collection.

    This class encapsulates meter provider lifecycle management, including
    initialization, shutdown, and meter retrieval.

    Example:
        config = TelemetryConfig.from_env()
        manager = MeterManager(config)
        manager.init()

        meter = manager.get_meter(__name__)
        counter = meter.create_counter("requests")
        counter.add(1)

        manager.shutdown()
    """

    def __init__(
        self,
        config: TelemetryConfig,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize the MeterManager.

        Args:
            config: Telemetry configuration.
            logger: Optional logger instance. Defaults to module logger.
        """
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._meter_provider: Optional[MeterProvider] = None
        self._initialized: bool = False

    @property
    def is_initialized(self) -> bool:
        """Check if metrics collection has been initialized."""
        return self._initialized

    def init(self) -> None:
        """Initialize OpenTelemetry metrics collection.

        Note:
            Calling this method multiple times is safe; subsequent calls are no-ops.
        """
        if self._initialized:
            self._logger.debug("Metrics already initialized, skipping")
            return

        if not self._config.enabled:
            self._logger.info("Metrics collection is disabled via configuration")
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

        readers = []

        # Add console exporter if enabled
        if self._config.console_exporter_enabled:
            console_exporter = ConsoleMetricExporter()
            reader = PeriodicExportingMetricReader(
                exporter=console_exporter,
                export_interval_millis=self._config.metrics_export_interval_ms,
            )
            readers.append(reader)
            self._logger.info(
                "Console metric exporter enabled with %dms interval",
                self._config.metrics_export_interval_ms,
            )

        # Create and configure meter provider
        self._meter_provider = MeterProvider(resource=resource, metric_readers=readers)

        # Set as global meter provider
        metrics.set_meter_provider(self._meter_provider)

        self._initialized = True
        self._logger.info("Metrics initialized for service '%s'", self._config.service_name)

    def shutdown(self) -> None:
        """Shutdown metrics, flushing any pending data.

        This should be called during application shutdown to ensure
        all metrics are exported.
        """
        if self._meter_provider is not None:
            try:
                self._meter_provider.shutdown()
                self._logger.info("Metrics shutdown complete")
            except Exception as e:
                self._logger.warning("Error during metrics shutdown: %s", e)
            finally:
                self._meter_provider = None

        self._initialized = False

    def get_meter(self, name: str) -> metrics.Meter:
        """Get a meter instance for creating metrics instruments.

        Args:
            name: Name for the meter, typically __name__ of the calling module.

        Returns:
            Meter instance. Returns a no-op meter if metrics is not initialized.
        """
        return metrics.get_meter(name)
