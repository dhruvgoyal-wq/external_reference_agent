import requests
import csv
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Find the featured stat block
featured = soup.find("div", class_="featured-stat")

if featured is None:
    print("Featured stat block not found.")
else:
    # Extract Bank Rate
    rate = featured.find("span", class_="stat-figure").get_text(strip=True)

    # Extract Next Due Date
    next_due_text = featured.find("p", class_="stat-caption").get_text(strip=True)
    next_due_date = next_due_text.replace("Next due:", "").strip()

    # Save to CSV
    with open("uk_bank_england_rate.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Source", "Current Bank Rate", "Next Due Date", "Scraped Timestamp"])
        writer.writerow([
            "Bank of England",
            rate,
            next_due_date,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        ])

    print("Data saved to uk_bank_england_rate.csv")