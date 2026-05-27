import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PurchaseScheduler:
    """
    Scheduler class that manages timed purchase tasks.
    """

    def load_config(self):
        """
        Load your config file here.
        Replace this placeholder with your real implementation.
        """
        raise NotImplementedError("load_config() must be implemented")

    def save_config(self, config):
        """
        Save updated config here.
        Replace this placeholder with your real implementation.
        """
        raise NotImplementedError("save_config() must be implemented")

    def check_if_should_run(self, task, current_time):
        """
        Determine if a task should run at the current time.
        Replace this placeholder with your real implementation.
        """
        raise NotImplementedError("check_if_should_run() must be implemented")

    async def execute_task(self, task, dry_run=False):
        """
        Execute a single task.
        Replace this placeholder with your real implementation.
        """
        raise NotImplementedError("execute_task() must be implemented")

    # ---------------------------------------------------------
    # YOUR METHOD — inserted exactly as you provided it
    # ---------------------------------------------------------
    async def run_scheduler(self, interval: int = 60, dry_run: bool = False, stop_event=None):
        """
        Main scheduler loop with clean stop support.

        Args:
            interval: Check interval in seconds
            dry_run: If True, simulate purchases without completing them
            stop_event: asyncio.Event() used to request a clean stop
        """
        logger.info("🤖 Purchase scheduler started")

        try:
            while True:

                # ---- STOP CHECK ----
                if stop_event and stop_event.is_set():
                    logger.info("🛑 Stop requested — exiting scheduler loop")
                    break

                config = self.load_config()
                current_time = datetime.now()

                logger.info(f"⏰ Checking tasks at {current_time.strftime('%H:%M:%S')}")

                tasks_to_run = [
                    t for t in config["tasks"]
                    if self.check_if_should_run(t, current_time)
                ]

                if tasks_to_run:
                    logger.info(f"🎯 Found {len(tasks_to_run)} task(s) to execute")

                    # Run tasks concurrently
                    results = await asyncio.gather(*[
                        self.execute_task(task, dry_run=dry_run)
                        for task in tasks_to_run
                    ])

                    # Update config with last_run times
                    for task in tasks_to_run:
                        for config_task in config["tasks"]:
                            if config_task["id"] == task["id"]:
                                config_task["last_run"] = task.get("last_run")

                    self.save_config(config)
                    logger.info(
                        f"📊 Execution complete: "
                        f"{sum(1 for r in results if r['success'])}/{len(results)} successful"
                    )

                # ---- RESPONSIVE SLEEP ----
                for _ in range(interval):
                    if stop_event and stop_event.is_set():
                        logger.info("🛑 Stop requested during sleep — exiting scheduler loop")
                        return
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            raise
