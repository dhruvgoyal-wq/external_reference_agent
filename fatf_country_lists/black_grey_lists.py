import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.fatf-gafi.org/en/countries/black-and-grey-lists.html"

scraper = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "windows",
        "mobile": False
    }
)

response = scraper.get(url)
print("Status Code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

results = []

# Target the specific list by its ID
target_list = soup.find("ul", id="list-61c19274bd")
#id="list-61c19274bd" is for High-Risk Jurisdictions subject to a Call for Action

if target_list:
    items = target_list.find_all("li", class_="cmp-list__item")
    print("Items found:", len(items))

    for item in items:
        title_tag = item.find("span", class_="cmp-list__item-title")
        link_tag = item.find("a", class_="cmp-list__item-link")

        if title_tag and link_tag:
            country = title_tag.get_text(strip=True)
            link = "https://www.fatf-gafi.org" + link_tag["href"]
            results.append({
                "Country": country,
                "Detail_URL": link
            })
else:
    print("Target list not found!")


df = pd.DataFrame(results)
df.to_csv("black-grey-lists/high-risk-jurisdictions.csv", index=False)

results = []

# list-6fd939583d is for Jurisdictions under Increased Monitoring
target_list_v2 = soup.find("ul", id="list-6fd939583d")

if target_list_v2:
    items = target_list_v2.find_all("li", class_="cmp-list__item")
    print("Items found:", len(items))

    for item in items:
        title_tag = item.find("span", class_="cmp-list__item-title")
        link_tag = item.find("a", class_="cmp-list__item-link")

        if title_tag and link_tag:
            country = title_tag.get_text(strip=True)
            link = "https://www.fatf-gafi.org" + link_tag["href"]
            results.append({
                "Country": country,
                "Detail_URL": link
            })
else:
    print("Target list not found!")


df = pd.DataFrame(results)
df.to_csv("black-grey-lists/jurisdictions-under-increased-monitoring.csv", index=False)