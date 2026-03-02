import requests
from bs4 import BeautifulSoup
import csv
import sys

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
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# =====================================
# 2️⃣ Make Request with Session
# =====================================
try:
    session = requests.Session()
    response = session.get(url, headers=headers, timeout=15)

    print(f"📡 Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ Failed to fetch page. Status: {response.status_code}")
        print(f"🔍 Response preview: {response.text[:300]}")
        sys.exit()

except requests.exceptions.Timeout:
    print("❌ Request timed out. Check your internet connection.")
    sys.exit()

except requests.exceptions.ConnectionError:
    print("❌ Connection error. Check your internet connection.")
    sys.exit()

# =====================================
# 3️⃣ Parse HTML
# =====================================
soup = BeautifulSoup(response.text, "html.parser")

# =====================================
# 4️⃣ Locate Table
# =====================================
table = soup.find("table")

if not table:
    print("❌ Table not found on page.")
    print(f"🔍 Page preview: {response.text[:500]}")
    sys.exit()

print("✅ Table found!")

# =====================================
# 5️⃣ Extract Headers
# =====================================
thead = table.find("thead")

if not thead:
    print("❌ Table header (thead) not found.")
    sys.exit()

header_cells = thead.find_all("th")
headers_list = [th.get_text(strip=True) for th in header_cells]

print(f"📋 Headers: {headers_list}")

# =====================================
# 6️⃣ Extract Body Rows
# =====================================
tbody = table.find("tbody")

if not tbody:
    print("❌ Table body (tbody) not found.")
    sys.exit()

data = []

for row in tbody.find_all("tr"):
    cells = row.find_all("td")
    if cells:  # Skip empty rows
        row_data = [cell.get_text(strip=True) for cell in cells]
        data.append(row_data)

print(f"📊 Total rows extracted: {len(data)}")

# =====================================
# 7️⃣ Save to CSV
# =====================================
output_file = "canada_federal_holidays.csv"

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers_list)
    writer.writerows(data)

print(f"✅ CSV created: {output_file}")

# =====================================
# 8️⃣ Preview Extracted Data
# =====================================
print("\n📅 Preview of extracted data:")
print(f"{'Federal Holiday':<45} {'Date':<30} {'Date of System Closure'}")
print("-" * 100)

for row in data:
    if len(row) == 3:
        print(f"{row[0]:<45} {row[1]:<30} {row[2]}")