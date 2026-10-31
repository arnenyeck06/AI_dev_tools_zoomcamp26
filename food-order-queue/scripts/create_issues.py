"""Creates the GitHub issues for food-order-queue from _docs/tasks.md.

Dry run by default: prints what it would do. Pass --apply to create the labels
and issues with the `gh` CLI (you must be logged in: `gh auth status`).

    uv run --no-project python scripts/create_issues.py            # dry run
    uv run --no-project python scripts/create_issues.py --apply    # create them
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = "arnenyeck06/AI_dev_tools_zoomcamp26"
TASKS = Path(__file__).resolve().parent.parent / "_docs" / "tasks.md"

LABELS = {
    "food-order-queue": ("0e8a16", "Food order queue final project"),
    "ready": ("1d76db", "Has acceptance criteria; can be picked up"),
    "in progress": ("fbca04", "A Builder is working on it"),
    "backend": ("5319e7", "Area: FastAPI backend"),
    "frontend": ("c5def5", "Area: React frontend"),
    "infra": ("bfd4f2", "Area: Docker, CI/CD, observability, hosting"),
    "docs": ("0075ca", "Area: documentation"),
    "ai": ("d93f0b", "Area: Claude integration or agents"),
    "incident": ("b60205", "Opened by the On-call agent from an alert"),
}

# Tasks already finished before the tracker existed: closed with the commit that did them.
DONE = {
    "T2": "Done in 71544a5 (customer order form and staff dashboard).",
    "T3": "Done in 5d3512d (README, spec, AGENTS.md, agent team, process, tasks). "
          "The last criterion is met by creating these issues.",
}
# Tasks mostly done but left open for a remaining criterion.
PARTIAL = {
    "T1": "Implemented in 92e741f. Left open: the concurrency criterion "
          "(two simultaneous Serve next calls) still needs a test and a fix.",
}


def parse_tasks(text):
    """Returns [(id, title, areas, spec_ref, criteria)] from the table and sections."""
    table = {m[0]: (m[1].strip(), m[2]) for m in re.findall(r"^\| (T\d+) \| ([^|]+) \| ([^|]+) \|", text, re.M)}
    tasks = []
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        heading, _, body = block.partition("\n")
        m = re.match(r"(T\d+)\. (.+)", heading.strip())
        if not m:
            continue
        task_id, title = m.groups()
        spec = re.search(r"^Spec (§.+?)\.?$", body, re.M)
        criteria = re.findall(r"^- \[([ x])\] (.+)$", body, re.M)  # [(tick, text)]
        title, area_list = table.get(task_id, (title, ""))  # the table has the full title
        task_areas = [a.strip() for a in area_list.split(",") if a.strip()]
        tasks.append((task_id, title, task_areas, spec.group(1) if spec else None, criteria))
    return tasks


def issue_body(task_id, title, spec, criteria, ticked):
    goal = f"{title}." + (f" See spec {spec} in `food-order-queue/_docs/spec.md`." if spec else "")
    lines = [
        "## Goal", goal, "",
        "## Acceptance criteria", *[f"- [{'x' if ticked else tick}] {c}" for tick, c in criteria], "",
        "## Test notes",
        "Each criterion is covered by a test (unit, frontend, or integration) before the PR is merged.", "",
        "## Out of scope", "Anything not listed above; see the other tasks.", "",
        f"_Mirrors {task_id} in `food-order-queue/_docs/tasks.md`._",
    ]
    return "\n".join(lines)


def gh(*args, apply):
    print("  $ gh " + " ".join(f'"{a}"' if " " in a else a for a in args[:6]) + (" ..." if len(args) > 6 else ""))
    if apply:
        return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout.strip()
    return f"https://github.com/{REPO}/issues/<new>"


def main(apply):
    tasks = parse_tasks(TASKS.read_text())
    print(f"{'Creating' if apply else 'Dry run:'} {len(LABELS)} labels and {len(tasks)} issues in {REPO}\n")

    for name, (color, description) in LABELS.items():
        gh("label", "create", name, "--repo", REPO, "--color", color, "--description", description, "--force", apply=apply)

    for task_id, title, areas, spec, criteria in tasks:
        done = task_id in DONE
        labels = ["food-order-queue", *areas] + ([] if done or task_id in PARTIAL else ["ready"])
        print(f"\n{task_id}: {title}  [{', '.join(labels)}]" + ("  (will close)" if done else ""))
        url = gh("issue", "create", "--repo", REPO, "--title", f"{task_id}: {title}",
                 "--body", issue_body(task_id, title, spec, criteria, ticked=done),
                 *[arg for label in labels for arg in ("--label", label)], apply=apply)
        print(f"  -> {url}")
        if done:
            gh("issue", "close", url, "--repo", REPO, "--comment", DONE[task_id], apply=apply)
        elif task_id in PARTIAL:
            gh("issue", "comment", url, "--repo", REPO, "--body", PARTIAL[task_id], apply=apply)

    if not apply:
        print("\nNothing was created. Run again with --apply to create them.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
