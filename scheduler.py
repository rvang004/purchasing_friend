"""
Task scheduler for running purchases at specified times.
"""

import json
import asyncio
import logging
from datetime import datetime, time
from pathlib import Path
from purchase_engine import run_purchase
from utils import CredentialManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('purchase_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PurchaseScheduler:
    """Manages scheduled purchase execution."""
    
    def __init__(self, config_file: str = "config.json", cred_file: str = "credentials.enc"):
        self.config_file = config_file
        self.cred_manager = CredentialManager(cred_file=cred_file)
        self.accounts = self.cred_manager.load_credentials()
    
    def load_config(self) -> dict:
        """Load purchase tasks config."""
        if not Path(self.config_file).exists():
            logger.error(f"Config file not found: {self.config_file}")
            return {"tasks": []}
        
        with open(self.config_file, "r") as f:
            return json.load(f)
    
    def save_config(self, config: dict):
        """Save updated config."""
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
    
    def check_if_should_run(self, task: dict, current_time: datetime) -> bool:
        """Check if a task should run at the current time."""
        if not task.get("enabled", True):
            return False
        
        task_time = datetime.strptime(task["run_time"], "%H:%M").time()
        
        schedule_type = task.get("schedule_type", "once")
        
        if schedule_type == "once":
            # Run once at specified time
            return current_time.time() >= task_time and (task.get("last_run") is None)
        
        elif schedule_type == "daily":
            # Run daily at specified time (within a 1-minute window)
            current_task_time = datetime.now().replace(
                hour=task_time.hour,
                minute=task_time.minute,
                second=0,
                microsecond=0
            )
            time_diff = abs((datetime.now() - current_task_time).total_seconds())
            return time_diff < 60 and task.get("last_run") != datetime.now().date().isoformat()
        
        elif schedule_type == "weekly":
            # Run on specific days
            days_str = task.get("days", [])
            day_map = {
                "Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3,
                "Fri": 4, "Sat": 5, "Sun": 6
            }
            
            valid_days = [day_map[d.strip()] for d in days_str if d.strip() in day_map]
            current_weekday = datetime.now().weekday()
            
            if current_weekday in valid_days:
                current_task_time = datetime.now().replace(
                    hour=task_time.hour,
                    minute=task_time.minute,
                    second=0,
                    microsecond=0
                )
                time_diff = abs((datetime.now() - current_task_time).total_seconds())
                return time_diff < 60 and task.get("last_run") != datetime.now().date().isoformat()
        
        return False
    
    async def execute_task(self, task: dict, dry_run: bool = False) -> dict:
        """Execute a single purchase task."""
        account_id = task["account_id"]
        
        if account_id not in self.accounts:
            logger.error(f"❌ Account '{account_id}' not found")
            return {"success": False, "error": "Account not found"}
        
        account = self.accounts[account_id]
        account["id"] = account_id  # Add ID for tracking
        
        # Check spending limit
        spent = account.get("spent_this_month", 0)
        limit = account.get("monthly_limit", float('inf'))

        if spent >= limit:
            logger.warning(f"⚠️  {account_id} has reached monthly limit (${spent:.2f}/${limit})")
            return {"success": False, "error": "Monthly limit reached"}

        # Check quantity cap
        quantity = task.get("quantity", 1)
        qty_limit = account.get("quantity_limit_per_item")
        if qty_limit is not None and quantity > qty_limit:
            logger.warning(
                f"⚠️  Task quantity ({quantity}) exceeds account limit ({qty_limit}) "
                f"for {account_id} — purchase blocked"
            )
            return {"success": False, "error": f"Quantity {quantity} exceeds limit {qty_limit}"}

        logger.info(f"🚀 Starting purchase for task {task['id']} using account {account_id}")

        result = await run_purchase(account, task["product_url"], quantity=quantity, dry_run=dry_run)
        
        if result["success"]:
            logger.info(f"✅ Purchase successful: {task['id']}")
            # Update last_run timestamp
            task["last_run"] = datetime.now().isoformat()
        else:
            logger.error(f"❌ Purchase failed: {result['error']}")
        
        return result
    
    async def run_scheduler(self, interval: int = 60, dry_run: bool = False):
        """
        Main scheduler loop.
        
        Args:
            interval: Check interval in seconds
            dry_run: If True, simulate purchases without completing them
        """
        logger.info("🤖 Purchase scheduler started")
        
        try:
            while True:
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
                    logger.info(f"📊 Execution complete: {sum(1 for r in results if r['success'])}/{len(results)} successful")
                
                await asyncio.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("👋 Scheduler stopped by user")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            raise


async def main():
    """CLI entry point for scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Purchase Bot Scheduler")
    parser.add_argument("--dry-run", action="store_true", help="Simulate purchases without completing")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    args = parser.parse_args()
    
    scheduler = PurchaseScheduler()
    await scheduler.run_scheduler(interval=args.interval, dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
