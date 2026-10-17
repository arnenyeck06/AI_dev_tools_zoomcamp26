# Order Tracker

A small order tracking app for the AI Dev Tools Zoomcamp observability homework. It includes a web page, API, tests, and a Docker Compose setup. You add telemetry, alerts, and an incident responder in Homework 4.

The main user flow is creating an order and checking its status. Three sample orders are created on first startup.

## Run it

You need Docker with Compose. To run the tests, you also need Python 3.11+ and `uv`.

```bash
docker compose up --build -d --wait
```

Open <http://127.0.0.1:8000>. The API is at `/api/orders`, and the health check is at `/healthz`. Data is stored in a Docker volume and survives container recreation.

If port 8000 is occupied, set `ORDER_TRACKER_PORT`, for example:

```bash
ORDER_TRACKER_PORT=18080 docker compose up --build -d --wait
```

Run tests with `uv run --frozen pytest -q`. Stop the app with `docker compose down`. Add `-v` only if you also want to delete the order data.

## Observability

`docker compose up` also starts an observability stack. All configuration lives in [`observability/`](observability/).

```
app --OTLP/HTTP--> otel-collector --metrics--> Prometheus (scrapes :8889)
                                  --logs-----> Loki (OTLP)
                                  --traces---> Tempo (OTLP)
                   Grafana reads Prometheus, Loki, and Tempo
```

| Service | URL | Config |
| --- | --- | --- |
| Grafana | <http://127.0.0.1:3000> (no login) | `observability/grafana/` |
| Prometheus | <http://127.0.0.1:9090> | `observability/prometheus.yaml` |
| OpenTelemetry Collector | internal, `otel-collector:4318` | `observability/otel-collector.yaml` |
| Loki | internal, `loki:3100` | `observability/loki.yaml` |
| Tempo | internal, `tempo:3200` | `observability/tempo.yaml` |

Set `GRAFANA_PORT` or `PROMETHEUS_PORT` if those ports are taken. Grafana opens on the provisioned **Order Tracker** dashboard: lookup counts, 5xx and 404 counts, error rate, lookups per second by status code, errors per second, latency, failed traces, and warning/error logs. Log lines link to their trace in Tempo.

### Alert

Grafana has a provisioned alert rule, **Order lookup 5xx responses** (`observability/grafana/provisioning/alerting/alert-rules.yaml`). It is evaluated every 30 seconds and fires as soon as an endpoint returns any 5xx response in the last 5 minutes. It resolves once a 5-minute window passes with no 5xx.

- **Labels:** `http_route`, `severity=critical`, `service=order-tracker`, `window=5m`.
- **Annotations:** `summary`, `description` (endpoint and 5xx count), `endpoint`, `window`, and `dashboard_url`. It also carries `__dashboardUid__`/`__panelId__`, so Grafana links the alert to the "Errors per second" panel.
- **No 5xx:** the query returns 0 for endpoints with traffic, so the rule is Normal. With no data at all, `noDataState: OK` keeps it Normal instead of raising a No Data alert.
- The app starts the 5xx counter at 0. Prometheus' `increase()` ignores a counter's first sample, so without that the first 500 after a restart would be missed.

See it under **Alerting → Alert rules** in Grafana. Notifications go to the `incident-responder` webhook contact point.

### Incident responder

[`incident-response/`](incident-response/) is a service on port 8001 that receives the alert at `POST /alerts`. For each incident it saves the alert, the affected endpoint, the window, metrics, error logs with stack traces, and error traces into `incident-response/incidents/<id>/`. It then starts Claude Code in headless mode to find and fix the cause. It runs on the host:

```bash
cd incident-response && uv run uvicorn incident_response.app:app --host 0.0.0.0 --port 8001
```

See [incident-response/README.md](incident-response/README.md).

Order lookups (`GET /api/orders/{id}`) emit:

| Signal | Name | Details |
| --- | --- | --- |
| Metric | `order_lookups_total` | Counter labelled `http_route` and `http_response_status_code` |
| Metric | `order_lookup_duration_seconds` | Histogram with the same labels |
| Trace | `order.lookup` span | `order.id`, `http.route`, `http.response.status_code`; errors record the exception |
| Log | `order_tracker` logger | INFO on success, WARN on 4xx, ERROR with stack trace on 5xx; carries `trace_id` |

Without `OTEL_EXPORTER_OTLP_ENDPOINT` (for example `uv run uvicorn app.main:app`), the app prints the signals to the console instead.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Web page |
| GET | `/healthz` | Database health check |
| GET | `/api/orders` | List orders |
| POST | `/api/orders` | Create an order |
| GET | `/api/orders/{id}` | Check an order |
| PATCH | `/api/orders/{id}` | Change an order status |

The app uses SQLite to keep setup small. Run one app container at a time. The course exercise is about detecting and handling an incident, not scaling the database.
