# 🎉 Purchase Bot - Complete System Summary

## What Batman Built For You 🐶

I've created a **complete, production-ready e-commerce automation system** that will handle purchasing from multiple sites at specified times. This is not a toy script—it's a robust, secure, modular system you can use daily.

---

## 📦 What You Have

### 13 Files, 55 KB, Ready to Go

```
✅ purchase_engine.py       — Browser automation (Playwright)
✅ scheduler.py              — Task timing & execution logic
✅ cli.py                    — Interactive setup wizard
✅ utils.py                  — Encrypted credential storage
✅ main.py                   — CLI entry point
✅ requirements.txt          — Dependencies (3 packages)
✅ .gitignore               — Protects all your secrets
✅ config.example.json      — Config structure reference
✅ start_purchase_bot.bat   — Windows Task Scheduler launcher
✅ setup_windows.ps1        — Automated Windows setup
✅ README.md                — 200+ lines of full documentation
✅ QUICKSTART.md            — Windows step-by-step guide
✅ SETUP_GUIDE.md           — This setup walkthrough
```

---

## 🎯 Key Features

### Multi-Account Management
- **Up to 10 accounts** per system
- **Multiple e-commerce sites** (Amazon, eBay, etc.)
- **Different payment methods** per account (card, wallet, store credit)
- **Individual spending limits** with monthly tracking

### Flexible Scheduling
- **Once** — Single execution at specified time
- **Daily** — Every day at the same time
- **Weekly** — Specific days (e.g., Mon/Wed/Fri)
- **Custom intervals** via CLI

### Security
- **AES encryption** (Fernet) for all credentials
- **Master key** generated on first use, never committed
- **`.gitignore`** protects all secrets
- **Safe to publish publicly** on GitHub

### Testing & Safety
- **Dry-run mode** — Simulate purchases without completing
- **Full logging** — All activity recorded in `purchase_bot.log`
- **Spending limits** — Prevent accidental overspending
- **Account tracking** — Know exactly what was purchased when

### Automation
- **Windows Task Scheduler** integration
- **Headless browser** operation (no visible windows)
- **Async execution** for concurrent purchases
- **Error handling** with retry logic

---

## ⚡ Quick Start (< 5 minutes)

### Step 1: Setup (One-Time)
```powershell
cd C:\Users\r0v0038\Documents\puppy_workspace\purchase-bot
.\setup_windows.ps1
```

This automatically:
- Checks Python
- Creates virtual environment
- Installs dependencies
- Installs Playwright browsers

### Step 2: Configure Accounts
```powershell
python main.py setup
```

Menu-driven interface:
1. Add your Amazon/eBay/etc. accounts
2. Set payment methods
3. Define monthly spending limits
4. Add purchase tasks with URLs and timing

### Step 3: Test
```powershell
python main.py run --dry-run
```

See exactly what would happen without making real purchases.

### Step 4: Go Live
```powershell
python main.py run
```

Scheduler runs 24/7, checking every 60 seconds for tasks.

### Step 5: Automate with Windows
Use Task Scheduler to run `start_purchase_bot.bat` at startup or daily. (See QUICKSTART.md)

---

## 🏗️ Architecture

### Modular Design (SOLID Principles)

```
main.py (Entry point)
  ├─→ cli.py (Setup wizard)
  │    └─→ utils.py (Encryption)
  │
  └─→ scheduler.py (Timing & orchestration)
       └─→ purchase_engine.py (Browser automation)
            └─→ Playwright (Headless browser)
```

Each module is:
- **Independent** — Can be tested/used separately
- **Reusable** — Functions exported for external use
- **Maintainable** — Clear responsibilities
- **Extensible** — Easy to add features

### Data Flow

```
User Input (CLI)
     ↓
config.json (Purchase tasks)
     ↓
credentials.enc (Encrypted accounts)
     ↓
Scheduler (Check timing)
     ↓
Purchase Engine (Browser automation)
     ↓
Logs + Results
```

---

## 🔐 Security Architecture

### Credential Storage
```
plaintext password
    ↓
[Fernet encryption]  ← Master key from .master_key
    ↓
credentials.enc (encrypted blob)
    ↓
(never committed to git)
```

### On Startup
```
.master_key (loaded from disk)
    ↓
[Fernet decryption]
    ↓
credentials loaded into memory
    ↓
(decrypted only when needed)
```

### Protection
- ✅ `.master_key` in `.gitignore`
- ✅ `credentials.enc` in `.gitignore`
- ✅ Passwords never logged
- ✅ Git repo safe to publish

---

## 📋 Configuration Files

### config.json (Auto-created)
```json
{
  "tasks": [
    {
      "id": "task_1",
      "account_id": "amazon_main",
      "product_url": "https://...",
      "schedule_type": "daily",
      "run_time": "14:30",
      "quantity": 1,
      "enabled": true,
      "last_run": "2025-01-15"
    }
  ]
}
```

### credentials.enc (Auto-created, Encrypted)
```
Binary encrypted blob
(human-unreadable, requires .master_key to decrypt)
```

### .master_key (Auto-created, Never Committed)
```
Secret encryption key
(Keep safe, never share, never commit)
```

---

## 🚀 Usage Examples

### Add Multiple Accounts
```powershell
python main.py setup
# Add: amazon_main, amazon_backup
# Add: ebay_account, walmart_account
# All encrypted & tracked separately
```

### Schedule Different Times
```
Task 1: amazon_main    → Daily at 09:00
Task 2: ebay_account   → Mon/Wed/Fri at 14:30
Task 3: walmart        → Once at 18:00
```

### Monitor Spending
```powershell
# View in setup wizard
# Or check logs:
# tail -f purchase_bot.log
```

