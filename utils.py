"""
Encryption utilities for safe credential storage.
Uses Fernet (symmetric encryption) from cryptography library.
"""

import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from getpass import getpass


class CredentialManager:
    """Handles secure encryption/decryption of account credentials."""
    
    def __init__(self, cred_file: str = "credentials.enc", key_file: str = ".master_key"):
        self.cred_file = cred_file
        self.key_file = key_file
        self.cipher = None
        self._load_or_create_key()
    
    def _load_or_create_key(self):
        """Load existing key or create new one."""
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            print(f"✅ Master key created: {self.key_file}")
            print("⚠️  KEEP THIS FILE SAFE! Add to .gitignore (already done).\n")
        
        self.cipher = Fernet(key)
    
    def save_credentials(self, accounts: dict) -> bool:
        """Encrypt and save accounts to file."""
        try:
            json_data = json.dumps(accounts, indent=2)
            encrypted = self.cipher.encrypt(json_data.encode())
            
            with open(self.cred_file, "wb") as f:
                f.write(encrypted)
            
            return True
        except Exception as e:
            print(f"❌ Error saving credentials: {e}")
            return False
    
    def load_credentials(self) -> dict:
        """Decrypt and load accounts from file."""
        if not os.path.exists(self.cred_file):
            return {}
        
        try:
            with open(self.cred_file, "rb") as f:
                encrypted = f.read()
            
            decrypted = self.cipher.decrypt(encrypted).decode()
            return json.loads(decrypted)
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return {}
    
    def add_account(self, accounts: dict, account_id: str, site: str,
                    email: str, password: str, payment_method: str,
                    monthly_limit: float, price_limit_per_item: float,
                    price_limit_enabled: bool = True,
                    quantity_limit_per_item: int = None) -> dict:
        """Add a new account securely."""
        accounts[account_id] = {
            "site": site,
            "email": email,
            "password": password,
            "payment_method": payment_method,
            "monthly_limit": monthly_limit,
            "price_limit_per_item": price_limit_per_item,
            "price_limit_enabled": price_limit_enabled,
            "quantity_limit_per_item": quantity_limit_per_item,
            "spent_this_month": 0.0
        }
        return accounts
    
    def get_account(self, accounts: dict, account_id: str) -> dict:
        """Retrieve account by ID."""
        return accounts.get(account_id, {})


def setup_master_password() -> str:
    """Prompt user for master password (optional extra layer)."""
    password = getpass("Enter a master password (or press Enter to skip): ").strip()
    return password if password else None
