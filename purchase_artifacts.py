"""Run artifacts for browser purchase attempts."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app_paths import RUNS_DIR


class PurchaseArtifacts:
    """Captures screenshots and Playwright traces for a purchase run."""

    def __init__(self, base_dir: str | Path = RUNS_DIR, run_id: str | None = None):
        base_path = Path(base_dir)
        safe_run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.run_dir = base_path / self._safe_name(safe_run_id)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._trace_started = False

    async def start_trace(self, context: Any) -> None:
        try:
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
            self._trace_started = True
        except Exception:
            self._trace_started = False

    async def stop_trace(self, context: Any) -> str | None:
        if not self._trace_started:
            return None
        trace_path = self.run_dir / "trace.zip"
        try:
            await context.tracing.stop(path=str(trace_path))
            return str(trace_path)
        except Exception:
            return None

    async def screenshot(self, page: Any, name: str) -> str | None:
        path = self.run_dir / f"{self._safe_name(name)}.png"
        try:
            await page.screenshot(path=str(path), full_page=True)
            return str(path)
        except Exception:
            return None

    @staticmethod
    def _safe_name(value: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
        return safe or "run"
