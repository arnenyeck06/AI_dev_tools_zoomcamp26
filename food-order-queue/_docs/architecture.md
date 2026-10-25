# Architecture

## Components

```
 Browser
  ├─ Customer page (#/)          ─┐
  └─ Staff dashboard (#/staff)   ─┤  React + Vite
                                  │  /api/* (Vite proxy in dev, reverse proxy in Docker)
                                  ▼
                           FastAPI backend ──────────> Claude API (AI note check, F7)
                             │      │
                             │      └─ OpenTelemetry ──> Collector ──> Prometheus (metrics)
                             ▼                                   ├──> Loki (logs)
                      SQLite / PostgreSQL                        └──> Tempo (traces)
                                                                        │
                                                    Grafana (dashboards + alert rules)
                                                                        │ webhook
                                                                        ▼
                                                     Incident responder ──> On-call agent (Claude Code)
```

| Component | Status | Notes |
| --- | --- | --- |
| Frontend | Built | Hash routes `#/` and `#/staff`; polls the API (5 s ticket, 3 s dashboard) |
| Backend | Built | FastAPI + SQLModel; FIFO by ascending order id |
| Database | SQLite built; PostgreSQL planned | `DATABASE_URL` selects the database |
| Anomaly rules | Planned (F6) | Run synchronously when an order is placed |
| AI check | Planned (F7) | Called after the order is saved; 5 s timeout; failure never blocks the order |
| Observability stack | Planned | Reuses the OpenTelemetry + Grafana setup from the course's order-tracker homework |
| Incident responder | Planned | Receives Grafana alerts at `POST /alerts`, saves context, starts the On-call agent |

## Key decisions

- **FIFO by id, not timestamp.** Ids increase with insertion, so ordering by id is exact even when two orders share a timestamp.
- **Polling, not WebSockets.** A few-second delay is fine for a food counter and keeps the backend simple.
- **Flags never block orders.** A false positive must not cost a real customer their food.
- **Minimal data to the AI.** Only item, quantity, and note go to Claude; name and phone stay in our database.

## Configuration

| Variable | Used by | Default |
| --- | --- | --- |
| `DATABASE_URL` | backend | `sqlite:///orders.db` |
| `ANTHROPIC_API_KEY` | backend (F7) | read from `backend/.env` |
| `API_URL` | frontend dev proxy | `http://localhost:8010` |
