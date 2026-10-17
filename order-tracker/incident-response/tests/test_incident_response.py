import base64
import json
import sys
from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from incident_response import agent, app as service, context


ALERT = {
    "status": "firing",
    "labels": {
        "alertname": "Order lookup 5xx responses",
        "http_route": "/api/orders/{order_id}",
        "service": "order-tracker",
        "severity": "critical",
        "window": "5m",
    },
    "annotations": {
        "summary": "5xx responses on GET /api/orders/{order_id}",
        "description": "GET /api/orders/{order_id} returned 2 5xx response(s) in the last 5 minutes.",
        "endpoint": "GET /api/orders/{order_id}",
        "dashboard_url": "http://127.0.0.1:3000/d/order-tracker",
    },
    "startsAt": "2026-10-17T15:03:40Z",
    "fingerprint": "abc123",
    "generatorURL": "http://127.0.0.1:3000/alerting/grafana/order-lookup-5xx/view",
    "values": {"A": 2, "C": 1},
}
TRACE_ID = "d2f556fd70097d63180ede64bb4afde7"
STACK = 'Traceback (most recent call last):\n  File "/app/app/main.py", line 80, in order_detail\nValueError: day is out of range for month\n'
FAKE_AGENT = """
import json, pathlib, sys
prompt = sys.argv[sys.argv.index("-p") + 1]
incident_dir = prompt.split("The incident data is in ")[1].split(":")[0]
pathlib.Path(incident_dir, "report.md").write_text("fixed")
print(json.dumps({"type": "result", "is_error": False, "result": "Fixed it"}))
"""
NOW = datetime(2026, 10, 17, 15, 4, tzinfo=timezone.utc)


def fake_backends(request):
    path = request.url.path
    if path == "/api/v1/query":
        assert 'http_route="/api/orders/{order_id}"' in request.url.params["query"]
        return httpx.Response(200, json={"data": {"result": [
            {"metric": {"http_response_status_code": "200"}, "value": [0, "10"]},
            {"metric": {"http_response_status_code": "500"}, "value": [0, "2.04"]},
        ]}})
    if path == "/loki/api/v1/query_range":
        return httpx.Response(200, json={"data": {"result": [{
            "stream": {"severity_text": "ERROR", "trace_id": TRACE_ID, "order_id": "express-1002",
                       "http_response_status_code": "500", "exception_type": "ValueError",
                       "exception_message": "day is out of range for month", "exception_stacktrace": STACK},
            "values": [["1792249406911264512", "Order lookup error: order_id=express-1002 status_code=500"]],
        }]}})
    if path == "/api/search":
        assert 'span.http.route="/api/orders/{order_id}"' in request.url.params["q"]
        return httpx.Response(200, json={"traces": [{"traceID": TRACE_ID}]})
    if path == f"/api/traces/{TRACE_ID}":
        return httpx.Response(200, json={"batches": [{"scopeSpans": [{"spans": [{
            "name": "order.lookup",
            "spanId": base64.b64encode(bytes.fromhex("f73242f68572be86")).decode(),
            "startTimeUnixNano": "1792249406910000000", "endTimeUnixNano": "1792249406911500000",
            "status": {"code": "STATUS_CODE_ERROR", "message": "day is out of range for month"},
            "attributes": [{"key": "order.id", "value": {"stringValue": "express-1002"}},
                           {"key": "http.response.status_code", "value": {"intValue": "500"}}],
            "events": [{"name": "exception", "attributes": []}],
        }]}]}]})
    return httpx.Response(404)


def test_collect_gathers_metrics_logs_and_traces():
    client = httpx.Client(transport=httpx.MockTransport(fake_backends))

    collected = context.collect(ALERT, client=client, now=NOW)

    assert collected["errors"] == []
    assert collected["endpoint"] == "/api/orders/{order_id}"
    assert collected["window"]["start"] == "2026-10-17T14:58:40+00:00"
    assert collected["metrics"] == {"lookups_by_status_code": {"200": 10.0, "500": 2.0}}
    [log] = collected["logs"]
    assert (log["trace_id"], log["order_id"], log["stacktrace"]) == (TRACE_ID, "express-1002", STACK)
    [trace] = collected["traces"]  # the same trace from logs and search is fetched once
    [span] = trace["spans"]
    assert span["span_id"] == "f73242f68572be86"
    assert span["status"] == "STATUS_CODE_ERROR"
    assert span["attributes"]["order.id"] == "express-1002"


