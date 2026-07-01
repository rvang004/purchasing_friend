"""
Export local credentials as base64 for GitHub Actions secrets.

Run this once:
    python export_secrets.py

Then paste each value into GitHub → Settings → Secrets → Actions:
    CREDENTIALS_ENC
    MASTER_KEY
    CONFIG_JSON
"""

import base64
import sys
from pathlib import Path


def encode_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(f"[WARN] {path} not found - skipping")
        return None
    return base64.b64encode(p.read_bytes()).decode()


def main():
    secrets = {
        "CREDENTIALS_ENC": encode_file("credentials.enc"),
        "MASTER_KEY":       encode_file(".master_key"),
        "CONFIG_JSON":      encode_file("config.json"),
    }

    missing = [k for k, v in secrets.items() if v is None]
    if missing:
        print(f"\n[ERROR] Missing files for: {', '.join(missing)}")
        print("   Run `python main.py setup` first to create accounts & tasks.\n")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  GitHub Actions Secrets - copy each value below")
    print("  Destination: github.com/rvang004/purchase-bot")
    print("  -> Settings -> Secrets and variables -> Actions -> New secret")
    print("=" * 60)

    for name, value in secrets.items():
        print(f"\n[KEY] Secret name:  {name}")
        print(f"   Value:\n{value}\n")

    print("=" * 60)
    print("[OK] Done! After adding all 3 secrets, push your code and")
    print("   the bot will run automatically on your cron schedule.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
