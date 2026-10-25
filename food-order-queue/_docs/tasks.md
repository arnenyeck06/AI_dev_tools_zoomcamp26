# Tasks

Planned work, in order. The live tracker is [GitHub Issues](https://github.com/arnenyeck06/AI_dev_tools_zoomcamp26/issues) (label `food-order-queue`); this file mirrors it. Each task follows the issue template in [`process.md`](process.md).

| # | Task | Area | Status |
| --- | --- | --- | --- |
| T1 | Orders API with FIFO serving | backend | Done (`92e741f`) |
| T2 | Customer order form and staff dashboard | frontend | Done (`71544a5`) |
| T3 | Project docs: README, spec, AGENTS.md, agent team, process | docs | In progress |
| T4 | Rule-based anomaly flags | backend, frontend | To do |
| T5 | AI order check with Claude | backend, ai | To do |
| T6 | Frontend tests | frontend | To do |
| T7 | Integration tests | backend, frontend | To do |
| T8 | Docker Compose with PostgreSQL, single-command start | infra | To do |
| T9 | Observability for the order journey | backend, infra | To do |
| T10 | Alert on user impact | infra | To do |
| T11 | On-call agent | infra, ai | To do |
| T12 | CI: tests on every pull request | infra | To do |
| T13 | CD: auto-deploy to dev, manual production deploy with rollback | infra | To do |
| T14 | Public deployment | infra | To do |
| T15 | Shift summary (stretch) | backend, frontend, ai | To do |

---

## T1. Orders API with FIFO serving

Spec §F1–F4.

- [x] `POST /api/orders` returns `201` with id, `waiting` status, and position
- [x] Invalid input returns `422`
- [x] `POST /api/orders/next` serves the oldest waiting order; others move up by 1
- [x] Empty queue returns `404`
- [x] `POST /api/orders/{id}/done` only works on `in_progress` orders (`409` otherwise)
- [ ] Two simultaneous **Serve next** calls never return the same order

## T2. Customer order form and staff dashboard

Spec §F1, F2, F5.

- [x] Customer form with validation and a ticket showing ticket number and position
- [x] Ticket refreshes every 5 s through waiting, preparing, ready
- [x] Staff dashboard with three columns refreshing every 3 s, Serve next, Mark done, stats
- [x] Serve next disabled when nothing is waiting; API errors are shown

## T3. Project docs

- [ ] README describes the problem, functionality, expected behavior, and how to run
- [ ] `_docs/spec.md` has acceptance criteria for every feature
- [ ] `AGENTS.md` points to modular docs (spec, architecture, agents, process, tasks)
- [ ] `_docs/agents.md` defines roles and how agents hand off work
- [ ] Tasks exist as GitHub issues

## T4. Rule-based anomaly flags

Spec §F6.

- [ ] `flags` table; flags returned with each order
- [ ] Burst, duplicate, large-quantity, and long-wait rules with the spec thresholds
- [ ] Unit tests just below and just above each threshold
- [ ] Staff dashboard shows a badge with the reason; high severity stands out
- [ ] Flagged orders keep their FIFO position

## T5. AI order check with Claude

Spec §F7.

- [ ] Orders with a note are classified with structured output `{suspicious, category, reason}`
- [ ] Suspicious results add a flag with `source = ai`
- [ ] Only item, quantity, and note are sent; tested by asserting on the mocked request
- [ ] Missing key, error, or > 5 s timeout: order still accepted, failure logged
- [ ] Tests mock the model

## T6. Frontend tests

- [ ] Vitest + Testing Library set up; `npm test` runs them
- [ ] Order form: validation errors shown, ticket shown after submit
- [ ] Dashboard: columns render from API data; Serve next disabled when empty; flag badges render

## T7. Integration tests

- [ ] Tests run the real API against a real database (SQLite file and PostgreSQL in CI)
- [ ] End-to-end journey: place three orders → serve → done, checking positions at each step
- [ ] One command runs all backend, frontend, and integration tests

## T8. Docker Compose with PostgreSQL

- [ ] Dockerfiles for backend and frontend
- [ ] `docker compose up` starts frontend, backend, and PostgreSQL; data survives restarts
- [ ] README documents the single command

## T9. Observability for the order journey

- [ ] Place order, serve next, and done emit OpenTelemetry traces, metrics (`orders_placed_total`, `order_wait_seconds`, request counts by route and status), and structured logs sharing a trace id
- [ ] No customer name or phone in any signal (tested)
- [ ] Collector, Prometheus, Loki, Tempo, and Grafana in Docker Compose with a provisioned dashboard

## T10. Alert on user impact

- [ ] Grafana alert when order placement returns 5xx, or when the oldest waiting order exceeds a wait threshold
- [ ] Alert annotations include endpoint, window, and dashboard link
- [ ] Normal state when there are no errors

## T11. On-call agent

- [ ] Grafana sends alerts to an incident responder at `POST /alerts`
- [ ] Responder saves alert, logs, traces, and metrics, then starts Claude Code headless
- [ ] Agent fixes the cause, adds a regression test, and writes a report; demonstrated with an injected bug

## T12. CI

- [ ] GitHub Actions workflow runs backend, frontend, and integration tests on every pull request touching `food-order-queue/`

## T13. CD with rollback

- [ ] Merging to `main` deploys to dev automatically
- [ ] Manual workflow deploys a chosen version to production
- [ ] Rollback workflow redeploys the previous production version

## T14. Public deployment

- [ ] App reachable at a public URL, linked in the README
- [ ] Hosting provider chosen (decision pending)

## T15. Shift summary (stretch)

Spec §F8.

- [ ] Staff button returns an AI summary of today's orders
