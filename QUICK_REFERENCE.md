# 🎯 Quick Reference Card

## One-Time Setup
```powershell
cd C:\Users\r0v0038\Documents\puppy_workspace\purchase-bot
.\setup_windows.ps1
```

## Daily Commands

### Add/Manage Accounts & Tasks
```powershell
python main.py setup
```

### Test Before Going Live
```powershell
python main.py run --dry-run
```

### Start Scheduler (Real Purchases)
```powershell
python main.py run
```

### Run with Custom Check Interval
```powershell
python main.py run --interval 30
```

---

## Setup Menu (When You Run `python main.py setup`)

| Option | What It Does |
|--------|-------------|
| **1** | Add new account (email, password, payment method) |
| **2** | View all accounts (passwords masked) |
| **3** | Add purchase task (URL, timing, schedule) |
| **4** | View all purchase tasks |
| **5** | Delete account |
| **6** | Delete purchase task |
| **7** | Toggle price limit on/off for any account |
| **8** | Exit |

---

## Scheduling Options

### Daily
```
Time: 14:30
→ Runs every day at 2:30 PM
```

### Weekly
```
Time: 18:00
Days: Mon,Wed,Fri
→ Runs at 6:00 PM on Mon/Wed/Fri
```

### Once
```
Time: 20:00
→ Runs one time at 8:00 PM today
```

---

## Windows Task Scheduler Setup

1. Open: `taskschd.msc`
2. **Create Basic Task**
3. Name: `Purchase Bot`
4. Trigger: **At startup** (or specific time)
5. Action: Start `start_purchase_bot.bat`
6. Enable: **Run with highest privileges**
7. **Test:** Right-click → Run

---

## Troubleshooting Checklist

- [ ] Python installed? `python --version`
- [ ] Virtual env activated? `venv\Scripts\activate`
- [ ] Dependencies installed? `pip install -r requirements.txt`
- [ ] Playwright browsers? `playwright install`
- [ ] Accounts configured? `python main.py setup`
- [ ] Tasks created? `python main.py setup` → option 4
- [ ] Tested with dry-run? `python main.py run --dry-run`
- [ ] Checked logs? `type purchase_bot.log`
- [ ] Task Scheduler path correct? Verify in taskschd.msc

---

## File Locations

```
Project: C:\Users\r0v0038\Documents\puppy_workspace\purchase-bot
Config:  config.json (auto-created)
Creds:   credentials.enc (auto-created, encrypted)
Key:     .master_key (auto-created, keep safe!)
Logs:    purchase_bot.log (auto-created)
```

---

## Important Files to Know

| File | Purpose |
|------|---------|
| `main.py` | Entry point: setup/run commands |
| `cli.py` | Interactive account/task setup |
| `scheduler.py` | Timing logic & execution |
| `purchase_engine.py` | Browser automation (Playwright) |
| `utils.py` | Encryption & credential storage |
| `config.json` | Your purchase tasks |
| `credentials.enc` | Encrypted account data |
| `.master_key` | Encryption key (keep safe!) |
| `purchase_bot.log` | All activity logs |

---

## Key Security Reminders

✅ **DO:**
- Keep `.master_key` safe
- Use `--dry-run` before real purchases
- Check logs regularly
- Use unique passwords
- Review spending limits

❌ **DON'T:**
- Share `.master_key`
- Commit `credentials.enc`
- Ignore error logs
- Violate site ToS
- Set unlimited budgets

---

## Common Errors & Fixes

```
❌ "python: command not found"
✅ Python not in PATH. Reinstall from python.org

❌ "ModuleNotFoundError: playwright"
✅ Run: pip install -r requirements.txt

❌ "Config file not found"
✅ Run: python main.py setup (to create)

❌ "Login failed"
✅ Check email/password. Run with --dry-run for details.

❌ "Monthly limit reached"
✅ Edit account in setup wizard. Increase limit.

❌ Task Scheduler doesn't run
✅ Check batch file path. Test manually first.
```

---

## Pro Tips

💡 **Run scheduler in background:**
```powershell
# Open separate PowerShell, run:
python main.py run
# Close window, scheduler keeps running
```

💡 **Monitor logs live:**
```powershell
Get-Content purchase_bot.log -Tail 20 -Wait
```

💡 **Test specific task:**
```powershell
python main.py run --dry-run
# Checks timing, shows what would run
```

💡 **Check spending:**
```powershell
python main.py setup
# Option 2: View accounts (shows spent_this_month)
```

---

## Documentation Map

- 📖 **Start here:** `QUICKSTART.md` (5-min Windows setup)
- 📚 **Full docs:** `README.md` (200+ lines of features)
- 🎓 **Deep dive:** `SETUP_GUIDE.md` (detailed explanations)
- 📋 **This page:** `QUICK_REFERENCE.md` (cheat sheet)
- 📊 **Overview:** `SUMMARY.md` (architecture & design)

---

## What Gets Logged?

Every action logged to `purchase_bot.log`:

```
✅ Task checks
✅ Login attempts
✅ Product navigation
✅ Cart additions
✅ Checkouts
✅ Purchases completed
❌ Errors & failures
⏰ Timing of everything
💳 Spending per account
```

---

## Credentials: What Gets Stored

Per account, encrypted in `credentials.enc`:
```json
{
  "site": "https://www.amazon.com",
  "email": "your@email.com",
  "password": "encrypted_password",
  "payment_method": "credit_card",
  "monthly_limit": 500.00,
  "spent_this_month": 125.50
}
```

**All encrypted with AES. Never stored as plaintext.**

---

## Git Commands

```powershell
# First time setup
git config --global user.email "your@email.com"
git config --global user.name "Your Name"

# After changes
git add .
git commit -m "Description of changes"
git push origin main

# Pull updates
git pull origin main
```

---

## Environment Variables (Optional)

If you want to use env vars instead of `.master_key`:

```powershell
# Set environment variable
[Environment]::SetEnvironmentVariable("PURCHASE_BOT_KEY", "your-key")

# Verify
echo $env:PURCHASE_BOT_KEY
```

Then modify `utils.py` to check env var first.

---

## When Something Goes Wrong

1. Check `purchase_bot.log` for errors
2. Run `python main.py run --dry-run` to simulate
3. Verify accounts exist: `python main.py setup` → option 2
4. Verify tasks exist: `python main.py setup` → option 4
5. Test Task Scheduler task manually
6. Check Event Viewer for task errors (search "Event Viewer")

---

## Contact & Help

- 📖 **Documentation:** See README.md, QUICKSTART.md, SETUP_GUIDE.md
- 🔍 **Debug:** Run with `--dry-run`, check logs
- 🛠️ **Customize:** Edit `purchase_engine.py` for site-specific logic
- 🐛 **Report issues:** Check logs first, then review code comments

---

**Bookmark this page for quick reference!** 📌

*Everything you need to run, debug, and customize purchase-bot.*
