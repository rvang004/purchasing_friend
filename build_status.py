"""
Parses purchase_bot.log and writes docs/status.json for the GitHub Pages dashboard.
Called by GitHub Actions after every bot run.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


LOG_FILE    = Path("purchase_bot.log")
STATUS_FILE = Path("docs/status.json")
MAX_RUNS    = 200  # keep last N runs in the JSON


def parse_log() -> list[dict]:
    """Extract individual purchase results from the log file."""
    if not LOG_FILE.exists():
        return []

    runs   = []
    run    = None

    ts_pat    = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
    start_pat = re.compile(r"Starting purchase for task ([\w\d_]+) using account ([\w\d_]+)")
    price_pat = re.compile(r"Detected item price: \$?([\d.]+)")
    qty_pat   = re.compile(r"Quantity set to (\d+)")
    qty_low   = re.compile(r"site only allows (\d+)")
    url_pat   = re.compile(r"Product page loaded: (https?://\S+)")
    ok_pat    = re.compile(r"Purchase successful for [\w\d_]+ .* qty: (\d+)")
    fail_pat  = re.compile(r"Purchase failed: (.+)")
    block_pat = re.compile(r"price \(\$([\d.]+)\) exceeds limit")

    for line in LOG_FILE.read_text(errors="ignore").splitlines():
        m_ts = ts_pat.match(line)
        if not m_ts:
            continue
        ts  = m_ts.group(1)
        msg = line[len(ts):].strip(" -INFO WARNINGEROR")

        if m := start_pat.search(msg):
            run = {
                "timestamp":   ts,
                "task_id":     m.group(1),
                "account_id":  m.group(2),
                "product_url": None,
                "item_price":  None,
                "quantity":    None,
                "success":     False,
                "error":       None,
            }
            runs.append(run)

        if run is None:
            continue

        if m := url_pat.search(msg):
            run["product_url"] = m.group(1)
        if m := price_pat.search(msg):
            run["item_price"] = float(m.group(1))
        if m := qty_pat.search(msg):
            run["quantity"] = int(m.group(1))
        if m := qty_low.search(msg):
            run["quantity"] = int(m.group(1))
        if ok_pat.search(msg):
            run["success"] = True
            run["error"]   = None
        if m := fail_pat.search(msg):
            run["error"] = m.group(1)
        if m := block_pat.search(msg):
            run["error"] = f"Price ${m.group(1)} exceeded limit"

    # newest first
    runs.reverse()
    return runs[:MAX_RUNS]


def main():
    existing = {}
    if STATUS_FILE.exists():
        try:
            existing = json.loads(STATUS_FILE.read_text())
        except json.JSONDecodeError:
            pass
    runs = parse_log()
    STATUS_FILE.parent.mkdir(exist_ok=True)
    STATUS_FILE.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs": runs,
    }, indent=2))
    print(f"[OK] status.json updated -- {len(runs)} run(s) recorded", file=sys.stdout)


if __name__ == "__main__":
    main()
