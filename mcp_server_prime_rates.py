import requests
import uuid
import json
import re
from decimal import Decimal
from datetime import datetime, UTC
from bs4 import BeautifulSoup
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Rates Server")

def get_us_prime_rate():
    url = "https://www.wsj.com/market-data/bonds/moneyrates"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    prime_table = None
    for table in soup.find_all("table"):
        caption = table.find("caption")
        if caption and "Prime Rates" in caption.text:
            prime_table = table
            break
    if not prime_table:
        return {"error": "Prime Rates table not found"}
    
    current_value = None
    prev_value = None
    for row in prime_table.find_all("tr"):
        cols = row.find_all("td")
        if cols and cols[0].text.strip() == "U.S.":
            current_value = Decimal(re.search(r"[-+]?\d*\.\d+|\d+", cols[1].text.strip()).group())
            prev_value = Decimal(re.search(r"[-+]?\d*\.\d+|\d+", cols[2].text.strip()).group())
            break
    
    if current_value is None:
        return {"error": "Could not extract U.S. prime rate"}
    
    change_bps = int((current_value - prev_value) * 100)
    direction = "HIKE" if change_bps > 0 else "CUT" if change_bps < 0 else "HOLD"
    
    now_utc = datetime.now(UTC).isoformat()
    return {
        "rate_entry_id": str(uuid.uuid4()),
        "rate_country_code": "US",
        "rate_type": "prime_rate",
        "rate_authority_name": "wall_street_journal",
        "rate_effective_date": datetime.now(UTC).date().isoformat(),
        "rate_expiry_date": None,
        "is_rate_current": True,
        "rate_current_value_pct": float(round(current_value, 4)),
        "rate_current_value_bps": int(current_value * 100),
        "rate_prev_value_pct": float(round(prev_value, 4)),
        "rate_change_bps": change_bps,
        "rate_direction": direction,
        "rate_source_url": url,
        "created_at": now_utc,
        "updated_at": now_utc
    }

def get_can_prime_rate():
    url = "https://www.bankofcanada.ca/rates/daily-digest/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    interest_rates_table = None
    for table in soup.find_all("table"):
        thead = table.find("thead")
        if thead and "Interest Rates" in thead.text:
            interest_rates_table = table
            break
    if not interest_rates_table:
        return {"error": "Interest Rates table not found"}
    
    header_cols = interest_rates_table.find("thead").find("tr").find_all("th")
    dates = [col.get_text(strip=True) for col in header_cols[1:-1]]
    
    values = []
    tbody = interest_rates_table.find("tbody")
    if not tbody:
        return {"error": "tbody not found"}
        
    for row in tbody.find_all("tr"):
        th = row.find("th")
        if th and "Prime rate" in th.text:
            cells = row.find_all("td")
            values = [cell.get_text(strip=True) for cell in cells[:-1]]
            break
            
    clean_values = []
    for v in values:
        match = re.search(r"[-+]?\d*\.\d+|\d+", v)
        if match:
            clean_values.append(Decimal(match.group()))
            
    if not clean_values:
        return {"error": "Prime rate values not found"}
    
    i = len(clean_values) - 1
    current_value = clean_values[i]
    prev_value = clean_values[i-1] if i > 0 else current_value
    
    change_bps = int((current_value - prev_value) * 100)
    direction = "HIKE" if change_bps > 0 else "CUT" if change_bps < 0 else "HOLD"
    
    now_utc = datetime.now(UTC).isoformat()
    return {
        "rate_entry_id": str(uuid.uuid4()),
        "rate_country_code": "CA",
        "rate_type": "prime_rate",
        "rate_authority_name": "bank_of_canada",
        "rate_effective_date": dates[i] if i < len(dates) else "Unknown",
        "rate_expiry_date": None,
        "is_rate_current": True,
        "rate_current_value_pct": float(round(current_value, 4)),
        "rate_current_value_bps": int(current_value * 100),
        "rate_prev_value_pct": float(round(prev_value, 4)),
        "rate_change_bps": change_bps,
        "rate_direction": direction,
        "rate_source_url": url,
        "created_at": now_utc,
        "updated_at": now_utc
    }

def get_uk_sonia_rate():
    url = "https://www.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp?Travel=NIxAZxSUx&FromSeries=1&ToSeries=50&DAT=RNG&FD=1&FM=Jan&FY=2020&TD=1&TM=Jan&TY=2040&FNY=Y&CSVF=TT&html.x=66&html.y=26&SeriesCodes=IUDSOIA&UsingCodes=Y&Filter=N&title=SONIA%20rate"
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
    if not tbody:
        return {"error": "Table body not found"}
    
    rows = tbody.find_all("tr")[::-1]
    clean_values = []
    clean_dates = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            date_text = cells[0].get_text(strip=True)
            value_text = cells[1].get_text(strip=True)
            match = re.search(r"[-+]?\d*\.\d+|\d+", value_text)
            if match:
                clean_dates.append(date_text)
                clean_values.append(Decimal(match.group()))
        if len(clean_values) >= 2:
            break
            
    if not clean_values:
        return {"error": "SONIA values not found"}
    
    current_value = clean_values[0]
    prev_value = clean_values[1] if len(clean_values) > 1 else current_value
    change_bps = int((current_value - prev_value) * 100)
    direction = "HIKE" if change_bps > 0 else "CUT" if change_bps < 0 else "HOLD"
    
    now_utc = datetime.now(UTC).isoformat()
    return {
        "rate_entry_id": str(uuid.uuid4()),
        "rate_country_code": "GB",
        "rate_type": "sonia_rate",
        "rate_authority_name": "bank_of_england",
        "rate_effective_date": clean_dates[0],
        "rate_expiry_date": None,
        "is_rate_current": True,
        "rate_current_value_pct": float(round(current_value, 4)),
        "rate_current_value_bps": int(current_value * 100),
        "rate_prev_value_pct": float(round(prev_value, 4)),
        "rate_change_bps": change_bps,
        "rate_direction": direction,
        "rate_source_url": url,
        "created_at": now_utc,
        "updated_at": now_utc
    }

@mcp.tool()
def get_all_rates():
    """Get prime rates for US, Canada, and UK SONIA rate."""
    return {
        "US": get_us_prime_rate(),
        "CA": get_can_prime_rate(),
        "UK": get_uk_sonia_rate()
    }

if __name__ == "__main__":
    # Check whether all the functions are working or not 
    print("Testing US Rate Retrieval:")
    print(json.dumps(get_us_prime_rate(), indent=2))
    print("\nTesting Canada Rate Retrieval:")
    print(json.dumps(get_can_prime_rate(), indent=2))
    print("\nTesting UK Rate Retrieval:")
    print(json.dumps(get_uk_sonia_rate(), indent=2))

    # Start the server with SSE transport on port 8020
    mcp.run(transport="sse", host="0.0.0.0", port=8020)
