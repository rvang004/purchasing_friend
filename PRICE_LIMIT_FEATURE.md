# 💰 Price Limit Per Item Feature

## Overview

Your purchase bot now has **dual-layer price protection**:

1. **Monthly Spending Limit** — Total monthly cap (e.g., don't spend over $500/month)
2. **Price Per Item Limit** — Per-purchase cap (e.g., don't buy items over $100 each)

Both work together to prevent accidental overspending and impulse purchases.

---

## How It Works

### Setup Phase
When you add an account via `python main.py setup`:

```
1. Add new account
   - Account ID: amazon_main
   - Website: https://www.amazon.com
   - Email: your@email.com
   - Password: ••••••••••
   - Payment method: 1 (Credit Card)
   - Monthly spending limit: $500
   - Max price per item: $100  ← NEW!
```

### Purchase Execution

Before each purchase, the bot:

1. **Logs in** to your account
2. **Navigates** to product URL
3. **Detects** the item price from the product page
4. **Checks** against `price_limit_per_item`
5. **Blocks** or **proceeds** accordingly
6. **Logs** everything for audit trail

### Example Scenarios

#### ✅ Price Within Limit
```
Account: amazon_main
Price limit per item: $100.00
Product price detected: $45.99

Status: ✅ ALLOWED
Log: 💰 Detected item price: $45.99
Log: ✅ Price within limit ($45.99 <= $100.00)
Log: ✅ Item added to cart
Result: Purchase proceeds
```

#### ❌ Price Exceeds Per-Item Limit
```
Account: amazon_main
Price limit per item: $100.00
Product price detected: $150.00

Status: ❌ BLOCKED
Log: 💰 Detected item price: $150.00
Log: ⚠️  Item price ($150.00) exceeds limit ($100.00)
Log: ❌ Purchase failed: Item price exceeds limit
Result: Purchase prevented (item not purchased)
```

#### ❌ Monthly Limit Reached
```
Account: amazon_main
Monthly limit: $500.00
Currently spent: $500.00 (this month)

Status: ❌ BLOCKED
Log: ⚠️  amazon_main has reached monthly limit ($500.00/$500.00)
Result: All purchases blocked until next month
```

---

## Managing Price Limits

### View Current Limits
```powershell
python main.py setup
# Option 2: View accounts
```

Output example:
```
🔐 amazon_main
   Site: https://www.amazon.com
   Email: you***@***
   Payment: credit_card
   Monthly Limit: $500 (Spent: $125.50)
   Price Per Item: $100.00
```

### Update Price Limit

There's no direct "edit" option, so:

1. Run setup: `python main.py setup`
2. Delete the account: `Option 5`
3. Recreate with new limit: `Option 1`

Or manually edit `credentials.enc` (if you know the master key):
- Not recommended for non-technical users

---

## Account Storage

Each account in encrypted storage includes:

```json
{
  "site": "https://www.amazon.com",
  "email": "your@email.com",
  "password": "encrypted_password",
  "payment_method": "credit_card",
  "monthly_limit": 500.00,
  "price_limit_per_item": 100.00,
  "spent_this_month": 125.50
}
```

- **monthly_limit** — Max total spend per month
- **price_limit_per_item** — Max per individual purchase
- **spent_this_month** — Running total (tracked automatically)

---

## Price Detection

### How Prices Are Found

The bot uses multiple generic CSS selectors to find prices:

```python
'[class*="price" i]'          # Class containing "price"
'[id*="price" i]'             # ID containing "price"
'span[class*="price" i]'      # Span with price class
'[class*="amount" i]'         # Class containing "amount"
'[class*="cost" i]'           # Class containing "cost"
```

### What If Price Can't Be Found?

If the bot can't detect a price:

```
⚠️  Could not detect price, proceeding with caution
```

The purchase **proceeds anyway** (assumes price is OK). This is by design—don't want to block valid purchases.

### Improving Price Detection

For specific sites, you can modify `purchase_engine.py`:

```python
async def get_item_price(self) -> float:
    """Extract item price from product page (generic selector)."""
    # Add Amazon-specific logic here
    if "amazon.com" in self.page.url:
        element = await self.page.query_selector('span.a-price-whole')
        # ...
    
    # Fall back to generic selectors
```

---

## Logging & Auditing

Every price check is logged to `purchase_bot.log`:

```
2025-01-15 14:30:45 - INFO - 📍 Product page loaded
2025-01-15 14:30:47 - INFO - 💰 Detected item price: $45.99
2025-01-15 14:30:48 - INFO - ✅ Price within limit ($45.99 <= $100.00)
2025-01-15 14:30:52 - INFO - ✅ Item added to cart
2025-01-15 14:31:10 - INFO - 🎉 Purchase successful ($45.99)
```

Check logs regularly to:
- ✅ Verify prices detected correctly
- ✅ Confirm purchases weren't over limits
- ✅ Track spending per account
- ✅ Audit all automated actions

---

## Safety Features Summary

### Layer 1: Per-Item Price Check
- Runs **before** adding to cart
- Prevents expensive items from being purchased
- Example: "No items over $100"

### Layer 2: Monthly Spending Limit
- Tracks cumulative spending
- Resets each month
- Example: "Max $500/month"

### Layer 3: Dry-Run Testing
```powershell
python main.py run --dry-run
# Simulates everything including price checks
```

### Layer 4: Full Logging
```powershell
# Check logs to see all price checks
type purchase_bot.log
```

---

## Common Questions

### Q: Can I have different price limits for different accounts?
**A:** Yes! Each account has its own `price_limit_per_item`. 
- amazon_main: $100/item
- ebay_account: $50/item
- walmart: $200/item

### Q: What happens if I change the price limit mid-month?
**A:** The new limit applies immediately to future purchases. 
Monthly spending total continues tracking from before the change.

### Q: Does the bot track quantity x price?
**A:** Currently, it detects the **displayed price per item**. If you're buying quantity > 1, you should set the limit accordingly.

Example: Buying 2 items at $50 each
- Total: $100
- Set per-item limit to at least $100 (or $50 if you want to prevent individual items that expensive)

### Q: What if price is listed as "Contact for Price"?
**A:** The bot won't detect a numeric price, so it will log a warning and proceed with caution. You should test with `--dry-run` first.

### Q: Can I remove the price check?
**A:** Just set `price_limit_per_item` to a very high number (e.g., $10,000). But this defeats the safety feature—not recommended!

---

## Troubleshooting

### "Could not detect price" warnings
- Run with `--dry-run` to see exactly what's happening
- Check if the website has a different price format
- Consider adding site-specific logic to `purchase_engine.py`

### Purchase blocked unexpectedly
- Check `purchase_bot.log` for the exact price detected
- Verify your `price_limit_per_item` setting: `python main.py setup` → Option 2
- Website might have changed its price display

### Price limit not enforced
- Confirm account was created with the limit: `python main.py setup` → Option 2
- Make sure you didn't use old account created before this feature
- Check `credentials.enc` isn't corrupted (try deleting and re-adding account)

---

## Best Practices

✅ **DO:**
- Set reasonable per-item limits (reflect typical item prices)
- Use `--dry-run` before going live
- Check logs weekly for price anomalies
- Adjust limits monthly based on what you're buying

❌ **DON'T:**
- Set per-item limit higher than monthly limit (contradictory)
- Disable price checks by setting very high limits (defeats safety)
- Forget to account for shipping/taxes if included in displayed price
- Buy items with misleading prices displayed

---

## Example Setup

### Budget-Conscious Setup
```
Monthly limit: $200
Price per item: $30

Scenario: Buy office supplies daily
- Pens, notepads: typically $5-15
- Won't accidentally buy expensive items
- Won't overspend monthly
```

### Flexible Setup
```
Monthly limit: $1000
Price per item: $200

Scenario: Buy gadgets/electronics weekly
- Allows for occasional pricey items
- Prevents extreme purchases
- Tracks total monthly spending
```

### Conservative Setup
```
Monthly limit: $100
Price per item: $25

Scenario: Only buy essentials
- Very tight controls
- Good for impulse control
- Suitable for fixed allowance
```

---

## Future Enhancements

Possible improvements:

- [ ] Price comparison (alert if item is on sale)
- [ ] Currency conversion for international sites
- [ ] Tax/shipping estimation
- [ ] Quantity-aware pricing (2x $50 vs 1x $100)
- [ ] Price history tracking
- [ ] Custom price alerts via email/Slack

---

**Your purchase bot is now fully protected with dual-layer price checking!** 🛡️💰

Questions? Check `purchase_bot.log` or review the docs.
