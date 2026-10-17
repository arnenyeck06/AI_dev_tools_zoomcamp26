# Incident responder

Receives Grafana alerts, saves what's needed to understand the problem, and starts a coding agent (Claude Code, headless) to investigate and fix it.

```
Grafana alert --webhook--> POST /alerts (:8001)
                             |- incidents/<id>/alert.json         (as sent by Grafana)
                             |- query Prometheus, Loki, Tempo for the alert's window
                             |- incidents/<id>/incident.md        (summary: endpoint, window, exceptions,
                             |                                      stack trace, affected orders, logs, traces, links)
                             |- metrics.json, logs.json, traces.json
                             '- claude -p "<investigate incident.md, fix, add a test, write report.md>"
                                  -> incidents/<id>/agent.log, report.md, status.json
```

It runs on the host, not in Docker, so it can start your local `claude` CLI against this repository. Grafana reaches it at `http://host.docker.internal:8001/alerts` (see `observability/grafana/provisioning/alerting/contact-points.yaml`).

## Run

You need the Order Tracker stack running (`docker compose up --build -d --wait` in the repo root) and the `claude` CLI installed and logged in. Check the login with `claude -p "say ok"`.

```bash
cd incident-response
uv run uvicorn incident_response.app:app --host 0.0.0.0 --port 8001
```

Trigger the alert by causing a 500, for example `curl http://localhost:8000/api/orders/express-1002`. About 20 to 40 seconds later, an incident appears in `incidents/` and the agent starts.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/alerts` | Grafana webhook. Returns 202 with accepted, duplicate, and resolved incident ids |
| GET | `/incidents` | Incidents with their state (`queued`, `collecting_context`, `agent_running`, `agent_finished`, `failed`) |
| POST | `/incidents/{id}/rerun` | Collect context again and rerun the agent, for example after logging in to `claude` |
| GET | `/healthz` | Health check |

## Behaviour

- **One firing is one incident.** The id comes from the alert fingerprint and start time, so Grafana's repeat notifications are reported as duplicates. A resolved notification is saved as `resolved.json` in the incident.
- **One agent at a time.** Incidents are queued and handled in order, so two agents never edit the code at once.
- **The agent is restricted.** It runs with `--permission-mode acceptEdits` and an allow-list: read, search, edit, `uv run pytest`, and read-only `git`. Headless mode denies anything else, so it can't commit, push, or touch Docker. Review its changes yourself (`git diff`) and its `report.md`.
- **A backend failure doesn't stop the response.** If Prometheus, Loki, or Tempo can't be reached, the error is listed in `incident.md` and the agent still runs.

## Configuration

| Variable | Default |
| --- | --- |
| `PROMETHEUS_URL` | `http://127.0.0.1:9090` |
| `LOKI_URL` | `http://127.0.0.1:3100` |
| `TEMPO_URL` | `http://127.0.0.1:3200` |
| `INCIDENTS_DIR` | `incident-response/incidents` (git-ignored) |
| `REPO_DIR` | the Order Tracker repo root |
| `AGENT_COMMAND` | `claude` |
| `AGENT_ENABLED` | `true`. Set `false` to only save context |

## Tests

```bash
uv run pytest -q
```
