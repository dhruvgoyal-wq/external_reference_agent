import requests
import csv
from bs4 import BeautifulSoup

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

# Find the Money Market table
money_market_table = None
for table in soup.find_all("table"):
    thead = table.find("thead")
    if thead and "Money Market" in thead.text:
        money_market_table = table
        break

if money_market_table is None:
    print("Money Market table not found.")
else:
    header_row = money_market_table.find("thead").find("tr")
    header_cols = header_row.find_all("th")

    # Extract dates (skip first column and last "+/-" column)
    dates = [col.get_text(strip=True) for col in header_cols[1:-1]]

    output_rows = []

    for row in money_market_table.find_all("tr"):
        th = row.find("th")
        if th and "Overnight Money Market Financing Rate" in th.text:
            cells = row.find_all("td")
            rate_name = th.get_text(strip=True)

            for date, cell in zip(dates, cells):
                value = cell.get_text(strip=True)
                output_rows.append([rate_name, date, value])

            break

    # Save to CSV
    with open("can_overnight_rate.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rate Name", "Date", "Value"])  # Header row
        writer.writerows(output_rows)

    print("Data saved to can_overnight_rate.csv")