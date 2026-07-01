"""
Web UI server for Purchase Bot.

Easiest way to start:
    Windows: double-click start_ui.bat
    Manual:  python server.py

Then open: http://localhost:8100
"""

import json
import os
import uuid
import base64
import webbrowser
from urllib.parse import urlencode
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

from models import PurchaseTask, is_window_schedule
from utils import CredentialManager
from app_paths import CONFIG_FILE, ensure_parent

app = FastAPI(title="Purchase Bot UI")
templates = Jinja2Templates(directory="templates")
cred_manager = CredentialManager()
CONFIG_FILE = CONFIG_FILE


# ── helpers ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    # Try environment variable first (for Railway/cloud deployment)
    env_config = os.environ.get('CONFIG_JSON')
    if env_config:
        try:
            config_bytes = base64.b64decode(env_config)
            return json.loads(config_bytes.decode())
        except Exception as e:
            print(f"[ERROR] Failed to load CONFIG_JSON from env: {e}")
            return {"tasks": []}
    
    # Fall back to file-based (for local development)
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"tasks": []}


def save_config(config: dict):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def load_accounts() -> dict:
    return cred_manager.load_credentials()


def save_accounts(accounts: dict):
    cred_manager.save_credentials(accounts)


def redirect(tab: str = "accounts", msg: str = ""):
    query = urlencode({"tab": tab, "msg": msg})
    return RedirectResponse(url=f"/?{query}", status_code=303)


def parse_days(days: Optional[str]) -> list[str]:
    return [day.strip() for day in (days or "").split(",") if day.strip()]


def normalize_task(task: dict) -> dict:
    """Validate and normalize task fields before persisting config."""
    return PurchaseTask.from_dict(task).to_dict()


# ── pages ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, tab: str = "accounts", msg: str = ""):
    return templates.TemplateResponse(request, "ui.html", {
        "accounts": load_accounts(),
        "tasks":    load_config()["tasks"],
        "tab":      tab,
        "msg":      msg,
    })


# ── accounts ──────────────────────────────────────────────────────────────────

@app.post("/accounts/add")
async def add_account(
    account_id:          str           = Form(...),
    site:                str           = Form(...),
    email:               str           = Form(...),
    password:            str           = Form(...),
    payment_method:      str           = Form("credit_card"),
    monthly_limit:       float         = Form(1000.0),
    price_limit_per_item: float        = Form(500.0),
    price_limit_enabled: Optional[str] = Form(None),
    quantity_limit:      Optional[str] = Form(None),
    use_default_address: Optional[str] = Form(None),
    full_name:           str           = Form(""),
    line1:               str           = Form(""),
    line2:               str           = Form(""),
    city:                str           = Form(""),
    state:               str           = Form(""),
    zip_code:            str           = Form(""),
    country:             str           = Form("US"),
):
    accounts = load_accounts()
    if account_id in accounts:
        return redirect("accounts")

    qty = int(quantity_limit) if quantity_limit and quantity_limit.strip() else None
    addr = None
    if not use_default_address and line1.strip():
        addr = dict(full_name=full_name, line1=line1, line2=line2,
                    city=city, state=state, zip_code=zip_code, country=country)

    accounts = cred_manager.add_account(
        accounts, account_id, site, email, password,
        payment_method, monthly_limit, price_limit_per_item,
        price_limit_enabled="on",  # enabled by default
        quantity_limit_per_item=qty,
        shipping_address=addr,
    )
    save_accounts(accounts)
    return redirect("accounts")


@app.post("/accounts/delete")
async def delete_account(account_id: str = Form(...)):
    accounts = load_accounts()
    accounts.pop(account_id, None)
    save_accounts(accounts)
    return redirect("accounts")


@app.post("/accounts/toggle-price-limit")
async def toggle_price_limit(account_id: str = Form(...)):
    accounts = load_accounts()
    if account_id in accounts:
        current = accounts[account_id].get("price_limit_enabled", True)
        accounts[account_id]["price_limit_enabled"] = not current
        save_accounts(accounts)
    return redirect("accounts")


