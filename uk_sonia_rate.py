import requests
import csv
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://www.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp?Travel=NIxAZxSUx&FromSeries=1&ToSeries=50&DAT=RNG&FD=1&FM=Jan&FY=2020&TD=1&TM=Jan&TY=2040&FNY=Y&CSVF=TT&html.x=66&html.y=26&SeriesCodes=IUDSOIA&UsingCodes=Y&Filter=N&title=SONIA%20rate&VPD=Y#notes"

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

tbody = soup.find("tbody")

if tbody is None:
    print("Table body not found.")
else:
    rows = tbody.find_all("tr")

    # Reverse to get latest dates first
    rows = rows[::-1]

    output_rows = []

    for row in rows[:3]:  # Latest 3 records
        cells = row.find_all("td")
        if len(cells) >= 2:
            date = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            output_rows.append([
                "SONIA Rate",
                date,
                value,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            ])

    # Save to CSV
    with open("uk_sonia_rate.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rate Name", "Date", "Value", "Scraped Timestamp"])
        writer.writerows(output_rows)

    print("Data saved to uk_sonia_rate.csv")