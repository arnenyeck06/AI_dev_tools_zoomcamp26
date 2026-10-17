import pytest
from fastapi.testclient import TestClient
from opentelemetry.trace import StatusCode

from app import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "orders.db")
    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client


def lookup_count(telemetry, status_code):
    data = telemetry.metrics.get_metrics_data()
    if data is None:
        return 0
    for resource_metrics in data.resource_metrics:
        for scope_metrics in resource_metrics.scope_metrics:
            for metric in scope_metrics.metrics:
                if metric.name != "order_lookups":
                    continue
                for point in metric.data.data_points:
                    if point.attributes == {
                        "http.route": "/api/orders/{order_id}",
                        "http.response.status_code": status_code,
                    }:
                        return point.value
    return 0


def lookup_spans(telemetry):
    return [span for span in telemetry.spans.get_finished_spans() if span.name == "order.lookup"]


def lookup_logs(telemetry):
    return [item.log_record for item in telemetry.logs.get_finished_logs()]


@pytest.mark.parametrize(
    ("order_id", "status_code", "severity"),
    [("standard-1001", 200, "INFO"), ("missing", 404, "WARN")],
)
def test_lookup_telemetry(client, telemetry, order_id, status_code, severity):
    before = lookup_count(telemetry, status_code)

    assert client.get(f"/api/orders/{order_id}").status_code == status_code

    assert lookup_count(telemetry, status_code) == before + 1
    [span] = lookup_spans(telemetry)
    assert span.attributes["order.id"] == order_id
    assert span.attributes["http.response.status_code"] == status_code
    assert span.status.status_code == StatusCode.UNSET
    [log] = lookup_logs(telemetry)
    assert log.severity_text == severity
    assert log.attributes["order.id"] == order_id
    assert log.trace_id == span.context.trace_id


def test_failed_lookup_is_recorded_as_error(client, telemetry, monkeypatch):
    def broken_order_detail(row):
        raise ValueError("day is out of range for month")

    monkeypatch.setattr(main, "order_detail", broken_order_detail)
    before = lookup_count(telemetry, 500)

    assert client.get("/api/orders/express-1002").status_code == 500

    assert lookup_count(telemetry, 500) == before + 1
    [span] = lookup_spans(telemetry)
    assert span.status.status_code == StatusCode.ERROR
    assert span.events[0].name == "exception"
    [log] = lookup_logs(telemetry)
    assert log.severity_text == "ERROR"
    assert log.trace_id == span.context.trace_id
    assert "ValueError" in log.attributes["exception.type"]


def test_5xx_series_exists_before_any_error(telemetry):
    # Prometheus' increase() ignores a counter's first sample, so the 500 series
    # must already exist for the first 500 to trigger the alert.
    data = telemetry.metrics.get_metrics_data()
    points = [
        dict(point.attributes)
        for resource_metrics in data.resource_metrics
        for scope_metrics in resource_metrics.scope_metrics
        for metric in scope_metrics.metrics
        if metric.name == "order_lookups"
        for point in metric.data.data_points
    ]
    assert {"http.route": "/api/orders/{order_id}", "http.response.status_code": 500} in points
