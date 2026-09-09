# Backlog: Household Chores Manager

Derived from `_docs/plan.md`. Tasks are ordered so each builds on the last.
Scope is v1 MVP — no enjoyment ratings, no adaptive rotation.

## 1. Data model & admin ✅
- [x] `Household` model (name, created_at).
- [x] `Membership` model linking `User` ↔ `Household` with a `role` field
      (`parent` / `member`); at-most-one parent per household enforced by a
      partial unique constraint ("exactly one" is task #2 flow logic).
- [x] `Chore` model: title, description, `chore_type` (`recurring` / `one_off`),
      household FK, active flag, created_at.
- [x] `ChoreAssignment` model: chore FK, assignee FK, `due_date`, `week_start`
      (null for one-off), status (`pending` / `done`), `completed_at`.
- [x] `Grade` model: assignment FK (one-to-one), score `1..5` (validators +
      check constraint), graded_by FK, graded_at.
- [x] Register all models in `chores/admin.py`; `0001_initial` migration created
      and applied.
- **Done when:** models migrate cleanly and are editable in Django admin. ✅
      `manage.py check` clean; parent-uniqueness constraint smoke-tested.

## 2. Household & roles
- [ ] Signup / login using Django auth (built-in views + templates).
- [ ] "Create household" flow — creator becomes the parent.
- [ ] Parent-only "add member" (invite by username/email or create account).
- [ ] Parent-only member list with role display; block removing the last parent.
- [ ] `parent_required` decorator / mixin for view protection.
- **Done when:** a parent can create a household and add two members; a member
      hitting a parent-only URL gets 403.

## 3. Chore management & round-robin assignment
- [ ] Parent CRUD for chores (list, create, edit, deactivate).
- [ ] Assignment helper: given a chore, pick the next member round-robin
      (order by membership id, track last assignee on the chore).
- [ ] On chore create: generate the first `ChoreAssignment`.
- [ ] One-off chore: single assignment with a due date.
- **Done when:** creating 3 chores across a 3-member household assigns each to a
      different member in rotation.

## 4. Weekly re-rotation
- [ ] Management command `rotate_chores` that, for each active recurring chore,
      creates next week's assignment for the next member in rotation.
- [ ] Idempotent — running twice for the same `week_start` is a no-op.
- [ ] Document running it via cron / scheduler in README.
- **Done when:** running the command produces exactly one new assignment per
      recurring chore, advancing the rotation.

## 5. Completion tracking
- [ ] Member dashboard: "my chores this week" (pending + done).
- [ ] "Mark done" action on a pending assignment owned by the current user
      (sets status + `completed_at`); reject if not the assignee.
- [ ] Household activity view for the parent: recent completions.
- **Done when:** a member marks their chore done and it moves to the done list;
      another member cannot mark it.

## 6. Grading
- [ ] Parent view: list of completed-but-ungraded assignments.
- [ ] Grade form: score 1-5, one grade per assignment (edit allowed).
- [ ] Member "my grades" page: table of graded chores with score + date, and a
      simple average.
- **Done when:** a parent grades a completed chore and the member sees the score
      and updated average.

## 7. Polish & safety net
- [ ] Base template + minimal nav (role-aware links).
- [ ] Redirect users with no household to the create/join flow.
- [ ] Tests: round-robin helper, weekly rotation idempotency, completion
      permission check, grade score validation.
- [ ] README: setup, migrate, create superuser, run server, run `rotate_chores`.
- **Done when:** `python manage.py test` passes and a fresh clone runs from the
      README steps alone.
