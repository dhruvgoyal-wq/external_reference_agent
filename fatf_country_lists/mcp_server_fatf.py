import cloudscraper
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
import logging

# Initialize FastMCP server
mcp = FastMCP("FATF Risk Lists")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server_fatf")

FATF_URL = "https://www.fatf-gafi.org/en/countries/black-and-grey-lists.html"

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
    # Based on black_grey_lists.py logic: Looking for UL with ID 'list-61c19274bd'
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
    # Based on black_grey_lists.py logic: Looking for UL with ID 'list-6fd939583d'
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

@mcp.tool()
def get_fatf_high_risk():
    """
    Returns the list of countries identified by FATF as High-Risk Jurisdictions subject to a Call for Action (Black List).
    This performs a live scrape of the FATF website.
    """
    high_risk, _ = scrape_fatf_lists()
    return high_risk

@mcp.tool()
def get_fatf_increased_monitoring():
    """
    Returns the list of countries identified by FATF as Jurisdictions under Increased Monitoring (Grey List).
    This performs a live scrape of the FATF website.
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

if __name__ == "__main__":
    mcp.run(transport="sse")
