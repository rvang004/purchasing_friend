#  Deployment Guide: GitHub + Railway

This guide walks you through deploying Purchase Bot to GitHub and running it on Railway.

---

##  Prerequisites

- GitHub account (free)
- Railway account (free tier available at railway.app)
- Existing local Purchase Bot setup with accounts & tasks configured
- Git installed locally

---

##  Step 1: Prepare Credentials

Before pushing to GitHub, **export your local secrets** so you can restore them on Railway.

### 1a. Export Secrets to Base64

Run this locally to encode your sensitive files:

```bash
python export_secrets.py
```

This outputs three base64-encoded strings:
- `CREDENTIALS_ENC` (encrypted accounts)
- `MASTER_KEY` (encryption key)
- `CONFIG_JSON` (your purchase tasks)

**Copy these values — you'll need them in GitHub.**

### 1b. Verify .gitignore is Correct

Ensure these files are in `.gitignore` (they already are):

```
credentials.enc
.master_key
config.json
```

Run `git status` to confirm they won't be committed:

```bash
$ git status --short
# Should NOT show credentials.enc, .master_key, or config.json
```

---

##  Step 2: Push to GitHub

### 2a. Check Remote URL

```bash
git remote -v
# Should show: origin	https://github.com/rvang004/purchase-bot.git
```

If the remote has an embedded token, update it:

```bash
git remote set-url origin https://github.com/rvang004/purchase-bot.git
```

### 2b. Commit & Push

```bash
git add -A
git commit -m "Add deployment configs for Railway & GitHub Actions"
git push origin main
```

This pushes all code (excluding secrets in `.gitignore`).

---

##  Step 3: Add GitHub Secrets

Go to **GitHub → Your Repo → Settings → Secrets and variables → Actions → New secret**

Add each of these three secrets with the values from `export_secrets.py`:

| Secret Name | Value |
|-------------|-------|
| `MASTER_KEY` | (base64 output from export_secrets.py) |
| `CREDENTIALS_ENC` | (base64 output from export_secrets.py) |
| `CONFIG_JSON` | (base64 output from export_secrets.py) |

**Example:**
- Secret name: `MASTER_KEY`
- Secret value: (paste the base64 string from export_secrets.py)
- Click "Add secret"

Repeat for all three.

###  Verify Secrets Added

```bash
# In GitHub: Settings → Secrets and variables → Actions
# You should see 3 masked secrets listed
```

---

##  Step 4: Deploy to Railway

### 4a. Create Railway Project

1. Go to **railway.app** and sign in (or create account)
2. Click **New Project**
3. Select **Deploy from GitHub**
4. Authorize GitHub & select `rvang004/purchase-bot`

Railway will auto-detect the `railway.json` config and start building.

### 4b. Add Environment Variables

Once Railway is building, go to **Project Settings → Variables**

Add these variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `PURCHASE_BOT_DATA_DIR` | `/data` | Mounts to persistent volume |
| `PYTHONUNBUFFERED` | `1` | Live logging |
| `PORT` | `8100` | Web UI port (auto-set by Railway) |

### 4c. Add Persistent Volume

Your bot needs to save `config.json`, encrypted creds, logs, and history somewhere that survives redeploys.

1. Go to **Project → Volumes** (or Resources tab)
2. Click **Create Volume**
3. Mount path: `/data`
4. Size: 1GB (plenty for logs/history)
5. Save

---

##  Step 5: Configure Services

Railway will create two services from `railway.json`:

### Service 1: `web` (FastAPI UI)

