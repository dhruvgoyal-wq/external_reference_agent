import time
import uuid
import logging
import cloudscraper
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, UTC
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Unified Risk Registry")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server_risk_registry_unified")

FATF_URL = "https://www.fatf-gafi.org/en/countries/black-and-grey-lists.html"
BASEL_URL = "https://index.baselgovernance.org/ranking"

# ISO3 mapping from combine_v2.py
NAME_TO_ISO3 = {
    "Myanmar": "MMR", "Haiti": "HTI", "Democratic Republic of the Congo": "COD",
    "Chad": "TCD", "Equatorial Guinea": "GNQ", "Venezuela": "VEN", "Lao PDR": "LAO",
    "Gabon": "GAB", "Central African Republic": "CAF", "Guinea-Bissau": "GNB",
    "Republic of the Congo": "COG", "China": "CHN", "Djibouti": "DJI",
    "Niger": "NER", "Algeria": "DZA", "Madagascar": "MDG", "Turkmenistan": "TKM",
    "Cambodia": "KHM", "Vietnam": "VNM", "Comoros": "COM", "Nicaragua": "NIC",
    "Papua New Guinea": "PNG", "Kenya": "KEN", "Angola": "AGO", "Eswatini": "SWZ",
    "Tajikistan": "TJK", "Togo": "TGO", "Guinea": "GIN", "Suriname": "SUR",
    "Cameroon": "CMR", "Sierra Leone": "SLE", "Mozambique": "MOZ", "Benin": "BEN",
    "Solomon Islands": "SLB", "Mauritania": "MRT", "Liberia": "LBR", "Mali": "MLI",
    "Nigeria": "NGA", "Kuwait": "KWT", "United Arab Emirates": "ARE",
    "Côte d'Ivoire": "CIV", "Lesotho": "LSO", "Zimbabwe": "ZWE", "Thailand": "THA",
    "Kyrgyzstan": "KGZ", "Sao Tome and Principe": "STP", "Lebanon": "LBN",
    "Iraq": "IRQ", "Nepal": "NPL", "Saudi Arabia": "SAU", "Panama": "PAN",
    "Gambia": "GMB", "Burkina Faso": "BFA", "Uganda": "UGA", "Rwanda": "RWA",
    "Belarus": "BLR", "Ethiopia": "ETH", "Tonga": "TON", "Honduras": "HND",
    "India": "IND", "El Salvador": "SLV", "Türkiye": "TUR", "Pakistan": "PAK",
    "South Africa": "ZAF", "Bangladesh": "BGD", "Malaysia": "MYS", "Bolivia": "BOL",
    "Timor-Leste": "TLS", "Bosnia and Herzegovina": "BIH", "Indonesia": "IDN",
    "Mexico": "MEX", "Tanzania": "TZA", "Bhutan": "BTN", "Philippines": "PHL",
    "Azerbaijan": "AZE", "Saint Kitts and Nevis": "KNA", "Cape Verde": "CPV",
    "Guatemala": "GTM", "Malawi": "MWI", "Brazil": "BRA", "Ukraine": "UKR",
    "Hong Kong, SAR, China": "HKG", "Senegal": "SEN", "Zambia": "ZMB",
    "Uzbekistan": "UZB", "Qatar": "QAT", "Egypt": "EGY", "Serbia": "SRB",
    "Kazakhstan": "KAZ", "Bahrain": "BHR", "Cuba": "CUB", "Guyana": "GUY",
    "Hungary": "HUN", "Sri Lanka": "LKA", "Malta": "MLT", "Ghana": "GHA",
    "Bahamas": "BHS", "Dominican Republic": "DOM", "Colombia": "COL",
    "Morocco": "MAR", "Bulgaria": "BGR", "Costa Rica": "CRI", "Germany": "DEU",
    "Vanuatu": "VUT", "Mongolia": "MNG", "Barbados": "BRB", "Ecuador": "ECU",
    "Paraguay": "PRY", "Marshall Islands": "MHL", "Peru": "PER", "Grenada": "GRD",
    "Jordan": "JOR", "United States": "USA", "Romania": "ROU", "Jamaica": "JAM",
    "Namibia": "NAM", "Cyprus": "CYP", "Italy": "ITA", "Tunisia": "TUN",
    "Fiji": "FJI", "Japan": "JPN", "Singapore": "SGP", "Mauritius": "MUS",
    "Moldova": "MDA", "Canada": "CAN", "Seychelles": "SYC", "Saint Lucia": "LCA",
    "Samoa": "WSM", "Netherlands": "NLD", "Korea, South": "KOR",
    "Taiwan (Chinese Taipei)": "TWN", "Poland": "POL", "Switzerland": "CHE",
    "Belgium": "BEL", "Argentina": "ARG", "Ireland": "IRL", "Slovakia": "SVK",
    "Albania": "ALB", "Montenegro": "MNE", "Georgia": "GEO", "Austria": "AUT",
    "Chile": "CHL", "Oman": "OMN", "Spain": "ESP", "Uruguay": "URY",
    "Brunei Darussalam": "BRN", "North Macedonia": "MKD", "Croatia": "HRV",
    "Dominica": "DMA", "Australia": "AUS", "Botswana": "BWA",
    "Trinidad and Tobago": "TTO", "Liechtenstein": "LIE", "Belize": "BLZ",
    "Israel": "ISR", "Saint Vincent and the Grenadines": "VCT",
    "United Kingdom": "GBR", "Lithuania": "LTU", "Latvia": "LVA",
    "France": "FRA", "Greece": "GRC", "Antigua and Barbuda": "ATG",
    "Armenia": "ARM", "Luxembourg": "LUX", "Nauru": "NRU", "Portugal": "PRT",
    "Czech Republic": "CZE", "New Zealand": "NZL", "Norway": "NOR",
    "Slovenia": "SVN", "Andorra": "AND", "Sweden": "SWE", "Estonia": "EST",
    "Denmark": "DNK", "San Marino": "SMR", "Iceland": "ISL", "Finland": "FIN",
    "Democratic People's Republic of Korea": "PRK", "Iran": "IRN",
    "Democratic Republic of Congo": "COD",
    "Lao People's Democratic Republic": "LAO", "South Sudan": "SSD",
    "Syria": "SYR", "Yemen": "YEM", "Monaco": "MCO",
    "Virgin Islands (UK)": "VGB",
}

