import requests
import csv
from bs4 import BeautifulSoup
from datetime import datetime

us_federal_reserve_rate_url = "https://fred.stlouisfed.org/series/DFEDTARL"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(us_federal_reserve_rate_url, headers=headers)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Extract date and value
date_tag = soup.find("span", class_="series-meta-value")
value_tag = soup.find("span", class_="series-meta-observation-value")

if date_tag and value_tag:
    date = date_tag.text.strip(":").strip()
    value = value_tag.text.strip()

    # Save to CSV
    with open("us_federal_reserve_limit.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Series", "Date", "Value", "Scraped Timestamp"])
        writer.writerow([
            "DFEDTARL",
            date,
            value,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        ])

    print("Data saved to us_federal_reserve_limit.csv")
else:
    print("Could not find rate data on page.")