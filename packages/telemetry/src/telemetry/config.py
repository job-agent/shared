"""OpenTelemetry configuration settings.

Reads configuration from environment variables following OpenTelemetry conventions.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TelemetryConfig:
    """Configuration for OpenTelemetry telemetry.

    Attributes:
        service_name: Name of the service for resource identification.
        service_version: Version of the service.
        deployment_environment: Deployment environment (dev, staging, prod).
        enabled: Whether telemetry is enabled.
        console_exporter_enabled: Whether to export traces/metrics to console.
        otlp_exporter_enabled: Whether to export traces via OTLP to a collector.
        otlp_endpoint: OTLP collector endpoint (gRPC).
        traces_sampler: Sampling strategy (always_on, always_off, traceidratio, parentbased_*).
        traces_sampler_arg: Argument for sampler (e.g., 0.5 for 50% sampling ratio).
        metrics_export_interval_ms: Interval for periodic metric export in milliseconds.
    """

    service_name: str = "job-agent-platform"
    service_version: str = "0.1.0"
    deployment_environment: str = "development"
    enabled: bool = True
    console_exporter_enabled: bool = True
    otlp_exporter_enabled: bool = False
    otlp_endpoint: str = "http://otel-collector:4317"
    traces_sampler: str = "parentbased_always_on"
    traces_sampler_arg: Optional[float] = None
    metrics_export_interval_ms: int = 60000

    @classmethod
    def from_env(cls, service_name: Optional[str] = None) -> "TelemetryConfig":
        """Create configuration from environment variables.

        Environment variables (following OTEL conventions):
            OTEL_SERVICE_NAME: Service name (overridden by service_name param)
            OTEL_SERVICE_VERSION: Service version
            OTEL_DEPLOYMENT_ENVIRONMENT: Deployment environment
            OTEL_ENABLED: Enable/disable telemetry (true/false)
            OTEL_EXPORTER_CONSOLE_ENABLED: Enable console exporter (true/false)
            OTEL_TRACES_SAMPLER: Sampling strategy
            OTEL_TRACES_SAMPLER_ARG: Sampler argument (e.g., ratio for traceidratio)
            OTEL_METRICS_EXPORT_INTERVAL: Metrics export interval in milliseconds

        Args:
            service_name: Override service name from environment.

        Returns:
            TelemetryConfig instance with values from environment.
        """

        def parse_bool(value: str, default: bool) -> bool:
            if not value:
                return default
            return value.lower() in ("true", "1", "yes", "on")

        def parse_float(value: str) -> Optional[float]:
            if not value:
                return None
            try:
                return float(value)
            except ValueError:
                return None

        def parse_int(value: str, default: int) -> int:
            if not value:
                return default
            try:
                return int(value)
            except ValueError:
                return default

        resolved_service_name = service_name or os.getenv("OTEL_SERVICE_NAME") or cls.service_name

        return cls(
            service_name=resolved_service_name,
            service_version=os.getenv("OTEL_SERVICE_VERSION", cls.service_version),
            deployment_environment=os.getenv(
                "OTEL_DEPLOYMENT_ENVIRONMENT", cls.deployment_environment
            ),
            enabled=parse_bool(os.getenv("OTEL_ENABLED", ""), True),
            console_exporter_enabled=parse_bool(
                os.getenv("OTEL_EXPORTER_CONSOLE_ENABLED", ""), True
            ),
            otlp_exporter_enabled=parse_bool(os.getenv("OTEL_EXPORTER_OTLP_ENABLED", ""), False),
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", cls.otlp_endpoint),
            traces_sampler=os.getenv("OTEL_TRACES_SAMPLER", cls.traces_sampler),
            traces_sampler_arg=parse_float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "")),
            metrics_export_interval_ms=parse_int(
                os.getenv("OTEL_METRICS_EXPORT_INTERVAL", ""), cls.metrics_export_interval_ms
            ),
        )
