import requests
import uuid
import json
import re
from decimal import Decimal
from datetime import datetime, UTC
from bs4 import BeautifulSoup
import os

url = "https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers, timeout=10)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# -----------------------------
# Find Featured Stat Block
# -----------------------------
featured = soup.find("div", class_="featured-stat")

if featured is None:
    raise Exception("Featured stat block not found.")

# -----------------------------
# Extract Current Bank Rate
# -----------------------------
rate_text = featured.find("span", class_="stat-figure").get_text(strip=True)

# Clean numeric value safely
match = re.search(r"[-+]?\d*\.\d+|\d+", rate_text)
if not match:
    raise Exception("Could not extract numeric Bank Rate.")

current_value = Decimal(match.group())

# -----------------------------
# Extract Next Due Date (optional metadata)
# -----------------------------
caption = featured.find("p", class_="stat-caption").get_text(strip=True)
next_due_date = caption.replace("Next due:", "").strip()

# -----------------------------
# Since this page shows only current rate,
# we treat previous value as same (HOLD)
# -----------------------------
prev_value = current_value

current_bps = int(current_value * 100)
change_bps = 0
direction = "HOLD"

# -----------------------------
# Build JSON Output
# -----------------------------
now_utc = datetime.now(UTC)

output_json = {
    "rate_entry_id": str(uuid.uuid4()),
    "rate_country_code": "GB",
    "rate_type": "bank_rate",
    "rate_authority_name": "bank_of_england",
    "rate_effective_date": now_utc.date().isoformat(),
    "rate_expiry_date": None,
    "is_rate_current": True,
    "rate_current_value_pct": float(round(current_value, 4)),
    "rate_current_value_bps": current_bps,
    "rate_prev_value_pct": float(round(prev_value, 4)),
    "rate_change_bps": change_bps,
    "rate_direction": direction,
    "rate_source_url": url,
    "created_at": now_utc.isoformat(),
    "updated_at": now_utc.isoformat(),
    "next_policy_due_date_note": next_due_date  # optional metadata
}

if os.path.exists("uk_bank_england_rate.json"):
    with open("uk_bank_england_rate.json", "r") as f:
        existing_data = json.load(f)
        existing_data.append(output_json)
    with open("uk_bank_england_rate.json", "w") as f:
        json.dump(existing_data, f, indent=2)
else:
    with open("uk_bank_england_rate.json", "w") as f:
        json.dump([output_json], f, indent=2)