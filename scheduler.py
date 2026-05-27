import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from crypto_utils import decrypt_password
from automation import walmart, sams, target

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "tasks_config.json"


class PurchaseScheduler:

    # -------------------------------
    # Load/save config
    # -------------------------------
    def load_config(self):
        if not CONFIG_PATH.exists():
            return {"tasks": []}
        return json.loads(CONFIG_PATH.read_text())

    def save_config(self, config):
        CONFIG_PATH.write_text(json.dumps(config, indent=2))

    # -------------------------------
    # Time check
    # -------------------------------
    def check_if_should_run(self, task, now_local):
        if not task.get("enabled", True):
            return False

        sched = task["schedule"]
        hour = sched["hour"]
        minute = sched["minute"]
        second = sched["second"]
        ampm = sched["ampm"]

        # Convert AM/PM to 24h
        if ampm == "PM" and hour != 12:
            hour += 12
        if ampm == "AM" and hour == 12:
            hour = 0

        # Compare time
        if not (now_local.hour == hour and now_local.minute == minute):
            return False

        # Prevent double-run
        last = task.get("last_run")
        if last:
            last_dt = datetime.fromisoformat(last)
            if last_dt.year == now_local.year and last_dt.month == now_local.month and \
               last_dt.day == now_local.day and last_dt.hour == now_local.hour and \
               last_dt.minute == now_local.minute:
                return False

        return True

    # -------------------------------
    # Main scheduler loop
    # -------------------------------
    async def run_scheduler(self, interval=60, dry_run=False):
        logger.info("Scheduler started")

        while True:
            config = self.load_config()
            tasks = config["tasks"]

            for task in tasks:
                tz = ZoneInfo(self._tz_to_zone(task["schedule"]["timezone"]))
                now_local = datetime.now(tz)

                if self.check_if_should_run(task, now_local):
                    asyncio.create_task(self.run_task(task, config, dry_run))

            await asyncio.sleep(interval)

    # -------------------------------
    # Convert CST → America/Chicago
    # -------------------------------
    def _tz_to_zone(self, tz):
        mapping = {
            "CST": "America/Chicago",
            "EST": "America/New_York",
            "PST": "America/Los_Angeles",
            "MST": "America/Denver"
        }
        return mapping.get(tz, "America/Chicago")

    # -------------------------------
    # Execute a task
    # -------------------------------
    async def run_task(self, task, config, dry_run):
        retailer = task["retailer"]
        limits = task["limits"]

        # Decrypt password
        password = decrypt_password(task["account"]["password_encrypted"])

        # Route to retailer automation
        if retailer == "walmart":
            result = await walmart.run(task, password, dry_run)
        elif retailer == "sams":
            result = await sams.run(task, password, dry_run)
        elif retailer == "target":
            result = await target.run(task, password, dry_run)
        else:
            logger.error(f"Unknown retailer: {retailer}")
            return

        # Update last_run
        for t in config["tasks"]:
            if t["id"] == task["id"]:
                t["last_run"] = datetime.now().isoformat()

        self.save_config(config)