def test_collect_records_unreachable_backend():
    def down(request):
        raise httpx.ConnectError("connection refused")

    collected = context.collect(ALERT, client=httpx.Client(transport=httpx.MockTransport(down)), now=NOW)

    assert [error.split(":")[0] for error in collected["errors"]] == ["metrics", "logs", "traces"]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "INCIDENTS_DIR", tmp_path / "incidents")
    monkeypatch.setattr(service, "REPO_DIR", tmp_path)
    fake = httpx.Client(transport=httpx.MockTransport(fake_backends))
    monkeypatch.setattr(context, "collect", lambda alert, real=context.collect: real(alert, client=fake, now=NOW))
    # A stand-in agent that writes a report and a stream-json result, so the
    # whole flow runs without Claude.
    fake_agent = tmp_path / "fake_agent.py"
    fake_agent.write_text(FAKE_AGENT)
    monkeypatch.setattr(agent, "AGENT_COMMAND", f"{sys.executable} {fake_agent}")
    with TestClient(service.app) as test_client:
        yield test_client


def test_alert_saves_incident_and_runs_agent(client, tmp_path):
    response = client.post("/alerts", json={"status": "firing", "alerts": [ALERT]})

    assert response.status_code == 202
    [incident] = response.json()["accepted"]
    service.work.join()
    directory = tmp_path / "incidents" / incident
    assert json.loads((directory / "alert.json").read_text()) == ALERT
    summary = (directory / "incident.md").read_text()
    for expected in ("GET /api/orders/{order_id}", "lookback 5m", "ValueError", "express-1002",
                     TRACE_ID, "http://127.0.0.1:3000/d/order-tracker", "day is out of range"):
        assert expected in summary
    assert json.loads((directory / "logs.json").read_text())[0]["trace_id"] == TRACE_ID
    status = json.loads((directory / "status.json").read_text())
    assert status["state"] == "agent_finished"
    assert status["agent_exit_code"] == 0
    assert status["agent_result"] == {"is_error": False, "message": "Fixed it"}
    assert (directory / "report.md").read_text() == "fixed"
    assert client.get("/incidents").json()[0]["id"] == incident


def test_repeated_notification_is_one_incident(client):
    first = client.post("/alerts", json={"alerts": [ALERT]}).json()
    again = client.post("/alerts", json={"alerts": [ALERT]}).json()
    service.work.join()

    assert again == {"accepted": [], "duplicates": first["accepted"], "resolved": []}


def test_resolved_alert_is_recorded(client, tmp_path):
    [incident] = client.post("/alerts", json={"alerts": [ALERT]}).json()["accepted"]
    service.work.join()

    response = client.post("/alerts", json={"alerts": [{**ALERT, "status": "resolved"}]})

    assert response.json()["resolved"] == [incident]
    assert (tmp_path / "incidents" / incident / "resolved.json").exists()


def test_rerun_runs_the_agent_again(client, tmp_path):
    [incident] = client.post("/alerts", json={"alerts": [ALERT]}).json()["accepted"]
    service.work.join()

    assert client.post(f"/incidents/{incident}/rerun").status_code == 202
    service.work.join()

    states = [entry["state"] for entry in client.get("/incidents").json()[0]["history"]]
    assert states.count("agent_finished") == 2
    assert client.post("/incidents/nope/rerun").status_code == 404


def test_rejects_non_grafana_payload(client):
    assert client.post("/alerts", json={"hello": "world"}).status_code == 400


def test_agent_command_is_headless_and_restricted(tmp_path):
    command = agent.build_command(tmp_path / "incident", tmp_path)

    assert command[0] == "claude"
    assert command[command.index("-p") + 1].startswith("An alert fired")
    assert command[command.index("--permission-mode") + 1] == "acceptEdits"
    assert "Bash(uv run --frozen pytest:*)" in command
    assert not any(tool.startswith("Bash(git push") or tool == "Bash" for tool in command)


def test_agent_env_drops_parent_session_but_keeps_credentials():
    env = agent.agent_env({
        "PATH": "/bin", "CLAUDECODE": "1", "CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH": "1",
        "CLAUDE_CODE_SESSION_ID": "x", "CLAUDE_CODE_OAUTH_TOKEN": "token", "ANTHROPIC_API_KEY": "key",
    })

    assert env == {"PATH": "/bin", "CLAUDE_CODE_OAUTH_TOKEN": "token", "ANTHROPIC_API_KEY": "key"}