- **Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
- **Port:** 8100 (or Railway's assigned port)
- **URL:** Auto-generated (e.g., `https://purchase-bot-production.railway.app`)

Open this in your browser to manage accounts/tasks via UI.

### Service 2: `scheduler` (Background Loop)

- **Command:** `python main.py run --interval 60`
- **Runs continuously** checking for tasks every 60 seconds
- **No public URL** (internal service)

---

##  Step 6: GitHub Actions (Optional Cron Scheduler)

If you prefer **GitHub Actions to trigger purchases** instead of (or in addition to) the Railway scheduler:

### 6a. GitHub Actions Cron Schedule

The workflow `.github/workflows/scheduled-purchase.yml` runs:
- **Every day at 9:00 AM UTC** (edit cron to your preference)
- **On manual trigger** (workflow_dispatch)

Change the cron time by editing `.github/workflows/scheduled-purchase.yml`:

```yaml
schedule:
  - cron: '0 9 * * *'  # 9 AM UTC daily
  # Examples:
  # 0 */2 * * *     → Every 2 hours
  # 30 14 * * Mon-Fri  → 2:30 PM weekdays
```

### 6b. Push Workflow Updates

```bash
git add .github/workflows/
git commit -m "Update GitHub Actions schedule"
git push origin main
```

Then check **GitHub → Actions** to see workflow runs.

---

##  Testing Your Deployment

### Test 1: Web UI is Accessible

```bash
curl https://purchase-bot-production.railway.app/
# Should return HTML
```

Or open the URL in a browser. You'll see the dashboard.

### Test 2: Manual Trigger (GitHub Actions)

1. Go to **GitHub → Actions**
2. Select **Purchase Bot Scheduled Run**
3. Click **Run workflow**
4. Wait ~2 minutes for completion
5. Check **Artifacts** for logs/screenshots

### Test 3: Check Logs

**Railway logs:**
```bash
# In Railway UI: Project → Logs
# Or via CLI: railway logs -s scheduler
```

**GitHub Actions logs:**
```
GitHub → Actions → Purchase Bot Scheduled Run → Latest run → Click job
```

---

##  Updating Accounts/Tasks

### Via Web UI (Easiest)

1. Open `https://purchase-bot-production.railway.app`
2. Add accounts, tasks, or toggle settings
3. Changes auto-save to the mounted `/data` volume

### Via CLI (Local)

1. Edit locally: `python main.py setup`
2. Export updated secrets: `python export_secrets.py`
3. Update GitHub secrets (Settings → Secrets)
4. Redeploy Railway (push to main, or manual trigger)

---

##  Monitoring & Debugging

### View Scheduler Logs (Railway)

```bash
# Open Railway UI → Project → Logs
# Filter by service: scheduler
```

Look for:
-  `INFO - Purchase completed!`
-  `ERROR - Login failed`
-  `WARNING - Item price exceeds limit`

### Check Purchase History

SSH into Railway container or mount the `/data` volume locally:

```bash
# Download purchase_history.jsonl
cat purchase_history.jsonl | tail -20
```

Each line is a JSON event. Latest purchases show at the end.

### View Artifacts from GitHub Actions

After a GitHub Actions run:
1. **Artifacts** tab shows screenshots/traces from purchases
2. Download `purchase-bot-run.zip` to inspect what went wrong

---

##  Security Best Practices

###  DO:

-  Keep `.master_key` local (never commit)
-  Use GitHub Secrets for sensitive data
-  Rotate GitHub token after deployment
-  Use strong unique passwords for each site
-  Review logs regularly for suspicious activity
-  Keep Railway volume backups (export history periodically)

###  DON'T:

-  Commit `credentials.enc`, `.master_key`, or `config.json`
-  Paste secrets into code/comments
-  Share your `.master_key` file
-  Disable price limits in live mode
-  Use the same password across multiple sites

---

## 🆘 Troubleshooting

### Railway Build Fails

**Error:** `playwright install` fails in build

**Fix:** Railway's nixpacks includes Playwright system deps. If it still fails:
1. Clear Railway cache: **Project → Settings → Clear Build Cache**
2. Redeploy

### Scheduler Doesn't Run

**Error:** Tasks don't execute at scheduled times

**Check:**
1. Verify task is `enabled: true` in config.json
2. Check scheduler logs: `railway logs -s scheduler`
3. Verify `PURCHASE_BOT_DATA_DIR=/data` is set
4. Confirm persistent volume is mounted

### Login Fails on Site

**Error:** `Login failed`

**Check:**
1. Email/password correct locally? Test via `python main.py run --dry-run`
2. Site may have changed login flow → update selectors in `purchase_adapters/`
3. Check if site detects headless browsers (Playwright has anti-detection, but some sites are aggressive)

### Price Limit Blocks Legitimate Purchase

**Error:** `Item price ($X) exceeds limit ($Y)`

**Fix:**
1. Update price limit: `python main.py setup` → Edit account
2. Or disable price limit temporarily: toggle in setup wizard
3. Export & re-deploy

### GitHub Actions Secrets Not Found

**Error:** `Command 'base64 -d' not found` (Windows actions)

**Fix:** Use `base64 --decode` or run on Linux-based runners:

```yaml
runs-on: ubuntu-latest  # Not windows-latest
```

---

##  Next Steps

### Scaling Beyond Purchase-Bot

- **Email alerts:** Add Slack/email notifications on purchase success/failure
- **Database:** Move credentials from encrypted file to PostgreSQL (Railway offers free tier)
- **Web dashboard:** Expand FastAPI UI to show purchase history, spending trends
- **Multi-region:** Run separate instances in different regions for redundancy

### Advanced Configuration

- **Custom adapters:** Add support for new e-commerce sites in `purchase_adapters/`
- **Webhook integrations:** Trigger purchases from external webhooks
- **Policy engine:** Implement complex spending rules (e.g., budget per category)

---

##  Support

- Check logs in Railway or GitHub Actions
- Review the main `README.md` for feature docs
- Test locally with `python main.py run --dry-run` first
- Open an issue on GitHub if you hit a snag

---

**Happy automated shopping! **
