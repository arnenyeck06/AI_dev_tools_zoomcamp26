# PocketFlow — frontend

React + TypeScript + Vite. Implements the four MVP features from
`../_docs/specs.md`: expenses, recurring bills, budgets, and trends.

## Running

```bash
npm install
npm run dev
```

## No backend yet

There is no server behind this app. Every "backend call" goes through
a single mock client at `src/api/client.ts`, which exposes the same
shape a real API would (`api.expenses.list()`, `api.budgets.set()`,
etc.) but is backed by an in-memory store seeded from
`src/api/mockData.ts`. State resets on page reload.

When a real backend exists, `client.ts` is the only file that should
need to change — pages import `api` and don't know or care that it's
mocked.

## Structure

- `src/api/` — types, mock data, and the centralized client.
- `src/components/` — shared UI pieces (forms, budget meters, nav, tags).
- `src/pages/` — one component per tab (Dashboard, Expenses, Recurring
  Bills, Budgets, Trends).
- `src/lib/date.ts` — month/date helpers shared across pages.
