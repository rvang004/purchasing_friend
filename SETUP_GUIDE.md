# 🎉 Setup & Deployment Guide

## What You Got

I've built you a **complete, production-ready e-commerce automation system**. Here's what's included:

### Core Components
- **purchase_engine.py** — Playwright-powered browser automation
- **scheduler.py** — Task scheduling with timing logic
- **cli.py** — Interactive setup wizard for accounts & tasks
- **utils.py** — Encrypted credential storage
- **main.py** — CLI entry point

### Features
✅ Encrypt & securely store up to 10 account credentials
✅ Multiple e-commerce sites (Amazon, eBay, etc.)
✅ Individual payment methods & monthly spending limits per account
✅ Flexible scheduling: once, daily, weekly
✅ Dry-run mode for testing
✅ Full logging with purchase history
✅ Windows Task Scheduler integration
✅ Git-ready (all secrets in .gitignore)

---

## 🚀 Getting Started (5 minutes)

### 1. **Run Windows Setup Script** (Easiest)

```powershell
# Open PowerShell in purchase-bot directory
cd C:\Users\r0v0038\Documents\puppy_workspace\purchase-bot
.\setup_windows.ps1
```

This will:
- ✅ Verify Python
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Install Playwright browsers

### 2. **Manual Setup** (If PowerShell script doesn't work)

```powershell
# Create & activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install

# You're ready!
```

### 3. **Add Your First Account**

```powershell
python main.py setup
```

**Follow the wizard:**
- Select option **1** (Add new account)
- Enter account ID: `amazon_main`
- Website: `https://www.amazon.com`
- Email & password
- Payment method
- Monthly limit: `500`

### 4. **Add a Purchase Task**

- Select option **3** (Add purchase task)
- Choose account: `amazon_main`
- Enter product URL (e.g., `https://www.amazon.com/dp/B0123456789`)
- Schedule: **Daily** at **14:30** (2:30 PM)

### 5. **Test with Dry-Run**

```powershell
python main.py run --dry-run
```

This will show you exactly what would happen **without** making actual purchases. Check the output for any errors.

### 6. **Run for Real**

```powershell
python main.py run
```

The scheduler checks every 60 seconds. Press `Ctrl+C` to stop.

---

## ⏰ Windows Task Scheduler Setup

### Option A: Automated (PowerShell)
*Coming soon: scheduler setup script*

### Option B: Manual
1. Press `Windows Key + R` → type `taskschd.msc`
2. Right-click **Task Scheduler Library** → **Create Basic Task**
3. Name: `Purchase Bot`
4. Trigger: **At startup** (or Daily/Weekly)
5. Action: Start program
6. Program: `C:\Users\YOUR_USERNAME\purchase-bot\start_purchase_bot.bat`
7. Check "Run with highest privileges"
8. Click OK

**Test:** Right-click task → **Run**

---

## 📁 File Structure

```
purchase-bot/
├── main.py                   # Entry point: python main.py setup/run
├── cli.py                    # Account/task setup wizard
├── scheduler.py              # Timing logic & execution
├── purchase_engine.py        # Playwright browser automation
├── utils.py                  # Encryption utilities
├── requirements.txt          # Dependencies
├── start_purchase_bot.bat    # Windows Task Scheduler launcher
├── setup_windows.ps1         # Automated setup script
├── .gitignore               # Ignores secrets & caches
├── config.json              # Purchase tasks (auto-created)
├── credentials.enc          # Encrypted accounts (auto-created)
├── .master_key              # Encryption key (auto-created)
├── purchase_bot.log         # Activity log (auto-created)
├── README.md                # Full documentation
├── QUICKSTART.md            # Windows quick start
└── config.example.json      # Config structure reference
```

---

## 🔐 Security Details

### How It Works
1. **Master Key:** Generated once on first use, stored in `.master_key`
2. **Encryption:** Fernet (AES) from cryptography library
3. **Storage:** Passwords encrypted in `credentials.enc`
4. **Decryption:** Only in-memory during purchases

