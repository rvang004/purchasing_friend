#!/usr/bin/env python3
"""
Quick secret file generation for Railway deployment.
Creates minimal .master_key, credentials.enc, and config.json
"""

import json
from pathlib import Path
from cryptography.fernet import Fernet
from utils import CredentialManager
from app_paths import CONFIG_FILE, ensure_parent

def quickstart():
    """Generate minimal secret files for testing."""
    
    print("[INFO] Creating minimal secret files for Railway deployment...")
    
    # Create credential manager (this creates .master_key automatically)
    cred_manager = CredentialManager()
    print("[OK] Master key created")
    
    # Create empty accounts dict and save (creates credentials.enc)
    accounts = {}
    cred_manager.save_credentials(accounts)
    print("[OK] Credentials encrypted file created")
    
    # Create minimal config
    config = {
        "tasks": []
    }
    ensure_parent(CONFIG_FILE)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print("[OK] Config file created")
    
    print("\n" + "="*60)
    print("[SUCCESS] All secret files created!")
    print("="*60)
    print("\nNow run: python export_secrets.py")
    print("Then add the base64 strings to your Railway variables.")
    print("\n" + "="*60)

if __name__ == "__main__":
    quickstart()
