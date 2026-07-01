"""
Encryption utilities for safe credential storage.
Uses Fernet (symmetric encryption) from cryptography library.
"""

import json
import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from getpass import getpass

from app_paths import CREDENTIALS_FILE, MASTER_KEY_FILE, ensure_parent


class CredentialManager:
    """Handles secure encryption/decryption of account credentials."""
    
    def __init__(self, cred_file: str | Path = CREDENTIALS_FILE, key_file: str | Path = MASTER_KEY_FILE):
        self.cred_file = Path(cred_file)
        self.key_file = Path(key_file)
        self.cipher = None
        self._load_or_create_key()
    
    def _load_or_create_key(self):
        """Load key from env var, file, or create new one."""
        # Try environment variable first (for Railway/cloud deployment)
        env_key = os.environ.get('MASTER_KEY')
        if env_key:
            try:
                key = base64.b64decode(env_key)
                self.cipher = Fernet(key)
                return
            except Exception as e:
                print(f"[ERROR] Invalid MASTER_KEY env var: {e}")
                raise
        
        # Fall back to file-based key (for local development)
        if self.key_file.exists():
            with self.key_file.open("rb") as f:
                key = f.read()
        else:
            ensure_parent(self.key_file)
            key = Fernet.generate_key()
            with self.key_file.open("wb") as f:
                f.write(key)
            print(f"[OK] Master key created: {self.key_file}")
            print("[WARN] KEEP THIS FILE SAFE! Add to .gitignore (already done).\n")
        
        self.cipher = Fernet(key)
    
    def save_credentials(self, accounts: dict) -> bool:
        """Encrypt and save accounts to file."""
        try:
            json_data = json.dumps(accounts, indent=2)
            encrypted = self.cipher.encrypt(json_data.encode())
            
            ensure_parent(self.cred_file)
            with self.cred_file.open("wb") as f:
                f.write(encrypted)
            
            return True
        except Exception as e:
            print(f"[ERROR] Error saving credentials: {e}")
            return False
    
    def load_credentials(self) -> dict:
        """Decrypt and load accounts from file or env var."""
        # Try environment variable first (for Railway/cloud deployment)
        env_creds = os.environ.get('CREDENTIALS_ENC')
        if env_creds:
            try:
                encrypted = base64.b64decode(env_creds)
                decrypted = self.cipher.decrypt(encrypted).decode()
                return json.loads(decrypted)
            except Exception as e:
                print(f"[ERROR] Failed to load CREDENTIALS_ENC from env: {e}")
                return {}
        
        # Fall back to file-based (for local development)
        if not self.cred_file.exists():
            return {}
        
        try:
            with self.cred_file.open("rb") as f:
                encrypted = f.read()
            
            decrypted = self.cipher.decrypt(encrypted).decode()
            return json.loads(decrypted)
        except Exception as e:
            print(f"[ERROR] Error loading credentials: {e}")
            return {}
    
    def add_account(self, accounts: dict, account_id: str, site: str,
                    email: str, password: str, payment_method: str,
                    monthly_limit: float, price_limit_per_item: float,
                    price_limit_enabled: bool = True,
                    quantity_limit_per_item: int = None,
                    shipping_address: dict = None) -> dict:
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
            "shipping_address": shipping_address,
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
