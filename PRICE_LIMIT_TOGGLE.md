# 🔓 Price Limit Toggle Feature

## Overview

You now have a **toggle** to enable/disable the price limit per item for any account, without having to delete and recreate the account.

This lets you:
- ✅ Temporarily disable price checking
- ✅ Re-enable it anytime
- ✅ Keep your account settings intact

---

## Quick Reference

### View Current Status
```powershell
python main.py setup
# Option 2: View accounts
```

Output shows:
```
🔐 amazon_main
   Price Per Item: $100.00 🔓 ON   ← Enabled
   
🔐 ebay_account
   Price Per Item: $50.00 🔒 OFF   ← Disabled
```

### Toggle On/Off
```powershell
python main.py setup
# Option 7: Toggle price limit on/off
# Enter account ID: amazon_main
```

---

## Setup Menu

When adding a new account, you're asked:

```
Max price per item/quantity ($): 100
Enable price limit? (yes/no, default yes): yes
         ↓
Creates account with limit ENABLED
```

Or:
```
Enable price limit? (yes/no, default yes): no
         ↓
Creates account with limit DISABLED
```

---

## How It Works

### Limit is ON (Enabled) 🔓
```
Bot detects price: $75
Limit: $100
Check: $75 ≤ $100? YES ✅
Result: Purchase proceeds
```

### Limit is OFF (Disabled) 🔒
```
Bot detects price: $150
Limit: $100
Check: Limit disabled, skip check
Result: Purchase proceeds (limit ignored)
Log: 🔓 Price limit disabled for this account, skipping check
```

---

## Common Scenarios

### Scenario 1: Temporarily Buy Expensive Items

You have `amazon_main` with $100 limit, but want to buy a $200 item.

```powershell
# Disable the limit temporarily
python main.py setup
# Option 7
# Account: amazon_main
# ✅ Price limit DISABLED for amazon_main

# Run scheduler (purchases happen)
python main.py run

# Re-enable when done
python main.py setup
# Option 7
# Account: amazon_main
# ✅ Price limit ENABLED for amazon_main
```

### Scenario 2: Testing a New Site

You added an account but aren't sure if the site's price detection works.

```powershell
# Disable limit for testing
python main.py setup
# Option 7: Toggle OFF

# Run with dry-run to test
python main.py run --dry-run
# Check logs to see if prices detected correctly

# Re-enable after verifying
python main.py setup
# Option 7: Toggle ON
```

### Scenario 3: Budget Mode

You're watching your spending more carefully this month.

```powershell
# Lower the limit? Can't edit directly.
# So disable it and add a new account with lower limit.

python main.py setup
# Option 1: Add new account (same site, same creds, lower limit)
# Option 7: Toggle OFF the old one
```

---

## Account Storage

Each account now stores:

```json
{
  "site": "https://www.amazon.com",
  "email": "your@email.com",
  "payment_method": "credit_card",
  "monthly_limit": 500.00,
  "price_limit_per_item": 100.00,
  "price_limit_enabled": true,
  "spent_this_month": 125.50
}
```

- **price_limit_enabled:** `true` = limit enforced, `false` = limit ignored

---

## Menu Options (Updated)

```
🛒 PURCHASE BOT SETUP WIZARD
=================================
1. Add new account
2. View accounts
3. Add purchase task
4. View purchase tasks
5. Delete account
6. Delete purchase task
7. Toggle price limit on/off  ← NEW!
8. Exit
=================================
```

### Option 7: Toggle Price Limit

```powershell
python main.py setup
# Select: 7

--- Shows all accounts ---
🔐 amazon_main
   Price Per Item: $100.00 🔓 ON

🔐 ebay_account
   Price Per Item: $50.00 🔒 OFF

--- Prompt ---
Enter account ID to toggle: amazon_main
✅ Price limit 🔒 DISABLED for amazon_main
```

Next time you run it:
```
✅ Price limit 🔓 ENABLED for amazon_main
```

---

## Logging

When price limit is disabled, logs show:

