import requests
import uuid
import json
import re
from decimal import Decimal
from datetime import datetime, UTC
from bs4 import BeautifulSoup
import os

url = "https://www.bankofcanada.ca/rates/daily-digest/"

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

interest_rates_table = None

for table in soup.find_all("table"):
    thead = table.find("thead")
    if thead and "Interest Rates" in thead.text:
        interest_rates_table = table
        break

if interest_rates_table is None:
    raise Exception("Interest Rates table not found.")


header_row = interest_rates_table.find("thead").find("tr")
header_cols = header_row.find_all("th")
dates = [col.get_text(strip=True) for col in header_cols[1:-1]]

values = []
rate_name = None

for row in interest_rates_table.find_all("tr"):
    th = row.find("th")
    if th and "Prime rate" in th.text:
        rate_name = th.get_text(strip=True)
        cells = row.find_all("td")
        values = [cell.get_text(strip=True) for cell in cells]
        break

if not values:
    raise Exception("Prime rate values not found.")


clean_values = []

for v in values:
    if not v:
        continue

    match = re.search(r"[-+]?\d*\.\d+|\d+", v)

    if match:
        clean_values.append(Decimal(match.group()))

if len(clean_values) < 1:
    raise Exception("No valid numeric values found.")

current_value = clean_values[0]
prev_value = clean_values[1] if len(clean_values) > 1 else current_value

current_bps = int(current_value * 100)
change_bps = int((current_value - prev_value) * 100)

if change_bps > 0:
    direction = "HIKE"
elif change_bps < 0:
    direction = "CUT"
else:
    direction = "HOLD"

effective_date = dates[0]

now_utc = datetime.now(UTC)

output_json = {
    "rate_entry_id": str(uuid.uuid4()),
    "rate_country_code": "CA",
    "rate_type": "prime_rate",
    "rate_authority_name": "bank_of_canada",
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

if os.path.exists("can_prime_rate.json"):
    with open("can_prime_rate.json", "r") as f:
        existing_data = json.load(f)
        existing_data.append(output_json)
    with open("can_prime_rate.json", "w") as f:
        json.dump(existing_data, f, indent=2)
else:
    with open("can_prime_rate.json", "w") as f:
        json.dump([output_json], f, indent=2)