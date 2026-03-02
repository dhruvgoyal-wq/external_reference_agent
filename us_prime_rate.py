import requests
import csv
from bs4 import BeautifulSoup
from datetime import datetime

us_wsj_prime_rate_url = "https://www.wsj.com/market-data/bonds/moneyrates"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

response = requests.get(us_wsj_prime_rate_url, headers=headers, timeout=10)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Find Prime Rates table
prime_table = None
for table in soup.find_all("table"):
    caption = table.find("caption")
    if caption and "Prime Rates" in caption.text:
        prime_table = table
        break

if prime_table is None:
    print("Prime Rates table not found — page may require JavaScript rendering.")
else:
    us_data = None

    for row in prime_table.find_all("tr"):
        cols = row.find_all("td")
        if cols and cols[0].text.strip() == "U.S.":
            us_data = {
                "Country": cols[0].text.strip(),
                "Latest": cols[1].text.strip(),
                "Week Ago": cols[2].text.strip(),
                "52W High": cols[3].text.strip(),
                "52W Low": cols[4].text.strip(),
                "Scraped Timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
            break

    if us_data:
        with open("us_prime_rate.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=us_data.keys())
            writer.writeheader()
            writer.writerow(us_data)

        print("Data saved to us_prime_rate.csv")
    else:
        print("U.S. row not found in Prime Rates table.")