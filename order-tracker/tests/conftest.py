from types import SimpleNamespace

import pytest
from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter, SimpleLogRecordProcessor
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.telemetry import setup_telemetry

# Global providers can only be set once per process, so install in-memory ones
# before the app is imported and share them across tests.
span_exporter = InMemorySpanExporter()
metric_reader = InMemoryMetricReader()
log_exporter = InMemoryLogRecordExporter()
setup_telemetry(
    span_processor=SimpleSpanProcessor(span_exporter),
    metric_reader=metric_reader,
    log_processor=SimpleLogRecordProcessor(log_exporter),
)


@pytest.fixture
def telemetry():
    span_exporter.clear()
    log_exporter.clear()
    return SimpleNamespace(spans=span_exporter, metrics=metric_reader, logs=log_exporter)
