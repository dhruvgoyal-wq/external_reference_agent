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
    raise Exception("Interest Rates table not found")

header_cols = interest_rates_table.find("thead").find("tr").find_all("th")
dates = [col.get_text(strip=True) for col in header_cols[1:-1]]

values = []
for row in interest_rates_table.find("tbody").find_all("tr"):
    th = row.find("th")
    if th and "Prime rate" in th.text:
        cells = row.find_all("td")
        values = [cell.get_text(strip=True) for cell in cells[:-1]]
        break


clean_values = []
for v in values:
    match = re.search(r"[-+]?\d*\.\d+|\d+", v)
    if match:
        clean_values.append(Decimal(match.group()))


now_utc = datetime.now(UTC)

new_records = []

for i, date in enumerate(dates):

    current_value = clean_values[i]
    prev_value = clean_values[i-1] if i > 0 else current_value

    current_bps = int(current_value * 100)
    change_bps = int((current_value - prev_value) * 100)

    if change_bps > 0:
        direction = "HIKE"
    elif change_bps < 0:
        direction = "CUT"
    else:
        direction = "HOLD"

    record = {
        "rate_entry_id": str(uuid.uuid4()),
        "rate_country_code": "CA",
        "rate_type": "prime_rate",
        "rate_authority_name": "bank_of_canada",
        "rate_effective_date": date,
        "rate_expiry_date": None,
        "is_rate_current": i == len(dates) - 1,
        "rate_current_value_pct": float(round(current_value, 4)),
        "rate_current_value_bps": current_bps,
        "rate_prev_value_pct": float(round(prev_value, 4)),
        "rate_change_bps": change_bps,
        "rate_direction": direction,
        "rate_source_url": url,
        "created_at": now_utc.isoformat(),
        "updated_at": now_utc.isoformat()
    }

    new_records.append(record)


file_name = "can_prime_rate.json"

if os.path.exists(file_name):
    with open(file_name, "r") as f:
        existing_data = json.load(f)
else:
    existing_data = []


# Create set of existing dates
existing_dates = {item["rate_effective_date"] for item in existing_data}


# Filter only new records
records_to_insert = [
    r for r in new_records
    if r["rate_effective_date"] not in existing_dates
]


# Append only new records
existing_data.extend(records_to_insert)


# Save file
with open(file_name, "w") as f:
    json.dump(existing_data, f, indent=2)


print("New records inserted:", len(records_to_insert))