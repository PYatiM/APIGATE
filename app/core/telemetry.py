from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry._logs import set_logger_provider

from app.core.config import settings


def setup_telemetry(app) -> None:
    resource = Resource.create({"service.name": settings.otel_service_name})

    if settings.otel_traces_enabled:
        tracer_provider = TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=settings.otel_exporter_otlp_insecure,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)
        FastAPIInstrumentor.instrument_app(app)

    if settings.otel_logs_enabled:
        logger_provider = LoggerProvider(resource=resource)
        log_exporter = OTLPLogExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=settings.otel_exporter_otlp_insecure,
        )
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        set_logger_provider(logger_provider)
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)
        LoggingInstrumentor().instrument(set_logging_format=True)