import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.fatf-gafi.org/en/publications/High-risk-and-other-monitored-jurisdictions/increased-monitoring-february-2026.html"

# Create scraper that bypasses Cloudflare
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)

response = scraper.get(url)
print("Status:", response.status_code)
# print(len(response.text))
# print(response.text[:2000])

soup = BeautifulSoup(response.text, "html.parser")

results = {}

titles = soup.find_all("h3", class_="cmp-title__text")
print("Titles found:", len(titles))

for title in titles:
    country = title.get_text(strip=True)

    title_div = title.find_parent("div", class_="title")
    if title_div:
        next_text_div = title_div.find_next_sibling("div", class_="text")
        if next_text_div:
            paragraphs = next_text_div.find_all("p")
            reason = " ".join(
                p.get_text(strip=True)
                for p in paragraphs
                if p.get_text(strip=True)
            )
            results[country] = reason

for country, reason in results.items():
    print(f"\nCountry: {country}")
    print(f"Reason: {reason}")
    print("-" * 80)