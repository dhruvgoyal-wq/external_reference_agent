import requests
from bs4 import BeautifulSoup

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

response_us_wsj_prime = requests.get(us_wsj_prime_rate_url, headers=headers, timeout=10)
response_us_wsj_prime.raise_for_status()

soup_us_wsj_prime = BeautifulSoup(response_us_wsj_prime.text, "html.parser")

# Find the Prime Rates table specifically by its caption text
prime_table = None
for table in soup_us_wsj_prime.find_all("table"):
    caption = table.find("caption")
    if caption and "Prime Rates" in caption.text:
        prime_table = table
        break

if prime_table is None:
    print("Prime Rates table not found — page may require JavaScript rendering.")
else:
    us_data = {}
    for row in prime_table.find_all("tr"):
        cols = row.find_all("td")
        if cols and cols[0].text.strip() == "U.S.":
            us_data = {
                "Country": cols[0].text.strip(),
                "Latest":  cols[1].text.strip(),
                "Week Ago": cols[2].text.strip(),
                "52W High": cols[3].text.strip(),
                "52W Low":  cols[4].text.strip(),
            }
            break

    if us_data:
        for key, value in us_data.items():
            print(f"{key}: {value}")
    else:
        print("U.S. row not found in Prime Rates table.")