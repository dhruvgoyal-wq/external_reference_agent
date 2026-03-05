import requests
from bs4 import BeautifulSoup
import sys
import json
import uuid
import os
import re
from datetime import datetime, UTC

# =====================================
# 1️⃣ URL & Enhanced Headers
# =====================================
url = "https://www.payments.ca/system-closure-schedule"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# =====================================
# 2️⃣ Make Request
# =====================================
try:
    session = requests.Session()
    response = session.get(url, headers=headers, timeout=15)
    print(f"📡 Status Code: {response.status_code}")
    if response.status_code != 200:
        print("❌ Failed to fetch page.")
        sys.exit()

except Exception as e:
    print(f"❌ Request failed: {e}")
    sys.exit()

# =====================================
# 3️⃣ Parse HTML
# =====================================
soup = BeautifulSoup(response.text, "html.parser")
table = soup.find("table")

if not table or not table.find("tbody"):
    print("❌ Holiday table or body not found.")
    sys.exit()

tbody = table.find("tbody")

# =====================================
# 4️⃣ Detect Year (Improved)
# =====================================
# Look specifically for the schedule year in headers or title (usually 2024, 2025, 2026 etc.)
# We ignore "2002" which might appear in some metadata or scripts
page_title = soup.title.string if soup.title else ""
h1_text = soup.find("h1").get_text() if soup.find("h1") else ""

year_match = re.search(r"202[4-9]", h1_text + page_title + soup.get_text())

if not year_match:
    print("❌ Could not detect a valid schedule year (2024-2029).")
    sys.exit()

detected_year = int(year_match.group(0))
print(f"📅 Detected Year: {detected_year}")

# =====================================
# 5️⃣ Load Existing Data for Duplicate Check
# =====================================
output_file = "canada_system_closures.json"
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

# =====================================
# 6️⃣ Extract & Transform
# =====================================
new_records = []

for row in tbody.find_all("tr"):
    cells = row.find_all("td")
    if len(cells) >= 2:
        holiday_name = cells[0].get_text(strip=True)
        holiday_date_raw = cells[1].get_text(strip=True)

        try:
            # Fix deprecation: Prepend year to avoid ambiguity
            # Raw format: "Thursday, January 1"
            date_str_with_year = f"{holiday_date_raw} {detected_year}"
            parsed_date = datetime.strptime(date_str_with_year, "%A, %B %d %Y")
            formatted_date = parsed_date.strftime("%Y-%m-%d")

            # Duplicate Check
            if formatted_date in existing_dates:
                # print(f"⏭️ Skipping duplicate: {formatted_date}")
                continue

        except Exception as e:
            print(f"⚠️ Date parsing failed for '{holiday_date_raw}': {e}")
            continue

        now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        holiday_json = {
            "holiday_id": str(uuid.uuid4()),
            "holiday_country_code": "CAN",
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

# =====================================
# 7️⃣ Save Data
# =====================================
if new_records:
    existing_data.extend(new_records)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4)
    print(f"✅ Added {len(new_records)} new records.")
else:
    print("ℹ️ No new holidays found.")

# =====================================
# 8️⃣ Preview Newest
# =====================================
if new_records:
    print("\n📅 Sample New Record:")
    print(json.dumps(new_records[0], indent=4))