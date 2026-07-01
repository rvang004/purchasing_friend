"""Filesystem locations for Purchase Bot runtime data.

Set PURCHASE_BOT_DATA_DIR=/data on Railway when using a persistent volume.
Individual paths can be overridden with the PURCHASE_BOT_*_FILE variables.
"""

from __future__ import annotations

import os
from pathlib import Path


def _base_dir() -> Path:
    return Path(os.getenv("PURCHASE_BOT_DATA_DIR", ".")).expanduser()


def _path(env_var: str, filename: str) -> Path:
    configured = os.getenv(env_var)
    if configured:
        return Path(configured).expanduser()
    return _base_dir() / filename


CONFIG_FILE = _path("PURCHASE_BOT_CONFIG_FILE", "config.json")
CREDENTIALS_FILE = _path("PURCHASE_BOT_CREDENTIALS_FILE", "credentials.enc")
MASTER_KEY_FILE = _path("PURCHASE_BOT_MASTER_KEY_FILE", ".master_key")
HISTORY_FILE = _path("PURCHASE_BOT_HISTORY_FILE", "purchase_history.jsonl")
LOG_FILE = _path("PURCHASE_BOT_LOG_FILE", "purchase_bot.log")
RUNS_DIR = _path("PURCHASE_BOT_RUNS_DIR", "runs")


def ensure_parent(path: Path) -> None:
    """Create the parent directory for a file path if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
