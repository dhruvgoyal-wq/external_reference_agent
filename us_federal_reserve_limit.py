import requests
from bs4 import BeautifulSoup

us_federal_reserve_rate_url = "https://fred.stlouisfed.org/series/DFEDTARL"


response = requests.get(us_federal_reserve_rate_url)

soup = BeautifulSoup(response.text, "html.parser")

date = soup.find("span", class_="series-meta-value").text.strip(":")
value = soup.find("span", class_="series-meta-observation-value").text

print(date , value)