import cloudscraper
from bs4 import BeautifulSoup
import sys
import json
import uuid
import os
from datetime import datetime

# ===================================
# 1️⃣ URL
# ===================================
url = "https://www.gov.uk/bank-holidays"

# ===================================
# 2️⃣ Cloudflare-safe scraper
# ===================================
scraper = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "darwin",
        "mobile": False
    }
)

response = scraper.get(url)
print("Status Code:", response.status_code)

if response.status_code != 200:
    print("❌ Failed to fetch page")
    sys.exit()

soup = BeautifulSoup(response.text, "html.parser")

# ===================================
# 3️⃣ Extract First 3 Holiday Tables
# ===================================
tables = soup.find_all("table", class_="gem-c-table")

if len(tables) < 3:
    print("❌ Less than 3 tables found")
    sys.exit()

tables = tables[:3]

print(f"✅ Extracting first {len(tables)} tables")

output_data = []

# ===================================
# 4️⃣ Extract Data
# ===================================
for table in tables:

    caption = table.find("caption")
    region = caption.get_text(strip=True) if caption else "Unknown Region"

    tbody = table.find("tbody")

    for row in tbody.find_all("tr"):

        time_tag = row.find("time")

        if not time_tag:
            continue

        iso_date = time_tag.get("datetime")  # Already in YYYY-MM-DD
        display_date = time_tag.get_text(strip=True)

        cells = row.find_all("td")

        if len(cells) < 2:
            continue

        day_of_week = cells[0].get_text(strip=True)
        holiday_name = cells[1].get_text(strip=True)

        try:
            parsed_date = datetime.strptime(iso_date, "%Y-%m-%d")
        except Exception:
            print(f"⚠️ Date parsing failed: {iso_date}")
            continue

        now_utc = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        holiday_json = {
            "holiday_id": str(uuid.uuid4()),
            "holiday_country_code": "GBR",
            "holiday_region": region,
            "holiday_date": iso_date,
            "holiday_month": parsed_date.month,
            "holiday_year": parsed_date.year,
            "holiday_day_of_week": day_of_week,
            "holiday_name": holiday_name,
            "is_bank_holiday": True,
            "holiday_source_url": url,
            "created_at": now_utc,
            "updated_at": now_utc
        }

        output_data.append(holiday_json)

print(f"✅ Records scraped: {len(output_data)}")

# ===================================
# 5️⃣ Append to JSON (Simple Logic)
# ===================================
output_file = "uk_bank_holidays.json"

if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
        existing_data.extend(output_data)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4)

else:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)

print("✅ JSON file updated successfully.")

# ===================================
# 6️⃣ Preview
# ===================================
if output_data:
    print("\n📅 Sample Record:")
    print(json.dumps(output_data[0], indent=4))