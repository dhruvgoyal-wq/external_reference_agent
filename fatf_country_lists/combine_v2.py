import json
import uuid
import csv
from datetime import datetime

# ─────────────────────────────────────────────
# HELPER: classification_type + severity from Basel score
# ─────────────────────────────────────────────
def basel_classification(score):
    if score >= 7.0:
        return "high_risk", 4
    elif score >= 6.0:
        return "increased_monitoring", 3
    elif score >= 5.0:
        return "elevated_concern", 2
    else:
        return "standard", 1

# ─────────────────────────────────────────────
# HELPER: pick worst-case classification across frameworks
# Priority: sanctioned(5) > black_list(4) > grey_list / high_risk(3-4)
#           > increased_monitoring(3) > elevated_concern(2) > standard(1)
# ─────────────────────────────────────────────
SEVERITY_ORDER = {
    "sanctioned": 5,
    "black_list": 4,
    "high_risk": 4,
    "grey_list": 3,
    "increased_monitoring": 3,
    "non_cooperative": 3,
    "elevated_concern": 2,
    "standard": 1,
}

def merge_classification(fatf_type, basel_type):
    """Return the higher-risk classification_type and its severity."""
    fatf_sev  = SEVERITY_ORDER.get(fatf_type,  0)
    basel_sev = SEVERITY_ORDER.get(basel_type, 0)
    if fatf_sev >= basel_sev:
        return fatf_type,  fatf_sev
    else:
        return basel_type, basel_sev

# ─────────────────────────────────────────────
# ISO3 lookup
# ─────────────────────────────────────────────
name_to_iso3 = {
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
    # FATF-only names
    "Democratic People's Republic of Korea": "PRK", "Iran": "IRN",
    "Democratic Republic of Congo": "COD",
    "Lao People's Democratic Republic": "LAO", "South Sudan": "SSD",
    "Syria": "SYR", "Yemen": "YEM", "Monaco": "MCO",
    "Virgin Islands (UK)": "VGB",
}

NOW = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# ─────────────────────────────────────────────
# STEP 1: Load FATF Black List
# ─────────────────────────────────────────────
# country_name → {classification_type, severity, url, effective_date}
fatf_data = {}

with open("black-grey-lists/high-risk-jurisdictions.csv", "r", encoding="utf-8") as f:
    next(f)  # skip header
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 2:
            country = row[0].strip()
            url     = row[1].strip()
            fatf_data[country] = {
                "classification_type": "black_list",
                "classification_severity": 4,
                "url": url,
                "effective_date": "2025-02-01",
            }

# ─────────────────────────────────────────────
# STEP 2: Load FATF Grey List
# ─────────────────────────────────────────────
with open("black-grey-lists/jurisdictions-under-increased-monitoring.csv", "r", encoding="utf-8") as f:
    next(f)  # skip header
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 2:
            country = row[0].strip()
            url     = row[1].strip()
            fatf_data[country] = {
                "classification_type": "grey_list",
                "classification_severity": 3,
                "url": url,
                "effective_date": "2025-02-01",
            }

# ─────────────────────────────────────────────
# STEP 3: Load Basel AML Index
# ─────────────────────────────────────────────
# country_name → {score, rank}
basel_data = {}

with open("basel_aml_score/basel_governance_ranking.csv", "r", encoding="utf-8") as f:
    next(f)  # skip header
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 3:
            country = row[1].strip()
            score   = float(row[-1].strip())
            rank    = int(row[0].strip())
            basel_data[country] = {"score": score, "rank": rank}

# ─────────────────────────────────────────────
# STEP 4: Build unified country set and merge records
# ─────────────────────────────────────────────
all_countries = set(fatf_data.keys()) | set(basel_data.keys())

records = []
stats = {"fatf_only": 0, "basel_only": 0, "both": 0}

for country in sorted(all_countries):
    has_fatf  = country in fatf_data
    has_basel = country in basel_data

    # — FATF fields —
    fatf_type     = fatf_data[country]["classification_type"]      if has_fatf  else None
    fatf_url      = fatf_data[country]["url"]                      if has_fatf  else None
    fatf_eff_date = fatf_data[country]["effective_date"]           if has_fatf  else None

    # — Basel fields —
    basel_score   = basel_data[country]["score"]                   if has_basel else None
    if has_basel:
        basel_type, _ = basel_classification(basel_score)
    else:
        basel_type = None

    # — Merged classification (worst-case wins) —
    if has_fatf and has_basel:
        merged_type, merged_severity = merge_classification(fatf_type, basel_type)
        stats["both"] += 1
    elif has_fatf:
        merged_type     = fatf_type
        merged_severity = fatf_data[country]["classification_severity"]
        stats["fatf_only"] += 1
    else:
        merged_type, merged_severity = basel_classification(basel_score)
        stats["basel_only"] += 1

    # — Source framework label —
    if has_fatf and has_basel:
        source_framework        = "FATF,BASEL"
        framework_body_full_name = "Financial Action Task Force; Basel Committee on Banking Supervision"
    elif has_fatf:
        source_framework        = "FATF"
        framework_body_full_name = "Financial Action Task Force"
    else:
        source_framework        = "BASEL"
        framework_body_full_name = "Basel Committee on Banking Supervision"

    # — Source URLs (pipe-separated when both present) —
    urls = []
    if has_fatf:
        urls.append(fatf_url)
    if has_basel:
        urls.append("https://index.baselgovernance.org/ranking")
    source_reference_url = " | ".join(urls)

    # — Effective date: earliest across available sources —
    dates = []
    if has_fatf:
        dates.append(fatf_eff_date)
    if has_basel:
        dates.append("2024-01-01")
    effective_date = min(dates)

    records.append({
        "risk_registry_id":          str(uuid.uuid4()),
        "country_code_iso3":         name_to_iso3.get(country, None),
        "country_name":              country,
        "source_framework":          source_framework,
        "framework_body_full_name":  framework_body_full_name,
        "classification_type":       merged_type,
        "classification_severity":   merged_severity,
        "sanctions_programme_name":  None,
        "effective_date":            effective_date,
        "expiration_date":           None,
        "is_currently_active":       True,
        "applies_to_country":        "ALL",
        "fatf_mutual_evaluation_rating": None,
        "fatf_classification_type":  fatf_type,          # FATF-specific label preserved
        "basel_aml_index_score":     basel_score,
        "basel_aml_index_year":      2024 if has_basel else None,
        "basel_classification_type": basel_type,         # Basel-specific label preserved
        "source_reference_url":      source_reference_url,
        "source_document_date":      effective_date,
        "created_at":                NOW,
        "updated_at":                NOW,
    })

# ─────────────────────────────────────────────
# STEP 5: Write output
# ─────────────────────────────────────────────
output = {
    "table_name":    "fact_country_risk_registry",
    "total_records": len(records),
    "sources":       ["FATF", "BASEL"],
    "stats": {
        "fatf_and_basel": stats["both"],
        "fatf_only":      stats["fatf_only"],
        "basel_only":     stats["basel_only"],
    },
    "records": records,
}

with open("fact_country_risk_registry_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ Done — {len(records)} unique country records written.")
print(f"   Countries in both FATF + Basel : {stats['both']}")
print(f"   FATF only                      : {stats['fatf_only']}")
print(f"   Basel only                     : {stats['basel_only']}")