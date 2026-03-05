import requests
import uuid
import json
import re
from decimal import Decimal
from datetime import datetime, UTC
from bs4 import BeautifulSoup
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Overnight Rates Server")

def get_us_fed_limit():
    """Extract US Federal Funds Target Range - Upper Limit from FRED."""
    url = "https://fred.stlouisfed.org/series/DFEDTARL"
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
    
    date_tag = soup.find("span", class_="series-meta-value")
    value_tag = soup.find("span", class_="series-meta-observation-value")
    
    if not (date_tag and value_tag):
        return {"error": "Could not find rate data on FRED page."}
    
    date_text = date_tag.text.strip(":").strip()
    value_text = value_tag.text.strip()
    
    match = re.search(r"[-+]?\d*\.\d+|\d+", value_text)
    if not match:
        return {"error": "Could not extract numeric Fed rate."}
    
    current_value = Decimal(match.group())
    prev_value = current_value  # Standalone logic defaults to HOLD
    
    now_utc = datetime.now(UTC).isoformat()
    return {
        "rate_entry_id": str(uuid.uuid4()),
        "rate_country_code": "US",
        "rate_type": "federal_funds_target_upper",
        "rate_authority_name": "federal_reserve",
        "rate_effective_date": date_text,
        "rate_expiry_date": None,
        "is_rate_current": True,
        "rate_current_value_pct": float(round(current_value, 4)),
        "rate_current_value_bps": int(current_value * 100),
        "rate_prev_value_pct": float(round(prev_value, 4)),
        "rate_change_bps": 0,
        "rate_direction": "HOLD",
        "rate_source_url": url,
        "created_at": now_utc,
        "updated_at": now_utc
    }

def get_can_overnight_rate():
    """Extract Canada Overnight Money Market Financing Rate from Bank of Canada."""
    url = "https://www.bankofcanada.ca/rates/daily-digest/"
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
    
    money_market_table = None
    for table in soup.find_all("table"):
        thead = table.find("thead")
        if thead and "Money Market" in thead.text:
            money_market_table = table
            break
            
    if money_market_table is None:
        return {"error": "Money Market table not found."}
    
    header_row = money_market_table.find("thead").find("tr")
    header_cols = header_row.find_all("th")
    dates = [col.get_text(strip=True) for col in header_cols[1:-1]]
    
    values = []
    for row in money_market_table.find_all("tr"):
        th = row.find("th")
        if th and "Overnight Money Market Financing Rate" in th.text:
            cells = row.find_all("td")
            values = [cell.get_text(strip=True) for cell in cells]
            break
            
    if not values:
        return {"error": "Rate values not found."}
        
    clean_values = []
    for v in values:
        if not v: continue
        v_clean = v.replace("%", "").replace(",", "").strip()
        if v_clean in ["", "-", "–", "--"]: continue
        try:
            clean_values.append(Decimal(v_clean))
        except: continue
            
    if not clean_values:
        return {"error": "No valid numeric values found."}
        
    current_value = clean_values[0]
    prev_value = clean_values[1] if len(clean_values) > 1 else current_value
    
    change_bps = int(round((current_value - prev_value) * 100))
    direction = "HIKE" if change_bps > 0 else "CUT" if change_bps < 0 else "HOLD"
    
    effective_date = dates[0] if dates else "Unknown"
    
    now_utc = datetime.now(UTC).isoformat()
    return {
        "rate_entry_id": str(uuid.uuid4()),
        "rate_country_code": "CA",
        "rate_type": "overnight_money_market_financing_rate",
        "rate_authority_name": "bank_of_canada",
        "rate_effective_date": effective_date,
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

def get_uk_bank_rate():
    """Extract UK Bank Rate from Bank of England."""
    url = "https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate"
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
    
    featured = soup.find("div", class_="featured-stat")
    if featured is None:
        return {"error": "Featured stat block not found."}
        
    rate_text = featured.find("span", class_="stat-figure").get_text(strip=True)
    match = re.search(r"[-+]?\d*\.\d+|\d+", rate_text)
    if not match:
        return {"error": "Could not extract numeric Bank Rate."}
        
    current_value = Decimal(match.group())
    prev_value = current_value
    
    now_utc = datetime.now(UTC).isoformat()
    return {
        "rate_entry_id": str(uuid.uuid4()),
        "rate_country_code": "GB",
        "rate_type": "bank_rate",
        "rate_authority_name": "bank_of_england",
        "rate_effective_date": datetime.now(UTC).date().isoformat(),
        "rate_expiry_date": None,
        "is_rate_current": True,
        "rate_current_value_pct": float(round(current_value, 4)),
        "rate_current_value_bps": int(current_value * 100),
        "rate_prev_value_pct": float(round(prev_value, 4)),
        "rate_change_bps": 0,
        "rate_direction": "HOLD",
        "rate_source_url": url,
        "created_at": now_utc,
        "updated_at": now_utc
    }

@mcp.tool()
def get_overnight_rates():
    """Get overnight rates for US, Canada, and UK Bank Rate."""
    return {
        "US": get_us_fed_limit(),
        "CA": get_can_overnight_rate(),
        "UK": get_uk_bank_rate()
    }

if __name__ == "__main__":
    # Test section to verify output
    print("Testing US Fed Limit Retrieval:")
    print(json.dumps(get_us_fed_limit(), indent=2))
    print("\nTesting Canada Overnight Rate Retrieval:")
    print(json.dumps(get_can_overnight_rate(), indent=2))
    print("\nTesting UK Bank Rate Retrieval:")
    print(json.dumps(get_uk_bank_rate(), indent=2))

    # Start the server with SSE transport on port 8022
    mcp.run(transport="sse", host="0.0.0.0", port=8022)
