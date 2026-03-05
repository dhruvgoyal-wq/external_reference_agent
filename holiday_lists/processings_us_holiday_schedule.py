import cloudscraper
from bs4 import BeautifulSoup
import sys
import json
import uuid
import os
from datetime import datetime, UTC

# ===================================
# 1️⃣ Provide URL
# ===================================
url = "https://www.frbservices.org/about/holiday-schedules/#fedcash-holiday"

# ===================================
# 2️⃣ Fetch Page (Cloudflare Safe)
# ===================================
scraper = cloudscraper.create_scraper()
response = scraper.get(url)

if response.status_code != 200:
    print("❌ Failed to fetch page")
    sys.exit()

soup = BeautifulSoup(response.text, "html.parser")

# ===================================
# 3️⃣ Locate FedACH Table Using Caption
# ===================================
tables = soup.find_all("table", class_="table table-striped table-hover")

target_table = None

for table in tables:
    caption = table.find("caption")
    if caption and "FedACH" in caption.get_text():
        target_table = table
        break

if not target_table:
    print("❌ FedACH table not found")
    sys.exit()

print("✅ FedACH table found")

# ===================================
# 4️⃣ Month Normalization Map
# ===================================
month_map = {
    "Jan.": "January",
    "Feb.": "February",
    "Mar.": "March",
    "Apr.": "April",
    "May": "May",
    "June": "June",
    "July": "July",
    "Aug.": "August",
    "Sept.": "September",
    "Oct.": "October",
    "Nov.": "November",
    "Dec.": "December"
}

# ===================================
# 5️⃣ Load Existing Data for Duplicate Check
# ===================================
output_file = "us_fedach_holiday_schedule.json"
existing_dates = set()

if os.path.exists(output_file):
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            existing_dates = {item["holiday_date"] for item in existing_data if "holiday_date" in item}
    except Exception as e:
        print(f"⚠️ Could not load existing data: {e}")
        existing_data = []
else:
    existing_data = []

# ===================================
# 6️⃣ Extract Body & Convert to JSON
# ===================================
tbody = target_table.find("tbody")
new_records = []

for row in tbody.find_all("tr"):
    holiday_header = row.find("th")
    if not holiday_header:
        continue

    holiday_name = holiday_header.get_text(strip=True)

    for cell in row.find_all("td"):
        date_text = cell.get_text(strip=True)
        if not date_text:
            continue

        # Clean Date (Remove Time + TZ)
        parts = date_text.split(",")
        if len(parts) >= 2:
            clean_date = parts[0] + "," + parts[1]
        else:
            clean_date = date_text

        clean_date = clean_date.strip()

        # Normalize abbreviated months
        for short, full in month_map.items():
            if short in clean_date:
                clean_date = clean_date.replace(short, full)

        try:
            parsed_date = datetime.strptime(clean_date, "%B %d, %Y")
            formatted_date = parsed_date.strftime("%Y-%m-%d")
            
            # Duplicate check
            if formatted_date in existing_dates:
                continue

        except Exception:
            print(f"⚠️ Date parsing failed: {date_text}")
            continue

        now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        holiday_json = {
            "holiday_id": str(uuid.uuid4()),
            "holiday_country_code": "USA",
            "holiday_date": formatted_date,
            "holiday_month": parsed_date.month,
            "holiday_year": parsed_date.year,
            "holiday_day_of_week": parsed_date.strftime("%A"),
            "holiday_name": holiday_name,
            "is_bank_holiday": True,
            "holiday_source_url": url,
            "created_at": now_utc,
            "updated_at": now_utc
        }
        new_records.append(holiday_json)

# ===================================
# 7️⃣ Save Data
# ===================================
if new_records:
    existing_data.extend(new_records)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4)
    print(f"✅ Added {len(new_records)} new records.")
else:
    print("ℹ️ No new holidays found.")

# ===================================
# 8️⃣ Preview Newest
# ===================================
if new_records:
    print("\n📅 Sample New Record:")
    print(json.dumps(new_records[0], indent=4))