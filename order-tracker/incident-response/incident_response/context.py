"""Collects metrics, logs, and traces around an alert from Prometheus, Loki, and Tempo."""

import base64
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

import httpx


PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://127.0.0.1:9090")
LOKI_URL = os.getenv("LOKI_URL", "http://127.0.0.1:3100")
TEMPO_URL = os.getenv("TEMPO_URL", "http://127.0.0.1:3200")
MAX_LOGS = 50
MAX_TRACES = 5


def parse_window(text, default=timedelta(minutes=5)):
    match = re.fullmatch(r"(\d+)([smh])", text or "")
    if not match:
        return default
    unit = {"s": "seconds", "m": "minutes", "h": "hours"}[match[2]]
    return timedelta(**{unit: int(match[1])})


def parse_time(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def alert_window(alert, now=None):
    """The time range to investigate: the alert's lookback window before it started, until now."""
    now = now or datetime.now(timezone.utc)
    window = parse_window(alert["labels"].get("window"))
    started = parse_time(alert["startsAt"]) if alert.get("startsAt") else now
    return started - window, now, window


def collect(alert, client=None, now=None):
    """Returns {"metrics": ..., "logs": [...], "traces": [...], "errors": [...]}.

    Each backend is queried independently; a failing backend is recorded in
    "errors" instead of aborting the whole collection.
    """
    client = client or httpx.Client(timeout=10)
    start, end, window = alert_window(alert, now)
    labels = alert["labels"]
    service = labels.get("service", "order-tracker")
    route = labels.get("http_route")
    context = {
        "service": service,
        "endpoint": route,
        "window": {"start": start.isoformat(), "end": end.isoformat(), "lookback": str(window)},
        "metrics": {},
        "logs": [],
        "traces": [],
        "errors": [],
    }

    for name, step in (
        ("metrics", lambda: query_metrics(client, route, window, end)),
        ("logs", lambda: query_logs(client, service, start, end)),
    ):
        try:
            context[name] = step()
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            context["errors"].append(f"{name}: {exc!r}")

    try:
        trace_ids = [log["trace_id"] for log in context["logs"] if log.get("trace_id")]
        context["traces"] = query_traces(client, service, route, start, end, trace_ids)
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        context["errors"].append(f"traces: {exc!r}")
    return context


def query_metrics(client, route, window, at):
    selector = f'http_route="{route}"' if route else ""
    minutes = max(int(window.total_seconds() // 60), 1)
    response = client.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={
            "query": f"sum by (http_response_status_code) (increase(order_lookups_total{{{selector}}}[{minutes}m]))",
            "time": at.timestamp(),
        },
    )
    response.raise_for_status()
    results = response.json()["data"]["result"]
    return {
        "lookups_by_status_code": {
            r["metric"].get("http_response_status_code", "unknown"): round(float(r["value"][1]), 1)
            for r in results
        }
    }


def query_logs(client, service, start, end):
    """Warning and error logs for the service, newest first."""
    response = client.get(
        f"{LOKI_URL}/loki/api/v1/query_range",
        params={
            "query": f'{{service_name="{service}"}} | severity_text=~"ERROR|WARN.*"',
            "start": int(start.timestamp() * 1e9),
            "end": int(end.timestamp() * 1e9),
            "limit": MAX_LOGS,
            "direction": "backward",
        },
    )
    response.raise_for_status()
    logs = []
    for stream in response.json()["data"]["result"]:
        fields = stream["stream"]
        for timestamp, line in stream["values"]:
            logs.append({
                "time": datetime.fromtimestamp(int(timestamp) / 1e9, timezone.utc).isoformat(),
                "severity": fields.get("severity_text"),
                "message": line,
                "trace_id": fields.get("trace_id"),
                "order_id": fields.get("order_id"),
                "status_code": fields.get("http_response_status_code"),
                "exception_type": fields.get("exception_type"),
                "exception_message": fields.get("exception_message"),
                "stacktrace": fields.get("exception_stacktrace"),
            })
    logs.sort(key=lambda log: log["time"], reverse=True)
    return logs[:MAX_LOGS]


def query_traces(client, service, route, start, end, trace_ids):
    """Error traces for the endpoint: those referenced by error logs first, then a TraceQL search."""
    condition = f'resource.service.name="{service}" && status=error'
    if route:
        condition += f' && span.http.route="{route}"'
    response = client.get(
        f"{TEMPO_URL}/api/search",
        params={"q": "{" + condition + "}", "start": int(start.timestamp()),
                "end": int(end.timestamp()) + 1, "limit": MAX_TRACES},
    )
    response.raise_for_status()
    found = [t["traceID"] for t in response.json().get("traces", [])]

    ids = list(dict.fromkeys(trace_ids + found))[:MAX_TRACES]
    traces = []
    for trace_id in ids:
        trace = client.get(f"{TEMPO_URL}/api/traces/{trace_id}")
        if trace.status_code == 404:
            continue
        trace.raise_for_status()
        traces.append({"trace_id": trace_id, "spans": summarize_spans(trace.json())})
    return traces


def otlp_value(value):
    return next(iter(value.values()), None) if value else None


def otlp_attributes(attributes):
    return {a["key"]: otlp_value(a.get("value")) for a in attributes or []}


def summarize_spans(trace):
    spans = []
    for batch in trace.get("batches", trace.get("resourceSpans", [])):
        for scope in batch.get("scopeSpans", []):
            for span in scope.get("spans", []):
                duration_ms = (int(span["endTimeUnixNano"]) - int(span["startTimeUnixNano"])) / 1e6
                spans.append({
                    "name": span["name"],
                    # Tempo returns OTLP JSON with base64-encoded ids.
                    "span_id": base64.b64decode(span["spanId"]).hex(),
                    "start": datetime.fromtimestamp(int(span["startTimeUnixNano"]) / 1e9, timezone.utc).isoformat(),
                    "duration_ms": round(duration_ms, 3),
                    "status": span.get("status", {}).get("code", "STATUS_CODE_UNSET"),
                    "status_message": span.get("status", {}).get("message"),
                    "attributes": otlp_attributes(span.get("attributes")),
                    "events": [
                        {"name": event["name"], "attributes": otlp_attributes(event.get("attributes"))}
                        for event in span.get("events", [])
                    ],
                })
    return spans


def exception_summary(logs):
    """Counts of (exception type, message) across error logs."""
    return Counter(
        (log["exception_type"], log["exception_message"])
        for log in logs
        if log.get("exception_type")
    ).most_common()
