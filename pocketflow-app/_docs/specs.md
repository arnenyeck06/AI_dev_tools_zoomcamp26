# PocketFlow — Spec

## Idea
Full-stack expense tracker for a two-person household (Homework 2:
Build and Ship an AI-Assisted Full-Stack App).

## Context
Not roommates splitting evenly — a two-person household planning shared
expenses month to month, deciding ahead of time who covers what.

## MVP features

1. **Expenses** — amount, category, date, assigned payer (not forced
   50/50), free-text note for context (e.g. "birthday splurge").
2. **Recurring bills** — known recurring bills (rent, utilities) are
   suggested each month, but require confirmation before being added —
   never auto-created silently.
3. **Budgets** — monthly budget per category, actual vs. budget
   comparison.
4. **Trends** — month-over-month spending by category, to spot
   recurring bills vs. one-off splurges.

## Stack
- Backend: Python + uv
- Frontend: Node.js
- Database: TBD (set during implementation)
