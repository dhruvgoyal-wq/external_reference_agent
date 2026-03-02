import cloudscraper
from bs4 import BeautifulSoup
import csv
import sys

url = "https://www.gov.uk/bank-holidays"

# Create Cloudflare-safe scraper
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

# Get all holiday tables
tables = soup.find_all("table", class_="gem-c-table")

if len(tables) < 3:
    print("❌ Less than 3 tables found")
    sys.exit()

# Only first 3 tables
tables = tables[:3]

print(f"✅ Extracting first {len(tables)} tables")

all_data = []

for table in tables:

    # Extract year from caption
    caption = table.find("caption")
    year = caption.get_text(strip=True).split()[-1] if caption else "Unknown"

    tbody = table.find("tbody")

    for row in tbody.find_all("tr"):

        # Date column (inside <th><time>)
        time_tag = row.find("time")

        iso_date = time_tag["datetime"] if time_tag else ""
        display_date = time_tag.get_text(strip=True) if time_tag else ""

        cells = row.find_all("td")

        if len(cells) >= 2:
            day_of_week = cells[0].get_text(strip=True)
            holiday_name = cells[1].get_text(strip=True)

            all_data.append([
                year,
                iso_date,
                display_date,
                day_of_week,
                holiday_name
            ])

# Save to CSV
with open("uk_first_3_tables.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Year",
        "ISO_Date",
        "Display_Date",
        "Day_of_Week",
        "Bank_Holiday"
    ])
    writer.writerows(all_data)

print("✅ CSV created successfully")
print("Total records:", len(all_data))