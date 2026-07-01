"""
Interactive CLI for setting up accounts and purchase tasks.
"""

import json
from pathlib import Path
from utils import CredentialManager
from datetime import datetime
from app_paths import CONFIG_FILE, ensure_parent


class SetupWizard:
    """Interactive configuration wizard."""
    
    def __init__(self):
        self.cred_manager = CredentialManager()
        self.accounts = self.cred_manager.load_credentials()
        self.config_file = CONFIG_FILE
    
    def load_config(self) -> dict:
        """Load purchase tasks config."""
        if Path(self.config_file).exists():
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {"tasks": []}
    
    def save_config(self, config: dict):
        """Save purchase tasks config."""
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
        print(f"[OK] Config saved to {self.config_file}")
    
    def show_menu(self):
        """Display main menu."""
        print("\n" + "="*50)
        print("[PURCHASE BOT SETUP WIZARD]")
        print("="*50)
        print("1. Add new account")
        print("2. View accounts")
        print("3. Add purchase task")
        print("4. View purchase tasks")
        print("5. Delete account")
        print("6. Delete purchase task")
        print("7. Toggle price limit on/off")
        print("8. Exit")
        print("="*50)
    
    def _prompt_shipping_address(self) -> dict | None:
        """Optionally collect a shipping address to use at checkout."""
        print("\nShipping Address:")
        print("  Leave blank to use the default address already saved on the site.")
        use_default = input("  Use site's default address? (yes/no, default yes): ").lower().strip()
        if use_default != "no":
            print("[OK] Will use the site's saved default address at checkout")
            return None

        print("  Enter the shipping address to use:")
        address = {
            "full_name": input("    Full name: ").strip(),
            "line1":     input("    Address line 1: ").strip(),
            "line2":     input("    Address line 2 (optional): ").strip() or "",
            "city":      input("    City: ").strip(),
            "state":     input("    State/Province: ").strip(),
            "zip_code":  input("    ZIP / Postal code: ").strip(),
            "country":   input("    Country (default US): ").strip() or "US",
        }
        return address

    def add_account(self):
        """Interactively add a new account."""
        print("\n[ADD NEW ACCOUNT]")
        
        account_id = input("Account ID (e.g., 'amazon_main'): ").strip()
        if not account_id:
            print("[ERROR] Account ID cannot be empty")
            return
        
        if account_id in self.accounts:
            print(f"[ERROR] Account '{account_id}' already exists")
            return
        
        site = input("Website URL (e.g., 'https://www.amazon.com'): ").strip()
        email = input("Email/Username: ").strip()
        password = input("Password: ")
        
        print("\nPayment Method Options:")
        print("1. Credit Card")
        print("2. Debit Card")
        print("3. Digital Wallet (PayPal, Apple Pay, etc.)")
        print("4. Store Credit")
        payment_choice = input("Select (1-4): ").strip()
        
        payment_map = {
            "1": "credit_card",
            "2": "debit_card",
            "3": "digital_wallet",
            "4": "store_credit"
        }
        payment_method = payment_map.get(payment_choice, "credit_card")
        
        try:
            monthly_limit = float(input("Monthly spending limit ($): "))
        except ValueError:
            monthly_limit = 1000.0
            print(f"[WARN] Using default monthly limit: ${monthly_limit}")
        
        try:
            price_limit = float(input("Max price per item/quantity ($): "))
        except ValueError:
            price_limit = 500.0
            print(f"[WARN] Using default price per item: ${price_limit}")
        
        enable_limit = input("Enable price limit? (yes/no, default yes): ").lower().strip()
        price_limit_enabled = enable_limit != "no"

        qty_input = input("Max quantity per purchase (leave blank for no limit): ").strip()
        try:
            quantity_limit = int(qty_input) if qty_input else None
        except ValueError:
            quantity_limit = None
            print("[WARN] Invalid quantity — no quantity limit set")

        shipping_address = self._prompt_shipping_address()

        self.accounts = self.cred_manager.add_account(
            self.accounts,
            account_id,
            site,
            email,
            password,
            payment_method,
            monthly_limit,
            price_limit,
            price_limit_enabled,
            quantity_limit,
            shipping_address,
        )
        
        if self.cred_manager.save_credentials(self.accounts):
            print(f"[OK] Account '{account_id}' added successfully!")
        else:
            print("[ERROR] Failed to save account")
    
    def view_accounts(self):
        """Display all accounts (masked)."""
        if not self.accounts:
            print("\n[ERROR] No accounts found")
            return
        
        print("\n[YOUR ACCOUNTS]")
        print("-" * 60)
        
        for account_id, account in self.accounts.items():
            email_masked = account["email"][:3] + "***@***"
            monthly_limit = account["monthly_limit"]
            price_limit = account.get("price_limit_per_item", "N/A")
            price_enabled = account.get("price_limit_enabled", True)
            spent = account.get("spent_this_month", 0)
            
            limit_status = "[ON]" if price_enabled else "[OFF]"
            
            print(f"\n[ACCOUNT] {account_id}")
            print(f"   Site: {account['site']}")
            print(f"   Email: {email_masked}")
            print(f"   Payment: {account['payment_method']}")
            qty_limit = account.get("quantity_limit_per_item")
            qty_display = f"{qty_limit} units" if qty_limit is not None else "No limit"
            addr = account.get("shipping_address")
            addr_display = f"{addr['line1']}, {addr['city']} {addr['state']}" if addr else "Site default"

            print(f"   Monthly Limit: ${monthly_limit} (Spent: ${spent:.2f})")
            print(f"   Price Per Item: ${price_limit} {limit_status}")
            print(f"   Qty Per Purchase: {qty_display}")
            print(f"   Ship To: {addr_display}")
    
    def _prompt_window(self) -> tuple[str, str, str | None]:
        """Collect a schedule window from the user."""
        start_time = input("Start time (e.g., 20:00 or 8:00 PM): ").strip()
        end_time = input("End time (e.g., 22:00 or 10:00 PM): ").strip()
        timezone = input("Timezone (optional, e.g., CST or America/Chicago): ").strip() or None
        return start_time, end_time, timezone

    def add_purchase_task(self):
        """Add a new purchase task."""
        print("\n[ADD PURCHASE TASK]")
        
        if not self.accounts:
            print("[ERROR] No accounts found. Please add an account first.")
            return
        
        self.view_accounts()
        account_id = input("\nSelect account ID: ").strip()
        
        if account_id not in self.accounts:
            print("[ERROR] Account not found")
            return
        
        product_url = input("Product URL: ").strip()
        
        print("\nSchedule Options:")
        print("1. Run once at/after a specific time")
        print("2. Run daily at a specific time")
        print("3. Run weekly on specific days/time")
        print("4. Run once within a timeframe")
        print("5. Run daily within a timeframe")
        print("6. Run weekly within a timeframe")
        schedule_choice = input("Select (1-6): ").strip()
        days = ""
        timezone = None
        start_time = None
        end_time = None

        if schedule_choice == "1":
            run_time = input("Time (e.g., 14:30 or 2:30 PM): ").strip()
            schedule_type = "once"
        elif schedule_choice == "2":
            run_time = input("Time (e.g., 14:30 or 2:30 PM): ").strip()
            schedule_type = "daily"
        elif schedule_choice == "3":
            run_time = input("Time (e.g., 14:30 or 2:30 PM): ").strip()
            days = input("Days (e.g., 'Mon,Wed,Fri'): ").strip()
            schedule_type = "weekly"
        elif schedule_choice == "4":
            run_time = ""
            start_time, end_time, timezone = self._prompt_window()
            schedule_type = "once_window"
        elif schedule_choice == "5":
            run_time = ""
            start_time, end_time, timezone = self._prompt_window()
            schedule_type = "daily_window"
        elif schedule_choice == "6":
            run_time = ""
            start_time, end_time, timezone = self._prompt_window()
            days = input("Days (e.g., 'Mon,Wed,Fri'): ").strip()
            schedule_type = "weekly_window"
        else:
            print("[ERROR] Invalid choice")
            return
        
        try:
            quantity = int(input("Quantity: ") or "1")
        except ValueError:
            quantity = 1
        
        config = self.load_config()
        
        task = {
            "id": f"task_{len(config['tasks']) + 1}",
            "account_id": account_id,
            "product_url": product_url,
            "schedule_type": schedule_type,
            "run_time": run_time,
            "quantity": quantity,
            "enabled": True,
            "created": datetime.now().isoformat(),
            "last_run": None
        }
        
        if schedule_choice in {"3", "6"}:
            task["days"] = days.split(",")
        if start_time and end_time:
            task["start_time"] = start_time
            task["end_time"] = end_time
        if timezone:
            task["timezone"] = timezone

        config["tasks"].append(task)
        self.save_config(config)
        print(f"[OK] Purchase task '{task['id']}' added!")
    
    def view_tasks(self):
        """Display all purchase tasks."""
        config = self.load_config()
        
        if not config["tasks"]:
            print("\n[ERROR] No purchase tasks found")
            return
        
        print("\n[PURCHASE TASKS]")
        print("-" * 60)
        
        for task in config["tasks"]:
            status = "[ENABLED]" if task["enabled"] else "[DISABLED]"
            print(f"\n[TASK] {task['id']}")
            print(f"   Account: {task['account_id']}")
            print(f"   Product: {task['product_url'][:50]}...")
            if task.get("start_time") and task.get("end_time"):
                tz = f" {task.get('timezone')}" if task.get("timezone") else ""
                schedule = f"{task['schedule_type']} {task['start_time']}–{task['end_time']}{tz}"
            else:
                schedule = f"{task['schedule_type']} @ {task['run_time']}"
            print(f"   Schedule: {schedule}")
            print(f"   Quantity: {task['quantity']}")
            print(f"   Status: {status}")
            print(f"   Last Run: {task['last_run'] or 'Never'}")
    
    def delete_account(self):
        """Delete an account."""
        self.view_accounts()
        account_id = input("\nEnter account ID to delete: ").strip()
        
        if account_id not in self.accounts:
            print("[ERROR] Account not found")
            return
        
        confirm = input(f"[WARN] Delete '{account_id}'? (yes/no): ").lower()
        if confirm == "yes":
            del self.accounts[account_id]
            if self.cred_manager.save_credentials(self.accounts):
                print(f"[OK] Account '{account_id}' deleted")
    
    def delete_task(self):
        """Delete a purchase task."""
        self.view_tasks()
        config = self.load_config()
        
        task_id = input("\nEnter task ID to delete: ").strip()
        
        original_len = len(config["tasks"])
        config["tasks"] = [t for t in config["tasks"] if t["id"] != task_id]
        
        if len(config["tasks"]) < original_len:
            self.save_config(config)
            print(f"[OK] Task '{task_id}' deleted")
        else:
            print("[ERROR] Task not found")
    
    def toggle_price_limit(self):
        """Toggle price limit on/off for an account."""
        self.view_accounts()
        
        if not self.accounts:
            print("\n[ERROR] No accounts found")
            return
        
        account_id = input("\nEnter account ID to toggle: ").strip()
        
        if account_id not in self.accounts:
            print("❌ Account not found")
            return
        
        current_state = self.accounts[account_id].get("price_limit_enabled", True)
        new_state = not current_state
        self.accounts[account_id]["price_limit_enabled"] = new_state
        
        if self.cred_manager.save_credentials(self.accounts):
            status = "[ENABLED]" if new_state else "[DISABLED]"
            print(f"[OK] Price limit {status} for {account_id}")
        else:
            print("[ERROR] Failed to update account")
    
    def run(self):
        """Main wizard loop."""
        while True:
            self.show_menu()
            choice = input("Select an option (1-8): ").strip()
            
            if choice == "1":
                self.add_account()
            elif choice == "2":
                self.view_accounts()
            elif choice == "3":
                self.add_purchase_task()
            elif choice == "4":
                self.view_tasks()
            elif choice == "5":
                self.delete_account()
            elif choice == "6":
                self.delete_task()
            elif choice == "7":
                self.toggle_price_limit()
            elif choice == "8":
                print("\n[OK] Goodbye!")
                break
            else:
                print("[ERROR] Invalid option")


if __name__ == "__main__":
    wizard = SetupWizard()
    wizard.run()