# -----------------------------------------------------------------------------
# Scraping Logic
# -----------------------------------------------------------------------------

def scrape_fatf_lists():
    """Scrapes the FATF website for high-risk and increased monitoring lists."""
    logger.info(f"Scraping FATF data from {FATF_URL}")
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(FATF_URL)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch FATF page: {e}")
        return [], []

    soup = BeautifulSoup(response.text, 'html.parser')
    high_risk = []
    increased_monitoring = []

    # High-risk jurisdictions (Black List)
    # Corrected selectors from black_grey_lists.py
    high_risk_section = soup.find('ul', id='list-61c19274bd')
    if high_risk_section:
        items = high_risk_section.find_all('li', class_='cmp-list__item')
        for item in items:
            title_tag = item.find('span', class_='cmp-list__item-title')
            link_tag = item.find('a', class_='cmp-list__item-link')
            if title_tag and link_tag:
                country_name = title_tag.get_text(strip=True)
                country_url = link_tag.get('href')
                if country_url and not country_url.startswith('http'):
                    country_url = "https://www.fatf-gafi.org" + country_url
                high_risk.append({
                    "country": country_name,
                    "url": country_url,
                    "type": "high_risk",
                    "severity": 2
                })

    # Jurisdictions under increased monitoring (Grey List)
    monitoring_section = soup.find('ul', id='list-6fd939583d')
    if monitoring_section:
        items = monitoring_section.find_all('li', class_='cmp-list__item')
        for item in items:
            title_tag = item.find('span', class_='cmp-list__item-title')
            link_tag = item.find('a', class_='cmp-list__item-link')
            if title_tag and link_tag:
                country_name = title_tag.get_text(strip=True)
                country_url = link_tag.get('href')
                if country_url and not country_url.startswith('http'):
                    country_url = "https://www.fatf-gafi.org" + country_url
                increased_monitoring.append({
                    "country": country_name,
                    "url": country_url,
                    "type": "jurisd_under_increased_monitoring",
                    "severity": 1
                })

    return high_risk, increased_monitoring

def scrape_basel_data():
    """Scrapes the Basel Governance Index ranking page using Selenium."""
    logger.info(f"Scraping Basel data from {BASEL_URL}")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(BASEL_URL)
        
        # Wait for JS to render
        time.sleep(5)
        
        # Scroll to load more if needed
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
    except Exception as e:
        logger.error(f"Failed to scrape Basel page: {e}")
        return []

    ranking_table = soup.find('table')
    if not ranking_table:
        logger.warning("No table found on Basel ranking page.")
        return []

    # Normalized headers
    headers = []
    for th in ranking_table.find_all('th'):
        h = th.text.strip().lower().replace(" ", "_")
        if "jurisdiction" in h: h = "country"
        if "score" in h: h = "score"
        headers.append(h)
        
    data = []
    rows = ranking_table.find_all('tr')[1:] # Skip header row
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= len(headers):
            row_data = {}
            for i, header in enumerate(headers):
                if i < len(cols):
                    row_data[header] = cols[i].text.strip()
            data.append(row_data)
            
    return data

