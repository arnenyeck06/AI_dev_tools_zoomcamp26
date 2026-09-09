# Plan: Household Chores Manager

## Starting idea
"A tool for managing shared household chores" (vague, given).

## Spec

### Users & roles
- Multi-user household
- One "parent" (admin) role: manages members, chores, grades
- Regular members: complete chores, view own history

### Chores
- Two types: recurring (weekly) and one-off
- Both auto-assigned round-robin across household members
- Recurring chores re-rotate weekly

### Completion
- Self-reported by the assigned member — no parent approval step

### Grading
- Parent grades each completed chore, 1-5 scale
- Members can see their own grade history over time

### Out of scope (v1)
- Enjoyment ratings
- Smart/adaptive rotation based on grade history (future work)

## MVP features (4)
1. Household & roles — parent creates household, adds members, admin permissions
2. Chore management — create chores (recurring/one-off), round-robin auto-assignment
3. Completion tracking — member marks chore done
4. Grading — parent rates 1-5, members view grade history

## Tech
- Django
