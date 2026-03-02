# import cloudscraper
# from bs4 import BeautifulSoup
# import csv
# import sys

# # ==============================
# # 1️⃣ Provide URL Here
# # ==============================
# url = "https://www.frbservices.org/about/holiday-schedules/#fedcash-holiday"


# def fetch_page(url):
#     """Fetch page using cloudscraper to bypass bot protection."""
#     scraper = cloudscraper.create_scraper()
#     response = scraper.get(url)

#     if response.status_code != 200:
#         print(f"❌ Failed to fetch page: {response.status_code}")
#         sys.exit()

#     return response.text


# def extract_table(soup):
#     """Locate the FedACH holiday table."""
#     table = soup.find("table", class_="table table-striped table-hover")

#     if not table:
#         print("❌ Target table not found.")
#         sys.exit()

#     return table


# def extract_headers(table):
#     """Extract headers safely (handles multi-row thead)."""
#     thead = table.find("thead")

#     if not thead:
#         print("❌ No <thead> found.")
#         sys.exit()

#     header_rows = thead.find_all("tr")

#     final_headers = []

#     # Case: Multi-row header (like your example)
#     if len(header_rows) == 2:
#         first_row = header_rows[0].find_all("th")
#         second_row = header_rows[1].find_all("th")

#         # First column header (Holiday)
#         final_headers.append(first_row[0].get_text(strip=True))

#         # Year (colspan header)
#         year = first_row[1].get_text(strip=True)

#         # Combine year with second row headers
#         for th in second_row:
#             sub_header = th.get_text(strip=True)
#             final_headers.append(f"{year} - {sub_header}")

#     else:
#         # Fallback: single row header
#         for th in header_rows[0].find_all("th"):
#             final_headers.append(th.get_text(strip=True))

#     return final_headers


# def extract_body(table):
#     """Extract table body rows."""
#     tbody = table.find("tbody")

#     if not tbody:
#         print("❌ No <tbody> found.")
#         sys.exit()

#     data = []

#     for row in tbody.find_all("tr"):
#         row_data = []

#         # Holiday name
#         holiday_cell = row.find("th")
#         if holiday_cell:
#             row_data.append(holiday_cell.get_text(strip=True))
#         else:
#             row_data.append("")

#         # Other columns
#         for td in row.find_all("td"):
#             row_data.append(td.get_text(strip=True))

#         data.append(row_data)

#     return data


# def save_to_csv(headers, data):
#     """Save extracted data to CSV."""
#     filename = "fedach_processing_schedule.csv"

#     with open(filename, mode="w", newline="", encoding="utf-8") as file:
#         writer = csv.writer(file)
#         writer.writerow(headers)
#         writer.writerows(data)

#     print(f"✅ CSV successfully created: {filename}")


# # ==============================
# # 🚀 MAIN EXECUTION
# # ==============================

# html = fetch_page(url)
# soup = BeautifulSoup(html, "html.parser")

# table = extract_table(soup)
# headers = extract_headers(table)
# data = extract_body(table)

# save_to_csv(headers, data)




import cloudscraper
from bs4 import BeautifulSoup
import csv
import sys

# ===================================
# 1️⃣ Provide URL
# ===================================
url = "https://www.frbservices.org/about/holiday-schedules/#fedcash-holiday"

# ===================================
# 2️⃣ Fetch Page (Cloudflare Safe)
# ===================================
scraper = cloudscraper.create_scraper()
response = scraper.get(url)

if response.status_code != 200:
    print("❌ Failed to fetch page")
    sys.exit()

soup = BeautifulSoup(response.text, "html.parser")

# ===================================
# 3️⃣ Find the FedACH Table Using Caption
# ===================================
tables = soup.find_all("table", class_="table table-striped table-hover")

target_table = None

for table in tables:
    caption = table.find("caption")
    if caption and "FedACH" in caption.get_text():
        target_table = table
        break

if not target_table:
    print("❌ FedACH table not found")
    sys.exit()

print("✅ FedACH table found")

# ===================================
# 4️⃣ Extract Headers (Multi-row Safe)
# ===================================
thead = target_table.find("thead")
header_rows = thead.find_all("tr")

final_headers = []

if len(header_rows) == 2:
    first_row = header_rows[0].find_all("th")
    second_row = header_rows[1].find_all("th")

    final_headers.append(first_row[0].get_text(strip=True))  # Holiday
    year = first_row[1].get_text(strip=True)

    for th in second_row:
        final_headers.append(f"{year} - {th.get_text(strip=True)}")
else:
    for th in header_rows[0].find_all("th"):
        final_headers.append(th.get_text(strip=True))

# ===================================
# 5️⃣ Extract Body Rows
# ===================================
tbody = target_table.find("tbody")
data = []

for row in tbody.find_all("tr"):
    row_data = []

    holiday = row.find("th").get_text(strip=True)
    row_data.append(holiday)

    for td in row.find_all("td"):
        row_data.append(td.get_text(strip=True))

    data.append(row_data)

# ===================================
# 6️⃣ Save to CSV
# ===================================
with open("fedach_holiday_processing_schedule.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(final_headers)
    writer.writerows(data)

print("✅ CSV created: fedach_holiday_processing_schedule.csv")