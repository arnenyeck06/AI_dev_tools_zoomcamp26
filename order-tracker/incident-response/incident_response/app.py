"""Incident responder: receives Grafana alerts, saves incident context, starts a coding agent.

Run with: uv run uvicorn incident_response.app:app --host 0.0.0.0 --port 8001
"""

import json
import logging
import os
import queue
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

from incident_response import agent, context
from incident_response.incident import incident_id, write_context, write_json, write_status


ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_DIR = Path(os.getenv("INCIDENTS_DIR", ROOT / "incidents"))
REPO_DIR = Path(os.getenv("REPO_DIR", ROOT.parent))
AGENT_ENABLED = os.getenv("AGENT_ENABLED", "true").lower() not in {"0", "false", "no"}

logger = logging.getLogger("incident_response")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# Incidents are handled one at a time, so two agents never edit the repo at once.
work = queue.Queue()


def handle(incident_dir, alert):
    write_status(incident_dir, "collecting_context")
    collected = context.collect(alert)
    write_context(incident_dir, alert, collected)
    logger.info("incident %s: saved %d logs and %d traces", incident_dir.name,
                len(collected["logs"]), len(collected["traces"]))

    if not AGENT_ENABLED:
        write_status(incident_dir, "context_saved", agent="disabled")
        return
    process = agent.start_agent(incident_dir, REPO_DIR)
    write_status(incident_dir, "agent_running", agent_pid=process.pid, agent_command=agent.AGENT_COMMAND)
    logger.info("incident %s: started agent pid %s", incident_dir.name, process.pid)
    exit_code = process.wait()
    write_status(incident_dir, "agent_finished", agent_exit_code=exit_code,
                 agent_result=agent.final_result(incident_dir / "agent.log"),
                 report=str(incident_dir / "report.md") if (incident_dir / "report.md").exists() else None)
    logger.info("incident %s: agent exited with %s", incident_dir.name, exit_code)


def worker():
    while True:
        incident_dir, alert = work.get()
        try:
            handle(incident_dir, alert)
        except Exception as exc:
            logger.exception("incident %s failed", incident_dir.name)
            write_status(incident_dir, "failed", error=repr(exc))
        finally:
            work.task_done()


@asynccontextmanager
async def lifespan(_app):
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=worker, daemon=True, name="incident-worker").start()
    yield


app = FastAPI(title="Incident Responder", lifespan=lifespan)


@app.get("/healthz")
def health():
    return {"status": "ok", "queued": work.qsize()}


@app.post("/alerts", status_code=202)
async def receive_alerts(request: Request):
    try:
        payload = await request.json()
        alerts = payload["alerts"]
    except (ValueError, KeyError, TypeError):
        raise HTTPException(400, "Expected a Grafana webhook payload with an 'alerts' list")

    accepted, duplicates, resolved = [], [], []
    for alert in alerts:
        directory = INCIDENTS_DIR / incident_id(alert)
        if alert.get("status") == "resolved":
            if directory.exists():
                write_json(directory / "resolved.json", alert)
                resolved.append(directory.name)
            continue
        try:
            # Grafana re-sends firing alerts; one firing is one incident.
            directory.mkdir(parents=True)
        except FileExistsError:
            duplicates.append(directory.name)
            continue
        write_json(directory / "alert.json", alert)
        write_status(directory, "queued")
        work.put((directory, alert))
        accepted.append(directory.name)
        logger.info("incident %s: %s on %s", directory.name,
                    alert["labels"].get("alertname"), alert["labels"].get("http_route"))
    return {"accepted": accepted, "duplicates": duplicates, "resolved": resolved}


@app.get("/incidents")
def list_incidents():
    return [
        {"id": path.name, **json.loads((path / "status.json").read_text())}
        for path in sorted(INCIDENTS_DIR.iterdir(), reverse=True)
        if (path / "status.json").exists()
    ]


@app.post("/incidents/{incident}/rerun", status_code=202)
def rerun(incident: str):
    """Collects the context again and restarts the agent, e.g. after fixing the agent's setup."""
    directory = INCIDENTS_DIR / incident
    if "/" in incident or not (directory / "alert.json").exists():
        raise HTTPException(404, "Incident not found")
    write_status(directory, "queued")
    work.put((directory, json.loads((directory / "alert.json").read_text())))
    return {"accepted": [incident]}
