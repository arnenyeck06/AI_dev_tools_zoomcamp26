# Product specification: Food Order Queue

## 1. Goal

Let a small food business take orders online, serve them in strict arrival order, and catch suspicious orders before food is wasted.

## 2. Users

| User | Needs |
| --- | --- |
| **Customer** | Order quickly from a phone, know their place in line, know when food is ready |
| **Staff** (counter or kitchen) | One shared queue, a fair "next order" rule, early warning about bad orders |

There is no login in the MVP: the staff dashboard is reached at `#/staff`. Access control is out of scope (see §8).

## 3. Order lifecycle

```
waiting ──(Serve next)──> in_progress ──(Mark done)──> done
```

- New orders start as `waiting`.
- Only the **oldest** `waiting` order can move to `in_progress` (FIFO).
- Only an `in_progress` order can move to `done`.

## 4. Features and acceptance criteria

### F1. Place an order

A customer submits name, phone, item, quantity, and an optional note.

- [ ] Given valid input, the API returns `201` with the order's ticket number (`id`), `status = waiting`, and `position` in line.
- [ ] `customer_name` is 1–80 characters, `phone` 7–20 characters, `item` 1–120 characters, `quantity` 1–100, `note` up to 500 characters; anything else returns `422` with the failing field.
- [ ] The customer page shows the ticket number and position right after submitting.

### F2. Track my order

- [ ] `GET /api/orders/{id}` returns the order with its current status and position (`null` once no longer waiting).
- [ ] The ticket view refreshes at least every 5 seconds and shows "You're #N in line", "You're next!", "being prepared", or "ready".
- [ ] An unknown id returns `404`.

### F3. Serve next (FIFO)

- [ ] `POST /api/orders/next` moves the oldest `waiting` order to `in_progress` and returns it.
- [ ] After serving, every remaining waiting order's position decreases by exactly 1.
- [ ] With no waiting orders it returns `404` and changes nothing.
- [ ] Two staff pressing **Serve next** at the same time never receive the same order.

### F4. Complete an order

- [ ] `POST /api/orders/{id}/done` moves an `in_progress` order to `done`.
- [ ] Completing an order in any other status returns `409` and changes nothing.

### F5. Staff dashboard

- [ ] Shows three columns (Waiting, In progress, Done) refreshed at least every 3 seconds.
- [ ] Waiting and In progress are sorted oldest first; Done shows the 10 most recent.
- [ ] Shows counts per status and the average wait of waiting orders.
- [ ] **Serve next** is disabled when nothing is waiting.
- [ ] If the API is unreachable, the dashboard shows an error instead of stale data silently.

### F6. Rule-based anomaly flags

Each new order is checked against these rules. Long wait is checked whenever a waiting order is read, so it appears as time passes. A matching order gets a flag with `source = rule`, a `reason`, and a `severity`.

| Rule | Default threshold | Severity |
| --- | --- | --- |
| Burst: same phone places several orders quickly | ≥ 3 orders in 10 minutes | high |
| Duplicate: same phone and same item | within 2 minutes | medium |
| Large quantity | quantity > 20 | medium |
| Long wait: order still waiting much longer than usual | > 2× the median wait of the last 50 served orders and > 15 minutes | low |

- [x] Each rule has unit tests for "just below" and "just above" its threshold.
- [x] Flags are returned with the order (`flags: [{source, reason, severity}]`).
- [x] The staff dashboard shows a badge per flag with its reason; high severity is visually distinct.
- [x] Flagged orders stay in the queue in FIFO order (flags never reorder or reject orders).

### F7. AI order check

When an order has a note, the backend asks Claude to classify it.

- [ ] The model returns structured output: `{suspicious: bool, category: string, reason: string}`.
- [ ] A suspicious result adds a flag with `source = ai` and the model's reason.
- [ ] Only the order's item, quantity, and note are sent to the model, never the customer's name or phone.
- [ ] If the API key is missing, the call fails, or it takes longer than 5 seconds, the order is still accepted without an AI flag, and the failure is logged.
- [ ] Tests mock the model; no test calls the real API.

### F8. Shift summary (stretch goal)

- [ ] A staff button produces a short AI summary of today's orders: totals, average wait, flags by type, busiest hour.

## 5. Non-functional requirements

| Area | Requirement |
| --- | --- |
| Persistence | Orders and flags survive restarts (SQLite locally, PostgreSQL in Docker Compose) |
| Single command | `docker compose up` starts frontend, backend, database, and observability stack |
| Tests | Unit, frontend, and integration tests run with one command and pass in CI |
| Privacy | Customer names and phone numbers never appear in logs, traces, or metrics; use the order id instead |
| Observability | The "place order → serve → done" journey emits metrics, traces, and structured logs that share a trace id, viewable in Grafana |
| Alerting | An alert fires on user impact: order placement failures (5xx) or customers waiting too long, not CPU or memory |
| On call | An agent receives the alert, investigates with logs and traces, and proposes a fix as a pull request |
| Delivery | CI runs tests on every pull request; CD deploys `main` to dev automatically; production deploys are manual and can be rolled back |

## 6. API summary

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/orders` | Place an order |
| GET | `/api/orders?status=` | List orders in arrival order |
| GET | `/api/orders/{id}` | One order with position |
| POST | `/api/orders/next` | Serve the oldest waiting order |
| POST | `/api/orders/{id}/done` | Complete an order |
| GET | `/healthz` | Health check |

## 7. Data model

**orders**: `id`, `customer_name`, `phone`, `item`, `quantity`, `note`, `status`, `created_at`, `served_at`

**flags** (F6/F7): `id`, `order_id`, `source` (`rule` / `ai`), `reason`, `severity`, `created_at`

## 8. Out of scope

Payments, user accounts and staff login, menus with prices, multiple locations, SMS notifications.
