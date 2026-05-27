import json
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

from utils import CredentialManager

# ──────────────────────────────────────────────────────────────────────────────
# Setup
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI()
templates = Jinja2Templates(directory="templates")
cred_manager = CredentialManager()

CONFIG_FILE = Path("config.json")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {"accounts": [], "tasks": []}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)


# ──────────────────────────────────────────────────────────────────────────────
# Task Models (FULL UI SUPPORT)
# ──────────────────────────────────────────────────────────────────────────────

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
    last_run: Optional[datetime] = None


# ──────────────────────────────────────────────────────────────────────────────
# HTML Routes (unchanged)
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    cfg = load_config()
    return templates.TemplateResponse(
        "index.html",
        {"
