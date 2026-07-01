"""
Task scheduler for running purchases at specified times.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any

from models import Account, PurchaseResult, PurchaseTask, is_window_schedule, parse_time_string
from purchase_engine import run_purchase
from purchase_history import PurchaseHistory
from purchase_policy import spend_amount, validate_purchase_result, validate_task_for_account
from utils import CredentialManager
from app_paths import CONFIG_FILE, CREDENTIALS_FILE, HISTORY_FILE
from app_paths import CONFIG_FILE, HISTORY_FILE, LOG_FILE, ensure_parent

ensure_parent(LOG_FILE)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE)),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class PurchaseScheduler:
    """Manages scheduled purchase execution."""

    def __init__(
        self,
        config_file: str | Path = CONFIG_FILE,
        cred_file: str | Path = CREDENTIALS_FILE,
        history_file: str | Path = HISTORY_FILE,
        *,
        cred_manager: CredentialManager | None = None,
        accounts: dict[str, dict[str, Any]] | None = None,
        history: PurchaseHistory | None = None,
    ):
        self.config_file = Path(config_file)
        self.cred_manager = cred_manager or CredentialManager(cred_file=cred_file)
        self.accounts = accounts if accounts is not None else self.cred_manager.load_credentials()
        self.history = history or PurchaseHistory(str(history_file))

    def load_config(self) -> dict[str, Any]:
        """Load purchase tasks config."""
        if not Path(self.config_file).exists():
            logger.error("Config file not found: %s", self.config_file)
            return {"tasks": []}

        with open(self.config_file, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def save_config(self, config: dict[str, Any]) -> None:
        """Save updated config."""
        with open(self.config_file, "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)

    def validate_task(self, raw_task: dict[str, Any]) -> PurchaseTask | None:
        """Validate a raw config task, logging bad configs without crashing."""
        try:
            return PurchaseTask.from_dict(raw_task)
        except ValueError as exc:
            task_id = str(raw_task.get("id", "unknown"))
            account_id = raw_task.get("account_id")
            logger.error("Invalid task %s: %s", task_id, exc)
            self.history.record_policy_block(
                task_id=task_id,
                account_id=account_id,
                reason=f"Invalid task: {exc}",
            )
            return None

    def check_if_should_run(self, raw_task: dict[str, Any], current_time: datetime) -> bool:
        """Check if a task should run at the current time."""
        task = self.validate_task(raw_task)
        if task is None or not task.enabled:
            return False

        task_now = self._time_for_task(current_time, task)
        current_date = task_now.date()

        if is_window_schedule(task.schedule_type):
            return self._window_should_run(task, raw_task, task_now)

        task_time = parse_time_string(task.run_time)
        if task.schedule_type == "once":
            return task_now.time() >= task_time and task.last_run is None

        if task.schedule_type == "daily":
            time_matches = task_now.hour == task_time.hour and task_now.minute == task_time.minute
            return time_matches and task.last_run_date != current_date

        if task.schedule_type == "weekly":
            weekday_matches = task_now.strftime("%a") in task.days
            time_matches = task_now.hour == task_time.hour and task_now.minute == task_time.minute
            return weekday_matches and time_matches and task.last_run_date != current_date

        return False

    def _time_for_task(self, current_time: datetime, task: PurchaseTask) -> datetime:
        """Return current time in the task timezone when configured."""
        if not task.timezone:
            return current_time
        zone = ZoneInfo(task.timezone)
        if current_time.tzinfo is None:
            return current_time.replace(tzinfo=zone)
        return current_time.astimezone(zone)

    def _window_should_run(
        self,
        task: PurchaseTask,
        raw_task: dict[str, Any],
        task_now: datetime,
    ) -> bool:
        """Return True once per configured start/end window."""
        start = parse_time_string(task.start_time)
        end = parse_time_string(task.end_time)
        current = task_now.time().replace(second=0, microsecond=0)
        crosses_midnight = start > end

        if crosses_midnight:
            in_window = current >= start or current <= end
            anchor_date = task_now.date() - timedelta(days=1) if current <= end else task_now.date()
        else:
            in_window = start <= current <= end
            anchor_date = task_now.date()

        if not in_window:
            return False

        if task.schedule_type == "weekly_window" and anchor_date.strftime("%a") not in task.days:
            return False
        if task.schedule_type == "once_window" and task.last_run is not None:
            return False

        last_window = raw_task.get("last_run_window") or task.last_run_window
        if not last_window and task.last_run_date == anchor_date:
            last_window = anchor_date.isoformat()
        return last_window != anchor_date.isoformat()

    def _window_key_for_task(self, task: PurchaseTask, current_time: datetime) -> str | None:
        """Return YYYY-MM-DD key for the active schedule window, if any."""
        if not is_window_schedule(task.schedule_type):
            return None
        task_now = self._time_for_task(current_time, task)
        start = parse_time_string(task.start_time)
        end = parse_time_string(task.end_time)
        current = task_now.time().replace(second=0, microsecond=0)
        if start > end and current <= end:
            return (task_now.date() - timedelta(days=1)).isoformat()
        return task_now.date().isoformat()

    async def execute_task(
        self,
        raw_task: dict[str, Any],
        dry_run: bool = False,
        mode: str | None = None,
    ) -> dict[str, Any]:
        """Execute a single purchase task with validation, policy, and audit."""
        run_mode = self._resolve_mode(mode, dry_run)
        audit_dry_run = run_mode != "live"
        task = self.validate_task(raw_task)
        if task is None:
            return {"success": False, "error": "Invalid task"}

        account_data = self.accounts.get(task.account_id)
        account = self._load_account(task.account_id, account_data)
        decision = validate_task_for_account(task, account)
        if not decision.allowed:
            logger.warning("Task %s blocked: %s", task.id, decision.reason)
            self.history.record_policy_block(
                task_id=task.id,
                account_id=task.account_id,
                reason=decision.reason,
                dry_run=audit_dry_run,
            )
            return {"success": False, "error": decision.reason}

        logger.info("Starting purchase for task %s using account %s", task.id, task.account_id)
        engine_account = dict(account_data or {})
        engine_account["id"] = task.account_id

        raw_result = await run_purchase(
            engine_account,
            task.product_url,
            quantity=task.quantity,
            dry_run=run_mode == "dry-run",
            mode=run_mode,
        )
        result = PurchaseResult.from_engine_result(
            task,
            task.account_id,
            raw_result,
            dry_run=audit_dry_run,
        )

        post_decision = validate_purchase_result(account, result)
        if not post_decision.allowed:
            logger.error("Purchase blocked/failed for %s: %s", task.id, post_decision.reason)
            self.history.record_policy_block(
                task_id=task.id,
                account_id=task.account_id,
                reason=post_decision.reason,
                dry_run=audit_dry_run,
            )
            if result.success:
                raw_result = {**raw_result, "success": False, "error": post_decision.reason}
                result = PurchaseResult.from_engine_result(
                    task,
                    task.account_id,
                    raw_result,
                    dry_run=audit_dry_run,
                )
        else:
            logger.info("Purchase policy passed for task %s", task.id)

        self.history.record_result(result)

        if result.success:
            logger.info("Purchase successful: %s", task.id)
            completed_at = datetime.now().astimezone()
            raw_task["last_run"] = completed_at.isoformat()
            window_key = self._window_key_for_task(task, completed_at)
            if window_key:
                raw_task["last_run_window"] = window_key
            self._update_monthly_spend(task.account_id, result)
        else:
            logger.error("Purchase failed: %s", result.error)

        return result.to_dict()

    async def run_once(self, dry_run: bool = False, mode: str | None = None) -> None:
        """
        Single check cycle — loads tasks, runs whatever is due, then exits.
        Used by GitHub Actions so the workflow doesn't run forever.
        """
        config = self.load_config()
        current_time = datetime.now().astimezone()

        logger.info("One-shot check at %s", current_time.strftime("%H:%M:%S %Z"))
        await self._execute_due_tasks(config, current_time, dry_run=dry_run, mode=mode)

    async def run_scheduler(
        self,
        interval: int = 60,
        dry_run: bool = False,
        mode: str | None = None,
    ) -> None:
        """
        Main scheduler loop.

        Args:
            interval: Check interval in seconds
            dry_run: If True, simulate purchases without completing them
        """
        logger.info("Purchase scheduler started")

        try:
            while True:
                config = self.load_config()
                current_time = datetime.now().astimezone()

                logger.info("Checking tasks at %s", current_time.strftime("%H:%M:%S %Z"))
                await self._execute_due_tasks(config, current_time, dry_run=dry_run, mode=mode)
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as exc:
            logger.error("Scheduler error: %s", exc)
            raise

    async def _execute_due_tasks(
        self,
        config: dict[str, Any],
        current_time: datetime,
        *,
        dry_run: bool,
        mode: str | None = None,
    ) -> None:
        run_mode = self._resolve_mode(mode, dry_run)
        tasks_to_run = [
            task for task in config.get("tasks", [])
            if self.check_if_should_run(task, current_time)
        ]

        if not tasks_to_run:
            logger.info("No tasks due right now")
            return

        logger.info("Found %s task(s) to execute", len(tasks_to_run))

        # Sequential execution avoids same-account spend races. Boring? Yes.
        # Accidentally overspending through concurrency? No thanks.
        results = []
        for task in tasks_to_run:
            results.append(await self.execute_task(task, dry_run=dry_run, mode=run_mode))

        self.save_config(config)
        success_count = sum(1 for result in results if result.get("success"))
        logger.info("Execution complete: %s/%s successful", success_count, len(results))

    @staticmethod
    def _resolve_mode(mode: str | None, dry_run: bool) -> str:
        if dry_run:
            return "dry-run"
        return mode or "live"

    def _load_account(self, account_id: str, account_data: dict[str, Any] | None) -> Account | None:
        if account_data is None:
            logger.error("Account '%s' not found", account_id)
            return None
        try:
            return Account.from_dict(account_id, account_data)
        except ValueError as exc:
            logger.error("Invalid account %s: %s", account_id, exc)
            return None

    def _update_monthly_spend(self, account_id: str, result: PurchaseResult) -> None:
        amount = spend_amount(result)
        if amount <= 0:
            return

        account_data = self.accounts.get(account_id)
        if account_data is None:
            return

        current_spend = Account.from_dict(account_id, account_data).spent_this_month
        new_spend = current_spend + amount
        account_data["spent_this_month"] = float(new_spend)

        if self.cred_manager.save_credentials(self.accounts):
            logger.info("Updated monthly spend for %s: $%s", account_id, new_spend)
        else:
            logger.error("Failed to save updated spend for %s", account_id)


async def main() -> None:
    """CLI entry point for scheduler."""
    parser = argparse.ArgumentParser(description="Purchase Bot Scheduler")
    parser.add_argument("--dry-run", action="store_true", help="Alias for --mode dry-run")
    parser.add_argument("--mode", choices=["dry-run", "review", "live"], default="review")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    args = parser.parse_args()

    scheduler = PurchaseScheduler()
    await scheduler.run_scheduler(interval=args.interval, dry_run=args.dry_run, mode=args.mode)


if __name__ == "__main__":
    asyncio.run(main())
