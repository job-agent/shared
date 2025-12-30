"""Smoke tests for the scrapper-messaging package."""

import pytest


@pytest.mark.smoke
def test_import_scrapper_messaging_module() -> None:
    """Verify scrapper_messaging module can be imported."""
    import scrapper_messaging

    assert scrapper_messaging is not None


@pytest.mark.smoke
def test_public_api_exports() -> None:
    """Verify all public API exports are accessible."""
    from scrapper_messaging import (
        RabbitMQConnection,
        ScrapperConsumer,
        IRabbitMQConnection,
        QueueConfig,
        ScrapperConsumerDependencies,
        DEFAULT_QUEUE_NAME,
        inject_trace_context,
        extract_trace_context,
        create_span_from_context,
    )

    assert RabbitMQConnection is not None
    assert ScrapperConsumer is not None
    assert IRabbitMQConnection is not None
    assert QueueConfig is not None
    assert ScrapperConsumerDependencies is not None
    assert DEFAULT_QUEUE_NAME is not None
    assert callable(inject_trace_context)
    assert callable(extract_trace_context)
    assert callable(create_span_from_context)


@pytest.mark.smoke
def test_queue_config_creation() -> None:
    """Verify QueueConfig can be instantiated."""
    from scrapper_messaging import QueueConfig

    config = QueueConfig(queue_name="test-queue")
    assert config.queue_name == "test-queue"


@pytest.mark.smoke
def test_default_queue_name_value() -> None:
    """Verify DEFAULT_QUEUE_NAME has expected value."""
    from scrapper_messaging import DEFAULT_QUEUE_NAME

    assert isinstance(DEFAULT_QUEUE_NAME, str)
    assert len(DEFAULT_QUEUE_NAME) > 0


@pytest.mark.smoke
def test_irabbitqm_connection_is_protocol() -> None:
    """Verify IRabbitMQConnection is defined as expected."""
    from scrapper_messaging import IRabbitMQConnection

    assert hasattr(IRabbitMQConnection, "__abstractmethods__") or hasattr(
        IRabbitMQConnection, "__protocol_attrs__"
    )
