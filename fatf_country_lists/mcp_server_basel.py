import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Basel AML Scores")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server_basel")

BASEL_URL = "https://index.baselgovernance.org/ranking"

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
        
        # Scroll to load more if needed (based on main.py)
        # However, for live tool, we might just want what's visible or scrolls a bit
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
    except Exception as e:
        logger.error(f"Failed to scrape Basel page: {e}")
        return []

    # Parsing logic based on main.py
    ranking_table = soup.find('table')
    if not ranking_table:
        logger.warning("No table found on Basel ranking page.")
        return []

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

@mcp.tool()
def get_basel_scores():
    """
    Returns the full list of Basel AML scores and rankings.
    This performs a live scrape using Selenium.
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

if __name__ == "__main__":
    mcp.run(transport="sse")
