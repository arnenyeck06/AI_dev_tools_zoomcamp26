# Food Order Queue

A small web app for a food stand or counter: customers place food orders online, staff serve them strictly **first in, first out (FIFO)**, and the system **flags orders that look wrong** (spam, duplicates, unusual quantities) so staff can check them before cooking.

Final project for the [AI Dev Tools Zoomcamp 2026](https://courses.datatalks.club/ai-dev-tools-2026/).

## The problem

Small food businesses often take orders on paper, by phone, or through chat messages. That causes three recurring problems:

1. **Orders get served out of order.** Without a shared queue, whoever shouts loudest gets served first, and customers who ordered earlier wait longer.
2. **Customers don't know where they stand.** They keep asking "is my order ready?", which interrupts the kitchen.
3. **Bad orders waste food.** Prank orders, accidental duplicates, or a typo like 100 burgers instead of 1 only get noticed after the food is made.

## What the system does

| For | Feature |
| --- | --- |
| Customers | Place an order (name, phone, item, quantity, optional note) and get a ticket number |
| Customers | See their place in line update live, until the order is ready |
| Staff | See a live dashboard of orders in **Waiting**, **In progress**, and **Done** |
| Staff | Press **Serve next** to take the oldest waiting order: nobody can skip the line |
| Staff | Mark orders done; see queue stats (waiting count, average wait) |
| Staff | See **anomaly flags** with a reason on suspicious orders (rule-based checks plus an AI check of the order note) |

## Expected behavior

- Every order gets a unique ticket number and a position in line (1 = next to be served).
- **Serve next** always takes the waiting order that arrived first. Positions of everyone behind it move up by one.
- An order goes `waiting → in_progress → done`, never backwards and never skipping a step.
- Invalid orders (empty name, phone too short, quantity outside 1–100) are rejected with a clear error.
- Flagged orders are **still served in FIFO order**; the flag is a warning for staff, not a rejection.
- If the AI check is unavailable, orders are still accepted and only the rule-based flags apply.
- Orders persist across restarts.

Full requirements and acceptance criteria: [`_docs/spec.md`](_docs/spec.md). Progress is tracked in [GitHub Issues](https://github.com/arnenyeck06/AI_dev_tools_zoomcamp26/issues).

## Tech stack

| Layer | Choice | Role |
| --- | --- | --- |
| Frontend | React + Vite + TypeScript | Customer page and staff dashboard; all API calls go through `src/api.ts` |
| Backend | FastAPI (Python 3.12) + SQLModel | REST API under `/api`: FIFO queue, anomaly rules, OpenAPI docs at `/docs` |
| Database | SQLite locally, PostgreSQL in Docker Compose | Orders and flags; `DATABASE_URL` picks the database |
| Web server | nginx (in Docker) | Serves the built React app and forwards `/api` to the backend |
| Containers | Docker Compose | Runs database, backend, and frontend with one command |
| AI | Claude API (order note check) | Planned |

See [`_docs/architecture.md`](_docs/architecture.md) for how the parts fit together.

## Run it with Docker (one command)

You need [Docker](https://docs.docker.com/get-docker/) with Compose.

```bash
docker compose up --build
```

| URL | What |
| --- | --- |
| <http://localhost:8080> | Customer page |
| <http://localhost:8080/#/staff> | Staff dashboard |
| <http://localhost:8080/docs> | API docs (OpenAPI) |

Data is stored in PostgreSQL in the `pgdata` volume, so it survives `docker compose down` and restarts. To start over with an empty database: `docker compose down -v`.

## Run it locally for development

Uses SQLite (`backend/orders.db`) and hot reload. You need Python 3.12 with [uv](https://docs.astral.sh/uv/) and Node.js 20+.

```bash
# API (http://localhost:8010, docs at /docs)
cd backend && uv run uvicorn main:app --reload --port 8010

# Frontend (http://localhost:5173), in a second terminal
cd frontend && npm install && npm run dev
```

Open <http://localhost:5173> for the customer page and <http://localhost:5173/#/staff> for the staff dashboard. The frontend proxies `/api` to the backend.

If you pull a change that adds database columns, delete `backend/orders.db` once; it is recreated on start.

### AI check setup

Put your Anthropic API key in `backend/.env` (git-ignored):

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Tests

```bash
cd backend && uv run python -m pytest -q
```

The tests use a fresh SQLite file per test. To run the same tests against PostgreSQL:

```bash
docker run -d --rm --name orders-test-db -e POSTGRES_USER=orders -e POSTGRES_PASSWORD=orders -e POSTGRES_DB=orders -p 55432:5432 postgres:17-alpine
cd backend && TEST_DATABASE_URL=postgresql+psycopg://orders:orders@localhost:55432/orders uv run python -m pytest -q
docker stop orders-test-db
```

## Project structure

```
food-order-queue/
├── AGENTS.md          # Instructions for AI coding agents (start here)
├── README.md          # This file
├── _docs/
│   ├── spec.md        # Product spec and acceptance criteria
│   ├── architecture.md
│   ├── agents.md      # Agent team: roles and how they work together
│   ├── process.md     # Workflow: issue → branch → tests → PR → deploy
│   └── tasks.md       # Task list (mirrored in GitHub Issues)
├── docker-compose.yml # db + api + web, one command
├── backend/           # FastAPI app, tests, Dockerfile
└── frontend/          # React app, Dockerfile, nginx.conf
```
