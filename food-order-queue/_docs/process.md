# Development process

## Workflow for every change

1. **Spec first.** If the change adds or alters behavior, update `_docs/spec.md` (with acceptance criteria) before any code. The product owner approves spec changes.
2. **Issue.** The Planner creates a GitHub issue using the template below and labels it `ready`.
3. **Branch.** The Builder comments "starting" on the issue and creates `issue-N-short-name` from `main`.
4. **Tests first.** Add tests that fail for each acceptance criterion.
5. **Implement** the smallest change that makes them pass. Run the full test suite.
6. **Pull request** titled after the issue, with `Closes #N` and a checklist of the acceptance criteria.
7. **CI** runs all tests on the PR. A red build is never merged.
8. **Review.** The Tester fills test gaps; the Reviewer checks criteria, rules in `AGENTS.md`, and bugs.
9. **Merge** by the product owner. CD deploys `main` to **dev** automatically.
10. **Release.** The product owner runs the manual **deploy to production** workflow. If production breaks, run the **rollback** workflow to redeploy the previous version.

## Issue template

```markdown
## Goal
One sentence: what and why. Link the spec section (e.g. spec §F6).

## Acceptance criteria
- [ ] Observable behavior 1
- [ ] Observable behavior 2

## Test notes
Which tests prove each criterion (unit / frontend / integration).

## Out of scope
What this issue does not do.
```

## Labels

| Label | Meaning |
| --- | --- |
| `ready` | Has acceptance criteria; can be picked up |
| `in progress` | A Builder is working on it |
| `backend`, `frontend`, `infra`, `docs`, `ai` | Area |
| `incident` | Opened by the On-call agent from an alert |

## Definition of done

- All acceptance criteria checked in the PR, each covered by a test
- All tests pass locally and in CI
- No customer names or phone numbers in logs, traces, or AI prompts
- Docs updated if behavior or commands changed
- Merged to `main` and deployed to dev

## Commit messages

Imperative, one line, referencing the issue: `Add duplicate-order flag (#5)`.
