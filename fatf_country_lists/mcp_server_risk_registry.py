import json
import uuid
import logging
from datetime import datetime, UTC
from mcp.server.fastmcp import FastMCP

# Import scraping functions from siblings
from mcp_server_fatf import scrape_fatf_lists
from mcp_server_basel import scrape_basel_data

# Initialize FastMCP server
mcp = FastMCP("Country Risk Registry")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server_risk_registry")

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

def get_live_registry():
    """Combines live scraped data from FATF and Basel."""
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # 1. Scrape FATF
    fatf_high, fatf_monitoring = scrape_fatf_lists()
    fatf_map = {}
    for entry in fatf_high:
        fatf_map[entry["country"]] = entry
    for entry in fatf_monitoring:
        fatf_map[entry["country"]] = entry

    # 2. Scrape Basel
    basel_list = scrape_basel_data()
    basel_map = {}
    for entry in basel_list:
        country = entry.get("country")
        if country:
            basel_map[country] = entry

    # 3. Combine
    all_countries = set(fatf_map.keys()) | set(basel_map.keys())
    records = []
    
    for country in sorted(all_countries):
        fatf_entry = fatf_map.get(country)
        basel_entry = basel_map.get(country)
        
        has_fatf = fatf_entry is not None
        has_basel = basel_entry is not None
        
        # Classification
        classification_type = fatf_entry["type"] if has_fatf else None
        classification_severity = fatf_entry["severity"] if has_fatf else 0
        
        # Source Framework
        if has_fatf and has_basel:
            source_framework = "FATF,BASEL"
            framework_body = "Financial Action Task Force; Basel Committee on Banking Supervision"
        elif has_fatf:
            source_framework = "FATF"
            framework_body = "Financial Action Task Force"
        else:
            source_framework = "BASEL"
            framework_body = "Basel Committee on Banking Supervision"

        # URLs
        urls = []
        if has_fatf: urls.append(fatf_entry["url"])
        if has_basel: urls.append("https://index.baselgovernance.org/ranking")
        source_url = " | ".join(urls)

        # Dates
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
def get_combined_risk_registry():
    """
    Returns the unified risk registry by performing live scraping of both FATF and Basel sources.
    Note: This tool may take 10-15 seconds to complete due to live scraping.
    """
    return get_live_registry()

@mcp.tool()
def search_risk_registry(query: str):
    """
    Search for a country in the combined risk registry.
    """
    registry = get_live_registry()
    results = []
    for record in registry["records"]:
        if query.lower() in record["country_name"].lower() or (record["country_code_iso3"] and query.upper() == record["country_code_iso3"]):
            results.append(record)
    return results

if __name__ == "__main__":
    mcp.run(transport="sse")
