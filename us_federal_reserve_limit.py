import requests
import uuid
import json
import re
from decimal import Decimal
from datetime import datetime, UTC
from bs4 import BeautifulSoup
import os

url = "https://fred.stlouisfed.org/series/DFEDTARL"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers, timeout=10)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# -----------------------------
# Extract Date and Value
# -----------------------------
date_tag = soup.find("span", class_="series-meta-value")
value_tag = soup.find("span", class_="series-meta-observation-value")

if not (date_tag and value_tag):
    raise Exception("Could not find rate data on page.")

date_text = date_tag.text.strip(":").strip()
value_text = value_tag.text.strip()

# -----------------------------
# Clean Numeric Value Safely
# -----------------------------
match = re.search(r"[-+]?\d*\.\d+|\d+", value_text)
if not match:
    raise Exception("Could not extract numeric Fed rate.")

current_value = Decimal(match.group())

# Since FRED page only shows latest observation,
# we treat previous as same (true delta requires DB comparison)
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
    "rate_country_code": "US",
    "rate_type": "federal_funds_target_upper",
    "rate_authority_name": "federal_reserve",
    "rate_effective_date": date_text,
    "rate_expiry_date": None,
    "is_rate_current": True,
    "rate_current_value_pct": float(round(current_value, 4)),
    "rate_current_value_bps": current_bps,
    "rate_prev_value_pct": float(round(prev_value, 4)),
    "rate_change_bps": change_bps,
    "rate_direction": direction,
    "rate_source_url": url,
    "created_at": now_utc.isoformat(),
    "updated_at": now_utc.isoformat()
}

if os.path.exists("us_federal_reserve_limit.json"):
    with open("us_federal_reserve_limit.json", "r") as f:
        existing_data = json.load(f)
        existing_data.append(output_json)
    with open("us_federal_reserve_limit.json", "w") as f:
        json.dump(existing_data, f, indent=2)
else:
    with open("us_federal_reserve_limit.json", "w") as f:
        json.dump([output_json], f, indent=2)
