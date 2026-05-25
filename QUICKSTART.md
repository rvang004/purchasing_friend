# 🚀 Quick Start Guide (Windows)

## 1. **One-Time Setup**

### Install Python (if not already installed)
- Download from https://www.python.org/downloads/
- During install, **check "Add Python to PATH"**
- Verify: Open PowerShell/CMD and run `python --version`

### Clone the Repository
```powershell
git clone https://github.com/yourusername/purchase-bot.git
cd purchase-bot
```

### Create Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### Install Dependencies
```powershell
pip install -r requirements.txt
playwright install
```

---

## 2. **Configure Your Accounts**

```powershell
python main.py setup
```

**Menu options:**
```
1. Add new account
   - Enter account ID (e.g., "amazon_main")
   - Website URL (e.g., https://www.amazon.com)
   - Email/username
   - Password
   - Payment method (1-4)
   - Monthly spending limit (e.g., $500)
   - Max price per item (e.g., $100)

2. View accounts
   - See all configured accounts (passwords masked)
   - Shows monthly limit AND price per item

3. Add purchase task
   - Select account
   - Enter product URL
   - Choose schedule (once, daily, weekly)
   - Set time (HH:MM 24-hour format)

4. View purchase tasks
   - See all scheduled purchases
```

---

## 3. **Test with Dry-Run**

```powershell
python main.py run --dry-run
```

**What happens:**
- ✅ Loads your accounts and tasks
- ✅ Navigates to product pages
- ✅ Shows what would happen (without purchasing)
- ✅ Produces full logs

**Check results:**
- Open `purchase_bot.log` to see details
- Look for ✅ or ❌ indicators

---

## 4. **Run for Real**

```powershell
python main.py run
```

**The scheduler will:**
- Check for tasks every 60 seconds
- Execute purchases at their scheduled times
- **Automatically check item price** against your limit
- Block purchases that exceed price caps
- Log all activity
- Stop when you press `Ctrl+C`

---

## 4.5 **Understanding Price Protection**

Each account has **TWO price safeguards**:

### 🛡️ Per-Item Price Limit
- Maximum price per individual purchase
- Example: "Don't buy items over $100"
- Bot detects price and blocks if exceeded
- You'll see in logs: `⚠️  Item price exceeds limit`

### 🛡️ Monthly Spending Limit
- Total spending cap for the month
- Example: "Don't spend more than $500/month"
- Tracks all purchases throughout month
- Resets each new month

**Both work together:**
```
Monthly limit: $500 (prevents overspending)
Price per item: $100 (prevents expensive impulse buys)

✅ Item costs $45 → ALLOWED (under both limits)
❌ Item costs $150 → BLOCKED (exceeds per-item limit)
❌ Monthly total $520 → BLOCKED (exceeds monthly limit)
```

---

## 5. **Run Automatically with Windows Task Scheduler**

### Step A: Create Batch File
1. Open Notepad
2. Paste:
```batch
@echo off
cd C:\Users\YOUR_USERNAME\purchase-bot
venv\Scripts\activate.bat
python main.py run
pause
```
3. Replace `YOUR_USERNAME` with your Windows username
4. Save as `C:\Users\YOUR_USERNAME\purchase-bot\start_bot.bat`

### Step B: Open Task Scheduler
1. Press `Windows Key + R`
2. Type `taskschd.msc`
3. Press Enter

### Step C: Create Task
1. Right-click "Task Scheduler Library" → **Create Basic Task**
2. **Name:** Purchase Bot
3. **Description:** Automated e-commerce purchases
4. Click **Next >**

### Step D: Set Trigger
1. Select **At startup** (runs when Windows boots)
2. OR **Daily** and set time
3. Click **Next >**

### Step E: Set Action
1. Select **Start a program**
2. **Program:** `C:\Users\YOUR_USERNAME\purchase-bot\start_bot.bat`
3. Click **Next >**

### Step F: Finish
1. Check **"Open the Properties dialog"**
2. Click **Finish**
3. In Properties, go to **General** tab
4. Check **"Run with highest privileges"**
5. Click **OK**

### Test It
1. Right-click your new task → **Run**
2. Check `purchase_bot.log` for results

---

## 📋 Common Commands

```powershell
# Activate virtual environment (do this first!)
venv\Scripts\activate

# Setup accounts and tasks
python main.py setup

# Test purchases (no real transactions)
python main.py run --dry-run

# Run scheduler (real purchases)
python main.py run

# Run with 30-second check interval
python main.py run --interval 30
```

---

## 🔍 Troubleshooting

### "python: command not found"
```
→ Python not in PATH
→ Download from python.org and reinstall
→ Make sure to check "Add Python to PATH"
```

### "ModuleNotFoundError: No module named 'playwright'"
```
→ Virtual environment not activated
→ Run: venv\Scripts\activate
→ Run: pip install -r requirements.txt
```

### "Config file not found"
```
→ You haven't set up accounts yet
→ Run: python main.py setup
→ Add at least one account and task
```

### "Login failed"
```
→ Email/password incorrect
→ Account doesn't exist on that site
→ Site layout changed (let me know!)
→ Check purchase_bot.log for details
```

### Task Scheduler doesn't run
```
→ Verify batch file path is correct
→ Test batch file manually first
→ Check "Run with highest privileges"
→ Check Event Viewer for errors (search "Event Viewer")
```

---

## 📝 Important Reminders

✅ **DO:**
- Test with `--dry-run` first
- Check logs regularly
- Keep `.master_key` safe
- Review monthly spending limits

❌ **DON'T:**
- Share your credentials
- Commit `credentials.enc` to GitHub
- Use the same password everywhere
- Ignore log warnings

---

## 📞 Need Help?

1. Check `purchase_bot.log` for error messages
2. Run `python main.py run --dry-run` to see what's happening
3. Verify accounts/tasks: `python main.py setup` → View options
4. Check README.md for detailed documentation

---

**You're all set! 🎉 Happy automating!**
