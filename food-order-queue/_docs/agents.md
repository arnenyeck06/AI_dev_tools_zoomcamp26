# Agent team

The project is built by one human product owner working with a team of AI agents. Each agent is a Claude Code session with a defined role, inputs, outputs, and limits. Agents coordinate through **GitHub Issues and pull requests**, not through chat, so every hand-off is visible.

## Roles

| Role | Who | Responsibilities | Inputs | Outputs | May not |
| --- | --- | --- | --- | --- | --- |
| **Product owner** | Human (Arne) | Owns the spec, prioritizes issues, approves plans, reviews and merges PRs, triggers production deploys | Spec, PRs, alerts | Decisions, merges | — |
| **Planner** | Claude Code (plan mode) | Turns spec features into small GitHub issues with acceptance criteria and test notes; keeps `_docs/tasks.md` in sync | `_docs/spec.md`, product owner's request | Issues labeled `ready` | Write code |
| **Builder** | Claude Code | Implements one `ready` issue: failing tests first, then code; opens a PR | One issue, `AGENTS.md`, spec | Branch, tests, PR with `Closes #N` | Change scope, merge, deploy |
| **Tester** | Claude Code | Adds missing frontend and integration tests for an issue's acceptance criteria; checks edge cases (FIFO, concurrency, privacy) | Issue, PR diff | Extra tests on the PR, review comment listing gaps | Change app behavior |
| **Reviewer** | Claude Code (`/code-review`) | Reviews each PR against the issue's acceptance criteria, `AGENTS.md` rules, and for bugs | PR diff, issue | Review comments; approve or request changes | Merge |
| **On-call** | Headless Claude Code started by the incident responder | Wakes on a Grafana alert, reads the saved logs, traces, and metrics, finds the root cause, writes a fix with a regression test, opens a PR | Alert payload, incident context | Incident report, fix PR | Merge, deploy, restart production |

## How they work together

```
Product owner ──spec──> Planner ──issues (ready)──> Builder ──PR──> Tester ──tests──> Reviewer
      ^                                                                                  │
      └────────────────────────── approve, merge, deploy ────────────────────────────────┘

Grafana alert ──webhook──> incident responder ──starts──> On-call agent ──fix PR──> Reviewer ──> Product owner
```

1. The **product owner** asks the **Planner** to break a spec feature into issues.
2. The **Planner** creates issues with acceptance criteria and labels them `ready`.
3. A **Builder** picks one `ready` issue, comments "starting", and works on a branch `issue-N-short-name`.
4. The Builder opens a PR. The **Tester** adds tests for uncovered criteria.
5. The **Reviewer** checks the PR against the criteria. Problems go back to the Builder as review comments.
6. The **product owner** approves and merges. CI/CD deploys to dev; the product owner promotes to production.
7. In production, an alert wakes the **On-call** agent, which opens a fix PR that goes through the same review.

## Why this split

- **Separate planning from building**, so scope is fixed before code is written.
- **Separate building from reviewing and testing**, so no agent grades its own work.
- **Humans stay in control of merges and deploys.** Agents propose; the product owner decides.
