"""OpenTelemetry setup for traces, metrics, and logs.

By default the signals are exported to the console (stdout), so they show up in
`docker compose logs app`. Set OTEL_EXPORTER_OTLP_ENDPOINT to export over
OTLP/HTTP to a collector instead. Tests install in-memory components first.
"""

import logging
import os

from opentelemetry import _logs, metrics, trace
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    ConsoleLogRecordExporter,
    SimpleLogRecordProcessor,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor


LOGGER_NAME = "order_tracker"


def default_components():
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        return (
            BatchSpanProcessor(OTLPSpanExporter()),
            PeriodicExportingMetricReader(OTLPMetricExporter()),
            BatchLogRecordProcessor(OTLPLogExporter()),
        )
    return (
        SimpleSpanProcessor(ConsoleSpanExporter()),
        PeriodicExportingMetricReader(ConsoleMetricExporter()),
        SimpleLogRecordProcessor(ConsoleLogRecordExporter()),
    )


def setup_telemetry(span_processor=None, metric_reader=None, log_processor=None):
    # Global providers can only be set once; keep whatever was installed first.
    if isinstance(trace.get_tracer_provider(), TracerProvider):
        return
    if span_processor is None:
        span_processor, metric_reader, log_processor = default_components()

    resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "order-tracker")})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)

    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(log_processor)
    _logs.set_logger_provider(logger_provider)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.addHandler(LoggingHandler(logger_provider=logger_provider))