# ── tasks ─────────────────────────────────────────────────────────────────────

@app.post("/tasks/add")
async def add_task(
    account_id:    str           = Form(...),
    product_url:   str           = Form(...),
    schedule_type: str           = Form("daily"),
    run_time:      str           = Form("09:00"),
    start_time:    str           = Form(""),
    end_time:      str           = Form(""),
    timezone:      str           = Form(""),
    days:          Optional[str] = Form(None),
    quantity:      int           = Form(1),
):
    config = load_config()
    task = {
        "id":            f"task_{uuid.uuid4().hex[:8]}",
        "account_id":    account_id,
        "product_url":   product_url,
        "schedule_type": schedule_type,
        "run_time":      "" if is_window_schedule(schedule_type) else run_time,
        "quantity":      quantity,
        "enabled":       True,
        "created":       datetime.now().isoformat(),
        "last_run":      None,
    }
    if schedule_type in {"weekly", "weekly_window"}:
        task["days"] = parse_days(days)
    if is_window_schedule(schedule_type):
        task["start_time"] = start_time
        task["end_time"] = end_time
        if timezone.strip():
            task["timezone"] = timezone.strip()
        task["last_run_window"] = None

    try:
        config["tasks"].append(normalize_task(task))
    except ValueError as exc:
        return redirect("tasks", f"Invalid task: {exc}")
    save_config(config)
    return redirect("tasks", "Task added")


@app.post("/tasks/edit")
async def edit_task(
    task_id:       str           = Form(...),
    account_id:    str           = Form(...),
    product_url:   str           = Form(...),
    schedule_type: str           = Form("daily"),
    run_time:      str           = Form("09:00"),
    start_time:    str           = Form(""),
    end_time:      str           = Form(""),
    timezone:      str           = Form(""),
    days:          Optional[str] = Form(None),
    quantity:      int           = Form(1),
):
    config = load_config()
    for index, task in enumerate(config["tasks"]):
        if task["id"] == task_id:
            updated = {
                **task,
                "account_id":    account_id,
                "product_url":   product_url,
                "schedule_type": schedule_type,
                "run_time":      "" if is_window_schedule(schedule_type) else run_time,
                "quantity":      quantity,
            }
            updated.pop("days", None)
            updated.pop("start_time", None)
            updated.pop("end_time", None)
            updated.pop("timezone", None)
            updated.pop("last_run_window", None)

            if schedule_type in {"weekly", "weekly_window"}:
                updated["days"] = parse_days(days)
            if is_window_schedule(schedule_type):
                updated["start_time"] = start_time
                updated["end_time"] = end_time
                if timezone.strip():
                    updated["timezone"] = timezone.strip()
                updated["last_run_window"] = task.get("last_run_window")

            try:
                config["tasks"][index] = normalize_task(updated)
            except ValueError as exc:
                return redirect("tasks", f"Invalid task: {exc}")
            break
    save_config(config)
    return redirect("tasks", "Task updated")


@app.post("/tasks/toggle")
async def toggle_task(task_id: str = Form(...)):
    config = load_config()
    for task in config["tasks"]:
        if task["id"] == task_id:
            task["enabled"] = not task.get("enabled", True)
            break
    save_config(config)
    return redirect("tasks")


@app.post("/tasks/delete")
async def delete_task(task_id: str = Form(...)):
    config = load_config()
    config["tasks"] = [t for t in config["tasks"] if t["id"] != task_id]
    save_config(config)
    return redirect("tasks")


# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Only open browser locally, not on cloud deployment
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") is not None
    if not is_railway:
        webbrowser.open("http://localhost:8100")
    
    # On Railway, bind to 0.0.0.0; locally, bind to 127.0.0.1
    host = "0.0.0.0" if is_railway else "127.0.0.1"
    port = int(os.environ.get("PORT", 8100))
    uvicorn.run("server:app", host=host, port=port, reload=False)
