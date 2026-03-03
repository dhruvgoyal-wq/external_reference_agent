import requests
from bs4 import BeautifulSoup
import sys
import json
import uuid
import os
import re
from datetime import datetime

# =====================================
# 1️⃣ URL & Enhanced Headers (UNCHANGED)
# =====================================
url = "https://www.payments.ca/system-closure-schedule"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
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

except requests.exceptions.Timeout:
    print("❌ Request timed out.")
    sys.exit()

except requests.exceptions.ConnectionError:
    print("❌ Connection error.")
    sys.exit()

# =====================================
# 3️⃣ Parse HTML
# =====================================
soup = BeautifulSoup(response.text, "html.parser")

table = soup.find("table")

if not table:
    print("❌ Table not found.")
    sys.exit()

tbody = table.find("tbody")

if not tbody:
    print("❌ Table body not found.")
    sys.exit()

# =====================================
# 4️⃣ Detect Year
# =====================================
page_text = soup.get_text()
year_match = re.search(r"(20\d{2})", page_text)

if not year_match:
    print("❌ Could not detect year.")
    sys.exit()

detected_year = int(year_match.group(1))
print(f"📅 Detected Year: {detected_year}")

# =====================================
# 5️⃣ Extract & Transform
# =====================================
output_data = []

for row in tbody.find_all("tr"):
    cells = row.find_all("td")

    if len(cells) >= 2:
        holiday_name = cells[0].get_text(strip=True)
        holiday_date_raw = cells[1].get_text(strip=True)

        try:
            # Format: Thursday, January 1
            parsed_partial = datetime.strptime(
                holiday_date_raw, "%A, %B %d"
            )

            parsed_date = parsed_partial.replace(year=detected_year)

        except Exception:
            print(f"⚠️ Date parsing failed for: {holiday_date_raw}")
            continue

        now_utc = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        holiday_json = {
            "holiday_id": str(uuid.uuid4()),
            "holiday_country_code": "CAN",
            "holiday_date": parsed_date.strftime("%Y-%m-%d"),
            "holiday_month": parsed_date.month,
            "holiday_year": parsed_date.year,
            "holiday_day_of_week": parsed_date.strftime("%A"),
            "holiday_name": holiday_name,
            "is_bank_holiday": True,
            "holiday_source_url": url,
            "created_at": now_utc,
            "updated_at": now_utc
        }

        output_data.append(holiday_json)

print(f"✅ Records scraped: {len(output_data)}")

# =====================================
# 6️⃣ Simple Append Logic (As Requested)
# =====================================
output_file = "canada_system_closures.json"

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

# =====================================
# 7️⃣ Preview
# =====================================
if output_data:
    print("\n📅 Sample Record:")
    print(json.dumps(output_data[0], indent=4))