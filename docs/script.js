import json
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, Form, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
import uvicorn

from utils import CredentialManager

app = FastAPI()
templates = Jinja2Templates(directory="templates")
cred_manager = CredentialManager()

CONFIG_FILE = Path("config.json")

# ───────────────────────────────── helpers ────────────────────────────────────

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {"accounts": [], "tasks": []}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)


# ──────────────────────────────── models ──────────────────────────────────────

class TaskCreate(BaseModel):
    retailer: str
    product_url: str

    account_label: str
    login_email: str
    login_password: str

    hour: int
    minute: int
    second: int
    ampm: str          # "AM" or "PM"
    timezone: str      # "CST", "EST", "PST", "MST"

    desired_quantity: int
    max_quantity: int
    max_price: float
    max_spend: float

    enabled: bool


class Task(TaskCreate):
    id: str
    last_run: Optional[str] = None  # ISO string


# ──────────────────────────────── logging ─────────────────────────────────────

log_messages: List[str] = []


def log(message: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] {message}"
    log_messages.append(entry)
    # keep last 500 lines
    if len(log_messages) > 500:
        del log_messages[0:len(log_messages) - 500]


# ───────────────────────────── scheduler state ────────────────────────────────

scheduler = BackgroundScheduler()
scheduler.start()
scheduler_running = False


def _task_time_matches(now: datetime, t: dict) -> bool:
    try:
        hour = int(t.get("hour", 0))
        minute = int(t.get("minute", 0))
        second = int(t.get("second", 0))
        ampm = t.get("ampm", "AM").upper()
    except Exception:
        return False

    if ampm == "PM" and hour != 12:
        hour_24 = hour + 12
    elif ampm == "AM" and hour == 12:
        hour_24 = 0
    else:
        hour_24 = hour

    return (
        now.hour == hour_24
        and now.minute == minute
        and now.second == second
    )


def run_due_tasks():
    cfg = load_config()
    tasks = cfg.get("tasks", [])
    now = datetime.now()

    for t in tasks:
        if not t.get("enabled", False):
            continue

        if _task_time_matches(now, t):
            log(f"Running task {t.get('id')} for {t.get('retailer')} {t.get('product_url')}")
            t["last_run"] = now.isoformat()

    cfg["tasks"] = tasks
    save_config(cfg)


def start_scheduler():
    global scheduler_running
    if not scheduler_running:
        scheduler.add_job(run_due_tasks, "interval", seconds=5, id="task_runner", replace_existing=True)
        scheduler_running = True
        log("Scheduler started")


def stop_scheduler():
    global scheduler_running
    if scheduler_running:
        try:
            scheduler.remove_job("task_runner")
        except Exception:
            pass
        scheduler_running = False
        log("Scheduler stopped")


# ──────────────────────────────── routes: html ────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    cfg = load_config()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "accounts": cfg.get("accounts", [])}
    )


# ──────────────────────────────── routes: accounts ────────────────────────────

@app.post("/accounts/add")
def add_account(
    label: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    cfg = load_config()
    accounts = cfg.get("accounts", [])

    accounts.append({
        "id": str(uuid.uuid4()),
        "label": label,
        "email": email,
        "password": cred_manager.encrypt(password)
    })

    cfg["accounts"] = accounts
    save_config(cfg)

    return RedirectResponse("/", status_code=303)


@app.post("/accounts/delete")
def delete_account(account_id: str = Form(...)):
    cfg = load_config()
    accounts = cfg.get("accounts", [])
    accounts = [a for a in accounts if a["id"] != account_id]
    cfg["accounts"] = accounts
    save_config(cfg)
    return RedirectResponse("/", status_code=303)


@app.post("/accounts/toggle-price-limit")
def toggle_price_limit(account_id: str = Form(...)):
    cfg = load_config()
    accounts = cfg.get("accounts", [])

    for acc in accounts:
        if acc["id"] == account_id:
            acc["price_limit_enabled"] = not acc.get("price_limit_enabled", False)

    cfg["accounts"] = accounts
    save_config(cfg)
    return RedirectResponse("/", status_code=303)


@app.get("/accounts/list")
def api_accounts_list():
    cfg = load_config()
    return cfg.get("accounts", [])


# ──────────────────────────────── routes: tasks api ───────────────────────────

@app.get("/tasks", response_model=List[Task])
def api_list_tasks():
    cfg = load_config()
    tasks = cfg.get("tasks", [])
    result = []
    for t in tasks:
        try:
            result.append(Task(**t))
        except Exception:
            continue
    return result


@app.post("/tasks/add", response_model=Task)
def api_add_task(body: TaskCreate):
    cfg = load_config()
    tasks = cfg.get("tasks", [])

    task_id = str(uuid.uuid4())
    task = Task(id=task_id, last_run=None, **body.dict())

    tasks.append(task.dict())
    cfg["tasks"] = tasks
    save_config(cfg)

    log(f"Task created: {task_id} ({body.retailer})")
    return task


@app.post("/tasks/update", response_model=Task)
def api_update_task(task_id: str, body: TaskCreate):
    cfg = load_config()
    tasks = cfg.get("tasks", [])

    for i, t in enumerate(tasks):
        if t.get("id") == task_id:
            last_run = t.get("last_run")
            updated = Task(id=task_id, last_run=last_run, **body.dict())
            tasks[i] = updated.dict()
            cfg["tasks"] = tasks
            save_config(cfg)
            log(f"Task updated: {task_id}")
            return updated

    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/tasks/delete")
def api_delete_task(task_id: str):
    cfg = load_config()
    tasks = cfg.get("tasks", [])

    tasks = [t for t in tasks if t.get("id") != task_id]
    cfg["tasks"] = tasks
    save_config(cfg)

    log(f"Task deleted: {task_id}")
    return {"status": "deleted"}


# ──────────────────────────────── routes: scheduler api ───────────────────────

@app.post("/scheduler/start")
def api_scheduler_start():
    start_scheduler()
    return {"status": "running"}


@app.post("/scheduler/stop")
def api_scheduler
