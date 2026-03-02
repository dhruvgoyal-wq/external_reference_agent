import requests
from bs4 import BeautifulSoup
import csv

# 1️⃣ Provide the URL
url = "https://www.frbservices.org/about/holiday-schedules/#fedcash-holiday"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    print("Failed to fetch page:", response.status_code)
    exit()

soup = BeautifulSoup(response.text, "html.parser")

# 2️⃣ Extract column headers from <thead>
thead = soup.find("thead")
header_columns = []

if thead:
    header_row = thead.find("tr")
    for th in header_row.find_all("th"):
        header_columns.append(th.get_text(strip=True))
else:
    print("No thead found.")
    exit()

# 3️⃣ Extract data rows from <tbody>
tbody = soup.find("tbody")

if not tbody:
    print("No tbody found.")
    exit()

# 4️⃣ Write to CSV
with open("holidays.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    # Write dynamic headers
    writer.writerow(header_columns)

    # Extract each row
    for row in tbody.find_all("tr"):
        row_data = []

        # Holiday name from <th>
        holiday_name = row.find("th").get_text(strip=True)
        row_data.append(holiday_name)

        # Dates from <td>
        for td in row.find_all("td"):
            row_data.append(td.get_text(strip=True))

        writer.writerow(row_data)

print("✅ holidays.csv created successfully!")