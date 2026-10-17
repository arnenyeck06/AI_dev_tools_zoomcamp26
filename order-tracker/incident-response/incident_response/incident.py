"""Turns an alert plus collected context into files in an incident directory."""

import hashlib
import json
import re
from datetime import datetime, timezone

from incident_response.context import exception_summary


def incident_id(alert):
    """Stable per firing: the same alert re-notified by Grafana maps to the same incident."""
    started = alert.get("startsAt", "")
    key = f'{alert.get("fingerprint", "")}|{started}'
    stamp = re.sub(r"[^0-9]", "", started)[:14] or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{stamp}-{hashlib.sha1(key.encode()).hexdigest()[:8]}"


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, default=str) + "\n")


def write_status(directory, state, **details):
    status_path = directory / "status.json"
    status = json.loads(status_path.read_text()) if status_path.exists() else {"history": []}
    status["state"] = state
    status.update(details)
    status["history"].append({"state": state, "at": datetime.now(timezone.utc).isoformat()})
    write_json(status_path, status)


def write_context(directory, alert, context):
    write_json(directory / "metrics.json", context["metrics"])
    write_json(directory / "logs.json", context["logs"])
    write_json(directory / "traces.json", context["traces"])
    (directory / "incident.md").write_text(render_summary(alert, context))


def render_summary(alert, context):
    labels, annotations = alert["labels"], alert.get("annotations", {})
    logs, traces = context["logs"], context["traces"]
    errors = [log for log in logs if log["severity"] == "ERROR"]
    lines = [
        f"# Incident: {labels.get('alertname', 'alert')}",
        "",
        f"- **Summary:** {annotations.get('summary', '-')}",
        f"- **Description:** {annotations.get('description', '-')}",
        f"- **Service:** {context['service']}",
        f"- **Endpoint:** {annotations.get('endpoint') or context['endpoint'] or '-'}",
        f"- **Alert started:** {alert.get('startsAt', '-')}",
        f"- **Investigated window:** {context['window']['start']} to {context['window']['end']}"
        f" (lookback {labels.get('window', context['window']['lookback'])})",
        f"- **Severity:** {labels.get('severity', '-')}",
        f"- **Alert values:** {json.dumps(alert.get('values') or {})}",
        "",
        "## Links",
        "",
        f"- Dashboard: {annotations.get('dashboard_url') or alert.get('dashboardURL') or '-'}",
        f"- Panel: {alert.get('panelURL') or '-'}",
        f"- Alert rule: {alert.get('generatorURL') or '-'}",
        "",
        "## Requests by status code (over the lookback window)",
        "",
    ]
    by_status = context["metrics"].get("lookups_by_status_code", {})
    lines += [f"- `{code}`: {count}" for code, count in sorted(by_status.items())] or ["- no metric data"]

    lines += ["", "## Exceptions in error logs", ""]
    summary = exception_summary(logs)
    lines += [f"- {count}x `{kind}`: {message}" for (kind, message), count in summary] or ["- none found"]

    failing = sorted({log["order_id"] for log in errors if log.get("order_id")})
    lines += ["", "## Affected order ids", "", ", ".join(f"`{o}`" for o in failing) or "none found"]

    sample = next((log for log in errors if log.get("stacktrace")), None)
    if sample:
        lines += [
            "", "## Sample stack trace", "",
            f"From {sample['time']}, trace `{sample['trace_id']}`:", "",
            "```", sample["stacktrace"].rstrip(), "```",
        ]

    lines += ["", f"## Recent warning and error logs ({len(logs)}, newest first)", ""]
    lines += [f"- {log['time']} {log['severity']} {log['message']} (trace `{log['trace_id']}`)" for log in logs[:15]]

    lines += ["", f"## Error traces ({len(traces)})", ""]
    for trace in traces:
        lines.append(f"- trace `{trace['trace_id']}`")
        for span in trace["spans"]:
            attributes = ", ".join(f"{k}={v}" for k, v in span["attributes"].items())
            lines.append(
                f"  - span `{span['name']}` {span['duration_ms']} ms, {span['status']}"
                f"{': ' + span['status_message'] if span['status_message'] else ''} ({attributes})"
            )
    if context["errors"]:
        lines += ["", "## Collection errors", ""] + [f"- {error}" for error in context["errors"]]

    lines += [
        "", "## Files", "",
        "- `alert.json`: the alert as sent by Grafana",
        "- `metrics.json`, `logs.json`, `traces.json`: the raw collected context",
        "- `status.json`: incident processing state",
        "- `agent.log`: output of the coding agent (stream-json)",
        "- `report.md`: the agent's findings, once it finishes",
        "",
    ]
    return "\n".join(lines)
