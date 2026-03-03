import requests
import uuid
import json
import re
from decimal import Decimal
from datetime import datetime, UTC
from bs4 import BeautifulSoup
import os 

url = "https://www.wsj.com/market-data/bonds/moneyrates"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

response = requests.get(url, headers=headers, timeout=10)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# -----------------------------
# Locate Prime Rates table
# -----------------------------
prime_table = None

for table in soup.find_all("table"):
    caption = table.find("caption")
    if caption and "Prime Rates" in caption.text:
        prime_table = table
        break

if prime_table is None:
    raise Exception("Prime Rates table not found. Page likely requires JavaScript.")

# -----------------------------
# Extract U.S. row
# -----------------------------
current_value = None
prev_value = None

for row in prime_table.find_all("tr"):
    cols = row.find_all("td")
    if cols and cols[0].text.strip() == "U.S.":
        latest_text = cols[1].text.strip()
        week_ago_text = cols[2].text.strip()

        match_latest = re.search(r"[-+]?\d*\.\d+|\d+", latest_text)
        match_prev = re.search(r"[-+]?\d*\.\d+|\d+", week_ago_text)

        if match_latest:
            current_value = Decimal(match_latest.group())
        if match_prev:
            prev_value = Decimal(match_prev.group())

        break

if current_value is None:
    raise Exception("Could not extract U.S. prime rate.")

if prev_value is None:
    prev_value = current_value

# -----------------------------
# Compute BPS + Direction
# -----------------------------
current_bps = int(current_value * 100)
change_bps = int((current_value - prev_value) * 100)

if change_bps > 0:
    direction = "HIKE"
elif change_bps < 0:
    direction = "CUT"
else:
    direction = "HOLD"

# -----------------------------
# Build JSON Output
# -----------------------------
now_utc = datetime.now(UTC)

output_json = {
    "rate_entry_id": str(uuid.uuid4()),
    "rate_country_code": "US",
    "rate_type": "prime_rate",
    "rate_authority_name": "wall_street_journal",
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
    "updated_at": now_utc.isoformat()
}

if os.path.exists("us_prime_rate.json"):
    with open("us_prime_rate.json", "r") as f:
        existing_data = json.load(f)
        existing_data.append(output_json)
    with open("us_prime_rate.json", "w") as f:
        json.dump(existing_data, f, indent=2)
else:
    with open("us_prime_rate.json", "w") as f:
        json.dump([output_json], f, indent=2)