### Protection
- ✅ `.master_key` in `.gitignore` (never committed)
- ✅ `credentials.enc` in `.gitignore` (never committed)
- ✅ `config.json` in `.gitignore` (never committed)
- ✅ Passwords never logged
- ✅ Passwords never stored as plaintext

### Safe to Push to GitHub
Once `.gitignore` is applied, all secrets are protected. Safe to publish publicly.

---

## 💳 Account Management

### View All Accounts
```powershell
python main.py setup
# Then select option 2 (View accounts)
```

### Edit Account
1. Delete: `setup` → option 5
2. Re-add with new info: `setup` → option 1

### Update Spending Limit
```powershell
python main.py setup
# Option 5: Delete
# Option 1: Add with new limit
```

---

## 📊 Logs & Monitoring

Check `purchase_bot.log` to see:
- ✅ Successful purchases
- ❌ Failed purchases (with reasons)
- ⏰ Timing of each execution
- 💳 Monthly spending per account

**Example log:**
```
2025-01-15 14:30:22 - INFO - ⏰ Checking tasks at 14:30:22
2025-01-15 14:30:23 - INFO - 🎯 Found 1 task(s) to execute
2025-01-15 14:30:45 - INFO - ✅ Login successful
2025-01-15 14:31:10 - INFO - ✅ Purchase completed!
```

---

## 🛠️ Common Tasks

### Run Setup Wizard Again
```powershell
python main.py setup
```

### Test Before Going Live
```powershell
python main.py run --dry-run
```

### Run with Custom Check Interval
```powershell
python main.py run --interval 30
```
(Checks every 30 seconds instead of 60)

### Stop the Scheduler
Press `Ctrl+C` in the terminal

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "python: command not found" | Python not in PATH. Reinstall from python.org |
| "No module named 'playwright'" | Run `venv\Scripts\activate` then `pip install -r requirements.txt` |
| "Config file not found" | Run `python main.py setup` to create config |
| "Login failed" | Check email/password. Check if account exists on site |
| "Monthly limit reached" | Edit account: `setup` → delete → re-add with higher limit |
| Task Scheduler doesn't run | Verify batch file path. Test manually first. Check Event Viewer |

---

## 🚀 Next Steps

1. **Run setup wizard:** `python main.py setup`
2. **Add 1-2 test accounts**
3. **Add purchase tasks**
4. **Test with dry-run:** `python main.py run --dry-run`
5. **Set up Windows Task Scheduler**
6. **Push to GitHub** (all secrets protected)
7. **Sit back and enjoy automation!** 🎉

---

## 📚 Documentation

- **README.md** — Full feature documentation
- **QUICKSTART.md** — Windows step-by-step guide
- **config.example.json** — Config structure reference
- **start_purchase_bot.bat** — Task Scheduler launcher

---

## 🎯 Design Principles

- **DRY:** No repeated logic
- **YAGNI:** Only features you need
- **SOLID:** Modular, testable code
- **KISS:** Simple to use, understand, modify
- **Security First:** Encrypted storage, no plaintext secrets

---

## ⚙️ Tech Stack

- **Python 3.8+**
- **Playwright** — Browser automation
- **Cryptography** — AES encryption
- **asyncio** — Concurrent execution
- **No external APIs** — Works with any e-commerce site

---

## 📝 Important Reminders

✅ **DO:**
- Test with `--dry-run` first
- Check logs regularly
- Keep `.master_key` safe
- Use unique passwords per site when possible
- Review spending limits monthly

❌ **DON'T:**
- Share your `.master_key`
- Commit `credentials.enc` (it's in .gitignore)
- Ignore log errors
- Set unreasonable purchase limits
- Violate site Terms of Service

---

**You've got this! 🐶 Happy automating, Roger!**

Questions? Check the logs, run with `--dry-run`, or review the docs.
