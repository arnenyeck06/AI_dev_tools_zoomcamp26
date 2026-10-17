"""Starts the coding agent (Claude Code) in headless mode for an incident."""

import json
import os
import shlex
import subprocess
from pathlib import Path


AGENT_COMMAND = os.getenv("AGENT_COMMAND", "claude")
# Tools the agent may use without a human approving them. Headless mode denies
# everything else, so it can read and edit code and run the tests, but cannot
# commit, push, or touch Docker.
ALLOWED_TOOLS = [
    "Read", "Edit", "Write", "Glob", "Grep",
    "Bash(uv run --frozen pytest:*)", "Bash(uv run pytest:*)",
    "Bash(git diff:*)", "Bash(git status:*)", "Bash(git log:*)",
]

PROMPT = """\
An alert fired for the Order Tracker service and you are the on-call engineer.

The incident data is in {incident_dir}:
- incident.md: summary of the alert, endpoint, time window, exceptions, stack trace, logs, and traces
- alert.json, metrics.json, logs.json, traces.json: the raw data

The Order Tracker code is in {repo_dir} (FastAPI app in app/, tests in tests/).

1. Read incident.md and find the root cause in the code.
2. Fix it with the smallest correct change.
3. Add a regression test that fails without the fix.
4. Run the tests with `uv run --frozen pytest -q` from {repo_dir} and make sure they pass.
5. Write {incident_dir}/report.md with: what users saw, root cause (file and line), the fix,
   the test you added, and test results.

Do not commit, push, rebuild containers, or change anything in incident-response/ or observability/.
"""


def build_command(incident_dir, repo_dir):
    prompt = PROMPT.format(incident_dir=incident_dir, repo_dir=repo_dir)
    return [
        *shlex.split(AGENT_COMMAND),
        "-p", prompt,
        "--permission-mode", "acceptEdits",
        "--allowedTools", *ALLOWED_TOOLS,
        "--output-format", "stream-json",
        "--verbose",
    ]


def agent_env(environ):
    """The environment without the parent Claude Code session's variables.

    When this service is started from a Claude Code session, those variables
    make the agent expect the parent app to provide its login. The agent must
    use its own (`claude auth login`, or CLAUDE_CODE_OAUTH_TOKEN / ANTHROPIC_API_KEY).
    """
    return {
        key: value for key, value in environ.items()
        if key not in {"CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT"}
        and not key.startswith(("CLAUDE_CODE_", "CLAUDE_AGENT_SDK_", "CLAUDE_PREVIEW_"))
        or key == "CLAUDE_CODE_OAUTH_TOKEN"
    }


def start_agent(incident_dir: Path, repo_dir: Path):
    """Starts the agent in the background; its output goes to agent.log."""
    env = agent_env(os.environ)
    with open(incident_dir / "agent.log", "w") as log:
        return subprocess.Popen(
            build_command(incident_dir, repo_dir),
            cwd=repo_dir,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )


def final_result(log_path: Path):
    """The agent's closing message from its stream-json log, if it got that far."""
    result = None
    for line in log_path.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "result":
            result = {"is_error": event.get("is_error"), "message": event.get("result")}
    return result