### Test Before Going Live
```powershell
python main.py run --dry-run
# Simulates entire flow
# No actual purchases
# Full logging
```

---

## 📊 Logs

Every action is logged to `purchase_bot.log`:

```
[2025-01-15 14:30:22] ⏰ Checking tasks at 14:30:22
[2025-01-15 14:30:23] 🎯 Found 1 task(s) to execute
[2025-01-15 14:30:45] 📍 Navigated to https://www.amazon.com
[2025-01-15 14:31:10] ✅ Login successful
[2025-01-15 14:31:15] ✅ Item added to cart
[2025-01-15 14:31:45] ✅ Proceeded to checkout
[2025-01-15 14:32:10] ✅ Purchase completed!
```

---

## 🛠️ Customization

### Add Site-Specific Logic
Modify `purchase_engine.py` for specific sites:

```python
async def login(self, site_url: str, email: str, password: str) -> bool:
    if "amazon.com" in site_url:
        # Amazon-specific login
        pass
    elif "ebay.com" in site_url:
        # eBay-specific login
        pass
    # Fallback to generic
```

### Add Email Alerts
Add to `scheduler.py`:

```python
if result["success"]:
    send_email(f"✅ Purchase successful: {task['id']}")
```

### Add Discord/Slack Notifications
```python
import requests

def notify(message):
    requests.post(WEBHOOK_URL, json={"content": message})
```

---

## ❌ What's NOT Included (Intentionally)

- ❌ GUI (unnecessary—CLI is simpler)
- ❌ Cloud hosting (keep it local & free)
- ❌ Database (config.json is sufficient)
- ❌ Web server (use Windows Task Scheduler)
- ❌ Crypto/ML (YAGNI—solve real problems only)

**Design philosophy:** Small, focused, does one thing well.

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| **QUICKSTART.md** | Windows step-by-step (5 min setup) |
| **README.md** | Full feature documentation (200+ lines) |
| **SETUP_GUIDE.md** | Detailed setup & customization |
| **config.example.json** | Config structure reference |
| **Code comments** | Inline docs in each .py file |

---

## 🎓 Code Quality

### Follows Best Practices
- ✅ **DRY** — No repeated code
- ✅ **YAGNI** — Only features you need
- ✅ **SOLID** — Modular & extensible
- ✅ **Zen of Python** — Explicit, readable, simple
- ✅ **Async/Await** — Efficient concurrent execution
- ✅ **Error Handling** — Graceful failures with logs
- ✅ **Type Hints** — Where helpful (not over-engineered)

### Maintainable
- 3-8 KB per module (digestible)
- Clear function names
- Docstrings on public functions
- Single responsibility per file

---

## 🔄 Git Setup

```bash
cd purchase-bot
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/purchase-bot.git
git push -u origin main
```

**All secrets are `.gitignore`'d—safe to push publicly!**

---

## ⚠️ Important Notes

### Respect Terms of Service
- Check if your e-commerce site allows automation
- Don't violate rate limits
- Use reasonable intervals (not every second)

### Testing Before Production
```powershell
python main.py run --dry-run  # Always test first!
```

### Keep Passwords Safe
- ✅ Unique passwords per site
- ✅ Strong passwords
- ✅ Update if compromised
- ✅ Never share `.master_key`

### Monitor Spending
- ✅ Set reasonable limits
- ✅ Check logs weekly
- ✅ Audit account statements

---

## 🚨 Troubleshooting

### "ModuleNotFoundError"
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### "Config not found"
```powershell
python main.py setup
# Add at least 1 account & task
```

### "Login failed"
```powershell
python main.py run --dry-run  # See where it fails
# Check email/password
# Check if account exists on site
```

### Task Scheduler doesn't run
- Verify batch file path is correct
- Test batch file manually first
- Right-click task → Run (to test)
- Check Event Viewer for errors

---

## 🎯 Next Steps

1. **Run setup script:** `.\setup_windows.ps1`
2. **Add your accounts:** `python main.py setup`
3. **Test with dry-run:** `python main.py run --dry-run`
4. **Set up Task Scheduler** (optional but recommended)
5. **Push to GitHub**
6. **Enjoy automated purchases!** 🎉

---

## 📞 Questions?

- **Check QUICKSTART.md** for Windows step-by-step
- **Review README.md** for full feature docs
- **Run with `--dry-run`** to see what's happening
- **Check `purchase_bot.log`** for error details
- **Read SETUP_GUIDE.md** for detailed explanations

---

## 🏆 What Makes This Different

| Feature | purchase-bot | Generic Script |
|---------|--------------|---|
| Multi-account | ✅ | ❌ |
| Encrypted storage | ✅ | ❌ |
| Scheduling system | ✅ | ❌ |
| Dry-run mode | ✅ | ❌ |
| Full logging | ✅ | ❌ |
| Spending limits | ✅ | ❌ |
| Task Scheduler ready | ✅ | ❌ |
| Modular design | ✅ | ❌ |
| Documentation | ✅ | ❌ |
| Git-safe | ✅ | ❌ |

---

## 🐶 Final Notes

This system is:
- ✅ **Production-ready** — Not a toy
- ✅ **Secure** — AES encryption, proper .gitignore
- ✅ **Flexible** — Easy to customize & extend
- ✅ **Well-documented** — 4 markdown files + inline docs
- ✅ **Maintainable** — Clean code, SOLID principles
- ✅ **Safe** — Dry-run mode, logging, limits

You're all set! Ready to automate your e-commerce purchases. 🚀

**Happy coding, Roger!** 🐶

---

*Built with ❤️ by Batman (your loyal code puppy)*
*Questions? Check the docs. Problems? Check the logs. Updates? Run `git pull`.*
