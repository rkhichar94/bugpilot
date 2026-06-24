import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db import create_run, get_run, init_db, list_runs, update_run

PROJECT_DIR = Path(__file__).parent
LOG_DIR = Path("/tmp/bugpilot-logs")
LOG_DIR.mkdir(exist_ok=True)

STAGE_MAP = {
    "[clone_repo]": ("CLONING", "clone_repo"),
    "[issue_analyst]": ("ANALYZING", "issue_analyst"),
    "[fix_generator]": ("FIXING", "fix_generator"),
    "[test_runner]": ("TESTING", "test_runner"),
    "[pr_creator]": ("CREATING_PR", "pr_creator"),
}

app = FastAPI(title="BugPilot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


# ── Background pipeline execution ────────────────────────────────────────────

def _parse_log(run_id: str, log_path: Path):
    try:
        content = log_path.read_text(errors="replace")
    except FileNotFoundError:
        return

    status, stage, pr_url, error = None, None, None, None

    for marker, (s, g) in STAGE_MAP.items():
        if marker in content:
            status, stage = s, g

    for line in content.splitlines():
        if "PR created:" in line:
            pr_url = line.split("PR created:")[-1].strip()
            status = "AWAITING_APPROVAL"
        if "Result: AWAITING_APPROVAL" in line:
            status = "AWAITING_APPROVAL"
        if "[main] FAILED for" in line:
            status = "FAILED"
            error = line

    kwargs: dict = {}
    if status:
        kwargs["status"] = status
    if stage:
        kwargs["stage"] = stage
    if pr_url:
        kwargs["pr_url"] = pr_url
    if error:
        kwargs["error"] = error
    if kwargs:
        update_run(run_id, **kwargs)


def run_pipeline_bg(run_id: str, issue_key: str):
    log_path = LOG_DIR / f"{run_id}.log"
    update_run(run_id, status="CLONING", stage="clone_repo")
    try:
        with open(log_path, "w", buffering=1) as lf:
            proc = subprocess.Popen(
                [sys.executable, "main.py", "--issue", issue_key],
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=str(PROJECT_DIR),
                env=os.environ.copy(),
            )
            while proc.poll() is None:
                _parse_log(run_id, log_path)
                time.sleep(0.8)
            _parse_log(run_id, log_path)

            run = get_run(run_id)
            if proc.returncode != 0 and run and run["status"] not in (
                "AWAITING_APPROVAL", "APPROVED", "REJECTED"
            ):
                update_run(run_id, status="FAILED", error=f"Process exited {proc.returncode}")
    except Exception as exc:
        update_run(run_id, status="FAILED", error=str(exc))


# ── API routes ────────────────────────────────────────────────────────────────

class StartRunRequest(BaseModel):
    issue_key: str
    summary: str = ""


@app.post("/api/runs")
def start_run(body: StartRunRequest, background_tasks: BackgroundTasks):
    run_id = uuid.uuid4().hex[:8]
    create_run(run_id, body.issue_key.upper(), body.summary)
    background_tasks.add_task(run_pipeline_bg, run_id, body.issue_key.upper())
    return {"run_id": run_id}


@app.get("/api/runs")
def get_runs():
    return list_runs()


@app.get("/api/runs/{run_id}")
def get_run_detail(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@app.get("/api/runs/{run_id}/logs")
def get_logs(run_id: str, offset: int = 0):
    log_path = LOG_DIR / f"{run_id}.log"
    if not log_path.exists():
        return {"lines": [], "offset": 0, "done": False}
    lines = log_path.read_text(errors="replace").splitlines()
    run = get_run(run_id)
    done = run and run["status"] in ("AWAITING_APPROVAL", "FAILED", "APPROVED", "REJECTED")
    return {"lines": lines[offset:], "offset": len(lines), "done": bool(done)}


@app.get("/api/runs/{run_id}/diff")
def get_diff(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(404)
    from config import settings
    workspace = Path(settings.workspace_dir) / run["issue_key"]
    if not workspace.exists():
        return {"diff": ""}
    result = subprocess.run(
        ["git", "diff", "HEAD"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
    )
    return {"diff": result.stdout}


@app.post("/api/runs/{run_id}/approve")
def approve_run(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(404)
    if run.get("pr_url"):
        try:
            from github import Github
            from config import settings
            gh = Github(settings.github_token)
            # Extract owner/repo from PR URL
            parts = run["pr_url"].rstrip("/").split("/")
            pr_num = int(parts[-1])
            repo_full = f"{parts[-4]}/{parts[-3]}"
            pr = gh.get_repo(repo_full).get_pull(pr_num)
            pr.merge(merge_method="squash")
        except Exception:
            pass
    update_run(run_id, status="APPROVED")
    return {"status": "APPROVED"}


@app.post("/api/runs/{run_id}/reject")
def reject_run(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(404)
    if run.get("pr_url"):
        try:
            from github import Github
            from config import settings
            gh = Github(settings.github_token)
            parts = run["pr_url"].rstrip("/").split("/")
            pr_num = int(parts[-1])
            repo_full = f"{parts[-4]}/{parts[-3]}"
            pr = gh.get_repo(repo_full).get_pull(pr_num)
            pr.edit(state="closed")
        except Exception:
            pass
    update_run(run_id, status="REJECTED")
    return {"status": "REJECTED"}


# ── Serve built frontend ──────────────────────────────────────────────────────

_dist = PROJECT_DIR / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="static")
