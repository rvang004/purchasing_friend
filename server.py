"""
Web UI server for Purchase Bot.
Run with: python server.py
Then open: http://localhost:8100
"""

import json
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

from utils import CredentialManager

app = FastAPI(title="Purchase Bot UI")
templates = Jinja2Templates(directory="templates")
cred_manager = CredentialManager()
CONFIG_FILE = Path("config.json")


# ── helpers ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"tasks": []}


def save_config(config: dict):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def load_accounts() -> dict:
    return cred_manager.load_credentials()


def save_accounts(accounts: dict):
    cred_manager.save_credentials(accounts)


def redirect(tab: str = "accounts"):
    return RedirectResponse(url=f"/?tab={tab}", status_code=303)


# ── pages ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, tab: str = "accounts", msg: str = ""):
    return templates.TemplateResponse("ui.html", {
        "request":  request,
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
    days:          Optional[str] = Form(None),
    quantity:      int           = Form(1),
):
    config = load_config()
    task = {
        "id":            f"task_{uuid.uuid4().hex[:8]}",
        "account_id":    account_id,
        "product_url":   product_url,
        "schedule_type": schedule_type,
        "run_time":      run_time,
        "quantity":      quantity,
        "enabled":       True,
        "created":       datetime.now().isoformat(),
        "last_run":      None,
    }
    if schedule_type == "weekly" and days:
        task["days"] = [d.strip() for d in days.split(",") if d.strip()]
    config["tasks"].append(task)
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
    webbrowser.open("http://localhost:8100")
    uvicorn.run("server:app", host="0.0.0.0", port=8100, reload=True)
