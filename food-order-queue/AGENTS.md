# AGENTS.md: Food Order Queue

Instructions for AI coding agents (Claude Code and others) working in `food-order-queue/`. Read this first, then the doc for your task.

## What this project is

A FIFO food order queue: customers place orders, staff serve them in arrival order, and suspicious orders get flagged by rules and an AI check. See [`README.md`](README.md) for the overview.

## Docs map

| Read | When |
| --- | --- |
| [`_docs/spec.md`](_docs/spec.md) | Always, before changing behavior. It is the source of truth for features and acceptance criteria |
| [`_docs/architecture.md`](_docs/architecture.md) | Before touching how components connect (API, DB, proxy, telemetry) |
| [`_docs/agents.md`](_docs/agents.md) | To know your role and who hands work to whom |
| [`_docs/process.md`](_docs/process.md) | For the workflow: issue → branch → tests → PR → deploy |
| [`_docs/tasks.md`](_docs/tasks.md) | Task list; the live version is in [GitHub Issues](https://github.com/arnenyeck06/AI_dev_tools_zoomcamp26/issues) |

## Commands

| Task | Command |
| --- | --- |
| Run API | `cd backend && uv run uvicorn main:app --reload --port 8010` |
| Run frontend | `cd frontend && npm run dev` |
| Backend tests | `cd backend && uv run python -m pytest -q` |
| Frontend build + type check | `cd frontend && npm run build` |
| Frontend lint | `cd frontend && npm run lint` |

## Rules

1. **Work from an issue.** Every change belongs to a GitHub issue with acceptance criteria. Reference it in the branch name, commits, and PR (`Closes #N`). Comment on the issue when you start and when you finish.
2. **Follow the spec.** Don't add features that aren't in `_docs/spec.md`. If something is unclear or the spec seems wrong, stop and ask the product owner.
3. **Tests first.** Write or update a test that fails for each acceptance criterion, then make it pass. Never call the real Claude API in tests; mock it.
4. **Keep FIFO sacred.** Nothing may reorder the queue. Flags are warnings, never filters.
5. **Protect customer data.** Never log, trace, or send to the AI model a customer's name or phone number. Use the order id.
6. **Small, scoped changes.** Touch only what the issue needs. No speculative abstractions.
7. **Never commit secrets.** API keys live in `backend/.env` (git-ignored).
8. **Humans own git history.** Don't commit, push, merge, or deploy to production without explicit approval from the product owner.

## Code layout

- `backend/main.py`: FastAPI app, SQLModel models, endpoints
- `backend/tests/`: pytest tests (API tests use a temporary SQLite database)
- `frontend/src/api.ts`: typed API client; all requests go through it
- `frontend/src/OrderForm.tsx`: customer page and ticket
- `frontend/src/StaffDashboard.tsx`: staff queue dashboard
- `frontend/vite.config.ts`: proxies `/api` to the backend (`API_URL`, default `http://localhost:8010`)