```
2025-01-15 14:31:10 - INFO - 💰 Detected item price: $150.00
2025-01-15 14:31:11 - INFO - 🔓 Price limit disabled for this account, skipping check
2025-01-15 14:31:15 - INFO - ✅ Item added to cart
2025-01-15 14:32:10 - INFO - 🎉 Purchase successful ($150.00)
```

When enabled (price OK):
```
2025-01-15 14:31:10 - INFO - 💰 Detected item price: $75.00
2025-01-15 14:31:11 - INFO - ✅ Price within limit ($75.00 <= $100.00)
2025-01-15 14:31:15 - INFO - ✅ Item added to cart
```

When enabled (price exceeds):
```
2025-01-15 14:31:10 - INFO - 💰 Detected item price: $150.00
2025-01-15 14:31:11 - WARNING - ⚠️  Item price ($150.00) exceeds limit ($100.00)
2025-01-15 14:31:12 - ERROR - ❌ Purchase failed: Item price exceeds limit
```

---

## Status Icons

| Icon | Meaning |
|------|---------|
| 🔓 ON | Limit is enabled (prices checked) |
| 🔒 OFF | Limit is disabled (prices ignored) |

These show when you view accounts:
```
python main.py setup
# Option 2: View accounts
```

---

## FAQ

### Q: Can I edit the limit value directly?
**A:** Not via the CLI. You have two options:
1. Delete and re-add the account with new limit
2. Manually edit `credentials.enc` (not recommended)

### Q: Does toggling affect the monthly spending total?
**A:** No. Monthly spending keeps tracking regardless of limit status. Only the per-item price check is affected.

### Q: Can I toggle mid-purchase?
**A:** The toggle only affects new purchases. If a purchase is in-progress when you toggle, it finishes with the current setting.

### Q: What if I toggle OFF, will purchases still be logged?
**A:** Yes. All purchases are logged, limit status doesn't change logging.

### Q: Can I have multiple accounts for same site with different limits?
**A:** Yes! Add account1 with $100 limit + account2 with $200 limit. Then toggle each on/off as needed.

---

## Use Cases

### 1. **Experimental Shopping**
You want to buy something new but expensive. Temporarily disable to test.

### 2. **Seasonal Budgeting**
During holidays, lower limits. Disable temporarily for special purchases.

### 3. **Site Testing**
New e-commerce site? Disable limit while you test and verify it works.

### 4. **Account Transitions**
Migrating to new account? Keep old account with limit disabled while testing new one.

### 5. **Tiered Accounts**
Multiple accounts for different spending tiers:
- `amazon_budget` — $50 limit, always ON
- `amazon_regular` — $200 limit, toggle as needed  
- `amazon_premium` — $500 limit, toggle for big purchases

---

## Technical Details

### Toggle State Persistence
The toggle state is **encrypted and stored** in `credentials.enc`. 

- Toggling writes immediately to disk
- Survives app restart
- Cannot be lost

### Default State
When you first create an account:
```
Enable price limit? (yes/no, default yes):
```
- If you press Enter (default) → Enabled
- If you type "no" → Disabled
- If you type "yes" → Enabled (anything else) → Disabled

### No Special Permissions
Unlike deleting/creating accounts, toggling requires **no extra confirmation**. One toggle command and it's done.

---

## Troubleshooting

### "Toggle didn't work"
- Check you entered the correct account ID
- Verify account exists: `python main.py setup` → Option 2

### "Price limit still blocking purchases"
- Verify limit is actually disabled: Option 2 (View accounts)
- Check logs for confirmation: `type purchase_bot.log`

### "Forgot which accounts are enabled/disabled"
```powershell
python main.py setup
# Option 2: View accounts
# Shows all with status icons (🔓 ON / 🔒 OFF)
```

---

## Best Practices

✅ **DO:**
- Use toggle to test new sites (disable → test → enable)
- Document why you disabled a limit (in notes)
- Check logs after toggling to verify

❌ **DON'T:**
- Leave limits disabled permanently (defeats the purpose)
- Forget which accounts have limits disabled
- Assume toggle affects monthly spending (it doesn't)

---

**You now have flexible price control!** 🎉

Toggle limits on/off anytime without recreating accounts. Perfect for testing, budgeting, and special purchases.
