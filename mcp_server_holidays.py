import requests
import cloudscraper
import uuid
import json
import re
import os
from bs4 import BeautifulSoup
from datetime import datetime, UTC
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Holiday Rates Server")

# =====================================
# 1️⃣ Canada Holidays (Payments Canada)
# =====================================
def get_canada_holidays():
    """Extract Canada System Closures (Payments Canada)."""
    url = "https://www.payments.ca/system-closure-schedule"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"error": f"Failed to fetch Canada holidays: {response.status_code}"}
        
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if not table or not table.find("tbody"):
            return {"error": "Canada holiday table not found"}

        # Detect Year
        year_match = re.search(r"202[4-9]", soup.get_text())
        detected_year = int(year_match.group(0)) if year_match else datetime.now(UTC).year

        holidays = []
        for row in table.find("tbody").find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                date_raw = cells[1].get_text(strip=True)
                
                try:
                    date_str_with_year = f"{date_raw} {detected_year}"
                    parsed_date = datetime.strptime(date_str_with_year, "%A, %B %d %Y")
                    formatted_date = parsed_date.strftime("%Y-%m-%d")
                    
                    now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
                    holidays.append({
                        "holiday_id": str(uuid.uuid4()),
                        "holiday_country_code": "CAN",
                        "holiday_date": formatted_date,
                        "holiday_month": parsed_date.month,
                        "holiday_year": parsed_date.year,
                        "holiday_day_of_week": parsed_date.strftime("%A"),
                        "holiday_name": name,
                        "is_bank_holiday": True,
                        "holiday_source_url": url,
                        "created_at": now_utc,
                        "updated_at": now_utc
                    })
                except: continue
        return holidays
    except Exception as e:
        return {"error": str(e)}

# =====================================
# 2️⃣ UK Holidays (GOV.UK)
# =====================================
def get_uk_holidays():
    """Extract UK Bank Holidays (GOV.UK)."""
    url = "https://www.gov.uk/bank-holidays"
    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "darwin", "mobile": False})
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            return {"error": f"Failed to fetch UK holidays: {response.status_code}"}
        
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table", class_="gem-c-table")[:3]
        
        holidays = []
        for table in tables:
            caption = table.find("caption")
            region = caption.get_text(strip=True) if caption else "Unknown Region"
            
            for row in table.find("tbody").find_all("tr"):
                time_tag = row.find("time")
                cells = row.find_all("td")
                if time_tag and len(cells) >= 2:
                    iso_date = time_tag.get("datetime")
                    day_of_week = cells[0].get_text(strip=True)
                    name = cells[1].get_text(strip=True)
                    
                    try:
                        parsed_date = datetime.strptime(iso_date, "%Y-%m-%d")
                        now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
                        holidays.append({
                            "holiday_id": str(uuid.uuid4()),
                            "holiday_country_code": "GBR",
                            "holiday_region": region,
                            "holiday_date": iso_date,
                            "holiday_month": parsed_date.month,
                            "holiday_year": parsed_date.year,
                            "holiday_day_of_week": day_of_week,
                            "holiday_name": name,
                            "is_bank_holiday": True,
                            "holiday_source_url": url,
                            "created_at": now_utc,
                            "updated_at": now_utc
                        })
                    except: continue
        return holidays
    except Exception as e:
        return {"error": str(e)}

# =====================================
# 3️⃣ US Holidays (FedACH)
# =====================================
def get_us_holidays():
    """Extract US FedACH Holiday Schedule."""
    url = "https://www.frbservices.org/about/holiday-schedules/#fedcash-holiday"
    scraper = cloudscraper.create_scraper()
    
    month_map = {
        "Jan.": "January", "Feb.": "February", "Mar.": "March", "Apr.": "April",
        "May": "May", "June": "June", "July": "July", "Aug.": "August",
        "Sept.": "September", "Oct.": "October", "Nov.": "November", "Dec.": "December"
    }

    try:
        response = scraper.get(url)
        if response.status_code != 200:
            return {"error": f"Failed to fetch US holidays: {response.status_code}"}
        
        soup = BeautifulSoup(response.text, "html.parser")
        target_table = None
        for table in soup.find_all("table", class_="table table-striped table-hover"):
            caption = table.find("caption")
            if caption and "FedACH" in caption.get_text():
                target_table = table
                break
        
        if not target_table:
            return {"error": "US FedACH table not found"}

        holidays = []
        for row in target_table.find("tbody").find_all("tr"):
            header = row.find("th")
            if not header: continue
            name = header.get_text(strip=True)
            
            for cell in row.find_all("td"):
                date_text = cell.get_text(strip=True)
                if not date_text: continue
                
                clean_date = date_text.split(",")[0] + "," + date_text.split(",")[1] if "," in date_text else date_text
                clean_date = clean_date.strip()
                for short, full in month_map.items():
                    if short in clean_date: clean_date = clean_date.replace(short, full)
                
                try:
                    parsed_date = datetime.strptime(clean_date, "%B %d, %Y")
                    formatted_date = parsed_date.strftime("%Y-%m-%d")
                    now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
                    holidays.append({
                        "holiday_id": str(uuid.uuid4()),
                        "holiday_country_code": "USA",
                        "holiday_date": formatted_date,
                        "holiday_month": parsed_date.month,
                        "holiday_year": parsed_date.year,
                        "holiday_day_of_week": parsed_date.strftime("%A"),
                        "holiday_name": name,
                        "is_bank_holiday": True,
                        "holiday_source_url": url,
                        "created_at": now_utc,
                        "updated_at": now_utc
                    })
                except: continue
        return holidays
    except Exception as e:
        return {"error": str(e)}

# =====================================
# 4️⃣ MCP Tools
# =====================================
@mcp.tool()
def get_canada_holidays_tool():
    """Get Canada system closures (Payments Canada)."""
    return get_canada_holidays()

@mcp.tool()
def get_uk_holidays_tool():
    """Get UK bank holidays (GOV.UK)."""
    return get_uk_holidays()

@mcp.tool()
def get_us_holidays_tool():
    """Get US FedACH holiday schedule."""
    return get_us_holidays()

@mcp.tool()
def get_all_holidays():
    """Get all available holidays for US, Canada, and UK."""
    return {
        "Canada": get_canada_holidays(),
        "UK": get_uk_holidays(),
        "US": get_us_holidays()
    }

if __name__ == "__main__":
    # Test section
    print("Testing Canada Holiday Retrieval...")
    can = get_canada_holidays()
    print(f"Found {len(can)} records." if isinstance(can, list) else can)

    print("\nTesting UK Holiday Retrieval...")
    uk = get_uk_holidays()
    print(f"Found {len(uk)} records." if isinstance(uk, list) else uk)

    print("\nTesting US Holiday Retrieval...")
    us = get_us_holidays()
    print(f"Found {len(us)} records." if isinstance(us, list) else us)

    # Start the server with SSE transport on port 8023
    print("\nStarting Holiday Rates MCP Server on port 8023...")
    mcp.run(transport="sse", host="0.0.0.0", port=8023)
