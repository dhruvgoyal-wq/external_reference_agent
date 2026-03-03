import requests
import uuid
import json
import re
from decimal import Decimal
from datetime import datetime, UTC
from bs4 import BeautifulSoup
import os

url = "https://www.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp?Travel=NIxAZxSUx&FromSeries=1&ToSeries=50&DAT=RNG&FD=1&FM=Jan&FY=2020&TD=1&TM=Jan&TY=2040&FNY=Y&CSVF=TT&html.x=66&html.y=26&SeriesCodes=IUDSOIA&UsingCodes=Y&Filter=N&title=SONIA%20rate&VPD=Y#notes"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

response = requests.get(url, headers=headers, timeout=10)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

tbody = soup.find("tbody")
if tbody is None:
    raise Exception("Table body not found.")

rows = tbody.find_all("tr")

# Reverse so latest dates come first
rows = rows[::-1]

clean_values = []
clean_dates = []

for row in rows:
    cells = row.find_all("td")
    if len(cells) < 2:
        continue

    date_text = cells[0].get_text(strip=True)
    value_text = cells[1].get_text(strip=True)

    match = re.search(r"[-+]?\d*\.\d+|\d+", value_text)
    if match:
        clean_dates.append(date_text)
        clean_values.append(Decimal(match.group()))

    if len(clean_values) >= 2:
        break  # we only need current + previous

if len(clean_values) < 1:
    raise Exception("No valid SONIA values found.")

current_value = clean_values[0]
prev_value = clean_values[1] if len(clean_values) > 1 else current_value

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
# Effective Date
# -----------------------------
effective_date = clean_dates[0]

# -----------------------------
# Build JSON Output
# -----------------------------
now_utc = datetime.now(UTC)

output_json = {
    "rate_entry_id": str(uuid.uuid4()),
    "rate_country_code": "GB",
    "rate_type": "sonia_rate",
    "rate_authority_name": "bank_of_england",
    "rate_effective_date": effective_date,
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

if os.path.exists("uk_sonia_rate.json"):
    with open("uk_sonia_rate.json", "r") as f:
        existing_data = json.load(f)
        existing_data.append(output_json)
    with open("uk_sonia_rate.json", "w") as f:
        json.dump(existing_data, f, indent=2)
else:
    with open("uk_sonia_rate.json", "w") as f:
        json.dump([output_json], f, indent=2)