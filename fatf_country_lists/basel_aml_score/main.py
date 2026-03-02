import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# =====================================
# 1️⃣ Setup Headless Chrome
# =====================================
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(options=options)

# =====================================
# 2️⃣ Load the Page
# =====================================
url = "https://index.baselgovernance.org/ranking"
print(f"🌐 Opening: {url}")
driver.get(url)

# =====================================
# 3️⃣ Wait for Table to Render
# =====================================
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "tbody"))
    )
    print("✅ Table detected, waiting for full data load...")
    time.sleep(3)  # Extra wait for all rows to populate via JS
except Exception as e:
    print(f"❌ Table not found within timeout: {e}")
    driver.quit()
    exit()

# =====================================
# 4️⃣ Scroll to Load All Rows
#    (In case of lazy loading)
# =====================================
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

print("✅ Page fully scrolled.")

# =====================================
# 5️⃣ Parse with BeautifulSoup
# =====================================
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

table = soup.find("table")

if not table:
    print("❌ Table not found in parsed HTML.")
    exit()

# =====================================
# 6️⃣ Extract Headers
# =====================================
thead = table.find("thead")
headers_list = []

if thead:
    for th in thead.find_all("th"):
        # Get only the text from <span>, ignoring SVG icon text
        span = th.find("span")
        headers_list.append(span.get_text(strip=True) if span else th.get_text(strip=True))

print(f"📋 Headers: {headers_list}")

# =====================================
# 7️⃣ Extract All Body Rows
# =====================================
tbody = table.find("tbody")
data = []

for row in tbody.find_all("tr"):
    cells = row.find_all("td")
    if not cells:
        continue

    row_data = []
    for i, cell in enumerate(cells):
        # Score column has nested spans — extract only the number
        if i == 2:
            score_span = cell.find_all("span")
            # Last span contains the score value
            score = score_span[-1].get_text(strip=True) if score_span else cell.get_text(strip=True)
            row_data.append(score)
        else:
            row_data.append(cell.get_text(strip=True))

    data.append(row_data)

print(f"📊 Total rows extracted: {len(data)}")

# =====================================
# 8️⃣ Save to CSV
# =====================================
output_file = "basel_governance_ranking.csv"

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers_list)
    writer.writerows(data)

print(f"✅ CSV saved: {output_file}")

# =====================================
# 9️⃣ Preview First 10 Rows
# =====================================
print(f"\n{'Rank':<8} {'Jurisdiction':<45} {'Overall Score'}")
print("-" * 65)
for row in data[:10]:
    if len(row) == 3:
        print(f"{row[0]:<8} {row[1]:<45} {row[2]}")