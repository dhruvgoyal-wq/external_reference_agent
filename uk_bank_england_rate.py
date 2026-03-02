import requests
from bs4 import BeautifulSoup

# If scraping from a live website:
url = "https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Find the featured stat block
featured = soup.find("div", class_="featured-stat")

# Extract Bank Rate
rate = featured.find("span", class_="stat-figure").get_text(strip=True)

# Extract Next Due Date
next_due_text = featured.find("p", class_="stat-caption").get_text(strip=True)

# Clean the date (remove "Next due: ")
next_due_date = next_due_text.replace("Next due:", "").strip()

print("Current Bank Rate:", rate)
print("Next Due Date:", next_due_date)