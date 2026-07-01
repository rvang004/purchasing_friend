"""Append-only purchase audit/history storage.

JSONL is intentionally boring here: each line is one immutable event. Easy to
inspect, easy to test, and hard to corrupt wholesale. Boring wins trophies.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from models import PurchaseResult


class PurchaseHistory:
    """Records purchase attempts and policy decisions as JSONL events."""

    def __init__(self, history_file: str = "purchase_history.jsonl"):
        self.history_file = Path(history_file)

    def record_result(self, result: PurchaseResult) -> dict[str, Any]:
        """Record a normalized purchase result."""
        event = {
            "event_type": "purchase_result",
            "recorded_at": datetime.now().isoformat(),
            **result.to_dict(),
        }
        self._append(event)
        return event

    def record_policy_block(
        self,
        *,
        task_id: str,
        account_id: str | None,
        reason: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Record a task blocked before/after browser execution."""
        event = {
            "event_type": "policy_block",
            "recorded_at": datetime.now().isoformat(),
            "task_id": task_id,
            "account_id": account_id,
            "success": False,
            "error": reason,
            "dry_run": dry_run,
        }
        self._append(event)
        return event

    def read_events(self) -> list[dict[str, Any]]:
        """Read all history events. Intended for tests and small local reports."""
        if not self.history_file.exists():
            return []
        events = []
        for line in self.history_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
        return events

    def _append(self, event: dict[str, Any]) -> None:
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with self.history_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