# -----------------------------------------------------------------------------
# FATF Tools
# -----------------------------------------------------------------------------

@mcp.tool()
def get_fatf_high_risk():
    """
    Returns the list of countries identified by FATF as High-Risk Jurisdictions subject to a Call for Action (Black List).
    Performs live scraping.
    """
    high_risk, _ = scrape_fatf_lists()
    return high_risk

@mcp.tool()
def get_fatf_increased_monitoring():
    """
    Returns the list of countries identified by FATF as Jurisdictions under Increased Monitoring (Grey List).
    Performs live scraping.
    """
    _, increased_monitoring = scrape_fatf_lists()
    return increased_monitoring

@mcp.tool()
def get_all_fatf_risk_countries():
    """
    Returns both high-risk and increased monitoring countries in a single list.
    """
    high_risk, increased_monitoring = scrape_fatf_lists()
    return high_risk + increased_monitoring

# -----------------------------------------------------------------------------
# Basel Tools
# -----------------------------------------------------------------------------

@mcp.tool()
def get_basel_scores():
    """
    Returns the full list of Basel AML scores and rankings.
    Performs live scrape using Selenium.
    """
    return scrape_basel_data()

@mcp.tool()
def get_country_basel_score(country_name: str):
    """
    Search for a specific country's Basel AML score.
    """
    all_scores = scrape_basel_data()
    for entry in all_scores:
        if country_name.lower() in entry.get('country', '').lower():
            return entry
    return {"error": f"Country '{country_name}' not found in Basel ranking."}

# -----------------------------------------------------------------------------
# Combined Risk Registry Tools
# -----------------------------------------------------------------------------

@mcp.tool()
def get_combined_risk_registry():
    """
    Returns the unified risk registry merging live FATF and Basel data.
    Note: May take 10-15 seconds due to live scraping.
    """
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # 1. Scrape FATF
    fatf_high, fatf_monitoring = scrape_fatf_lists()
    fatf_map = {e["country"]: e for e in (fatf_high + fatf_monitoring)}

    # 2. Scrape Basel
    basel_list = scrape_basel_data()
    basel_map = {e.get("country"): e for e in basel_list if e.get("country")}

    # 3. Combine
    all_countries = set(fatf_map.keys()) | set(basel_map.keys())
    records = []
    
    for country in sorted(all_countries):
        fatf_entry = fatf_map.get(country)
        basel_entry = basel_map.get(country)
        
        has_fatf = fatf_entry is not None
        has_basel = basel_entry is not None
        
        # Severity Mapping: 0=None, 1=monitoring, 2=high_risk
        classification_type = fatf_entry["type"] if has_fatf else None
        classification_severity = fatf_entry["severity"] if has_fatf else 0
        
        source_framework = "FATF,BASEL" if (has_fatf and has_basel) else ("FATF" if has_fatf else "BASEL")
        framework_body = "Financial Action Task Force" if has_fatf else ""
        if has_basel:
            framework_body += ("; " if framework_body else "") + "Basel Committee on Banking Supervision"

        urls = []
        if has_fatf: urls.append(fatf_entry["url"])
        if has_basel: urls.append(BASEL_URL)
        source_url = " | ".join(urls)

        effective_date = "2025-02-01" if has_fatf else ("2024-01-01" if has_basel else None)

        records.append({
            "risk_registry_id": str(uuid.uuid4()),
            "country_code_iso3": NAME_TO_ISO3.get(country),
            "country_name": country,
            "source_framework": source_framework,
            "framework_body_full_name": framework_body,
            "classification_type": classification_type,
            "classification_severity": classification_severity,
            "effective_date": effective_date,
            "is_currently_active": True,
            "basel_aml_index_score": basel_entry.get("score") if has_basel else None,
            "basel_aml_index_year": 2024 if has_basel else None,
            "source_reference_url": source_url,
            "created_at": now,
            "updated_at": now,
        })

    return {
        "status": "success",
        "timestamp": now,
        "total_records": len(records),
        "records": records
    }

@mcp.tool()
def search_risk_registry(query: str):
    """
    Search for a country in the combined risk registry (Name or ISO3).
    """
    registry = get_combined_risk_registry()
    results = []
    for record in registry["records"]:
        if query.lower() in record["country_name"].lower() or (record["country_code_iso3"] and query.upper() == record["country_code_iso3"]):
            results.append(record)
    return results

if __name__ == "__main__":
    print(scrape_fatf_lists())
    print(scrape_basel_data())
    
    mcp.run(transport="sse", host="0.0.0.0", port=8024)
