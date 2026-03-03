import json
import uuid
import csv  # ✅ FIX 1: `csv` was used throughout but never imported — would crash immediately at runtime

records = []

def basel_classification(score):
    if score >= 7.0:
        return "high_risk", 4
    elif score >= 6.0:
        return "increased_monitoring", 3
    elif score >= 5.0:
        return "elevated_concern", 2
    else:
        return "standard", 1

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
    # ✅ FIX 2: "Côte d'Ivoire" was duplicated — once here and again in the FATF-only block below.
    # Python silently keeps only the last value; removed the duplicate from the FATF block.
    "Côte d'Ivoire": "CIV",
    "Lesotho": "LSO", "Zimbabwe": "ZWE", "Thailand": "THA",
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
    # FATF-only
    "Democratic People's Republic of Korea": "PRK", "Iran": "IRN",
    "Democratic Republic of Congo": "COD",
    # ✅ FIX 2 (cont): Removed duplicate "Côte d'Ivoire" entry that was here
    "Lao People's Democratic Republic": "LAO", "South Sudan": "SSD",
    "Syria": "SYR", "Yemen": "YEM", "Monaco": "MCO",
    "Virgin Islands (UK)": "VGB",
}

# ─────────────────────────────────────────────
# 1. FATF — Black List
# ─────────────────────────────────────────────
fatf_blacklist = []

# ✅ FIX 3: Added `next(f)` to skip the header row ("Country,Detail_URL,Type").
# Without this, the header would be appended as a fake country record.
with open("black-grey-lists/high-risk-jurisdictions.csv", "r", encoding="utf-8") as f:
    next(f)  # skip header
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 2:  # ✅ FIX 4: Guard against blank/malformed rows
            fatf_blacklist.append((row[0].strip(), row[1].strip()))

for country, url in fatf_blacklist:
    records.append({
        "risk_registry_id": str(uuid.uuid4()),
        "country_code_iso3": name_to_iso3.get(country, None),
        "country_name": country,
        "source_framework": "FATF",
        "framework_body_full_name": "Financial Action Task Force",
        "classification_type": "black_list",
        "classification_severity": 4,
        "sanctions_programme_name": None,
        "effective_date": "2025-02-01",
        "expiration_date": None,
        "is_currently_active": True,
        "applies_to_country": "ALL",
        "fatf_mutual_evaluation_rating": None,
        "basel_aml_index_score": None,
        "basel_aml_index_year": None,
        "source_reference_url": url,
        "source_document_date": "2025-02-01",
        "created_at": "2025-02-01T00:00:00Z",
        "updated_at": "2025-02-01T00:00:00Z"
    })

# ─────────────────────────────────────────────
# 2. FATF — Grey List
# ─────────────────────────────────────────────
fatf_greylist = []

# ✅ FIX 5: Filename was wrong — the scraper saves as "jurisdictions-under-increased-monitoring.csv"
# but the code referenced "increased-monitoring.csv". This would cause a FileNotFoundError.
with open("black-grey-lists/jurisdictions-under-increased-monitoring.csv", "r", encoding="utf-8") as f:
    next(f)  # ✅ FIX 3 (same): skip header row
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 2:  # ✅ FIX 4 (same): guard against blank/malformed rows
            fatf_greylist.append((row[0].strip(), row[1].strip()))

for country, url in fatf_greylist:
    records.append({
        "risk_registry_id": str(uuid.uuid4()),
        "country_code_iso3": name_to_iso3.get(country, None),
        "country_name": country,
        "source_framework": "FATF",
        "framework_body_full_name": "Financial Action Task Force",
        "classification_type": "grey_list",
        "classification_severity": 3,
        "sanctions_programme_name": None,
        "effective_date": "2025-02-01",
        "expiration_date": None,
        "is_currently_active": True,
        "applies_to_country": "ALL",
        "fatf_mutual_evaluation_rating": None,
        "basel_aml_index_score": None,
        "basel_aml_index_year": None,
        "source_reference_url": url,
        "source_document_date": "2025-02-01",
        "created_at": "2025-02-01T00:00:00Z",
        "updated_at": "2025-02-01T00:00:00Z"
    })

# ─────────────────────────────────────────────
# 3. BASEL AML Index
# ─────────────────────────────────────────────
basel_raw = []

with open("basel_aml_score/basel_governance_ranking.csv", "r", encoding="utf-8") as f:
    next(f)  # ✅ FIX 3 (same): skip header row ("Rank,Jurisdiction,Overall Score")
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 3:  # ✅ FIX 4 (same): guard against blank/malformed rows
            basel_raw.append(row)

for line in basel_raw:
    rank = int(line[0])
    score = float(line[-1])
    # ✅ FIX 6: When csv.reader parses a properly-quoted CSV (e.g. "Hong Kong, SAR, China"),
    # it already handles the embedded comma — line[1] will be the full name as a single field.
    # The old ",".join(line[1:-1]) hack + .replace(";", ",") was a workaround for the raw string
    # version and is incorrect here — it would produce "Hong Kong, SAR, China" correctly by
    # accident only if there's no middle column, but would fail for edge cases.
    # Correct approach: simply take line[1] directly since csv.reader handles quoting.
    country = line[1].strip()

    ctype, severity = basel_classification(score)
    iso3 = name_to_iso3.get(country, None)

    records.append({
        "risk_registry_id": str(uuid.uuid4()),
        "country_code_iso3": iso3,
        "country_name": country,
        "source_framework": "BASEL",
        "framework_body_full_name": "Basel Committee on Banking Supervision",
        "classification_type": ctype,
        "classification_severity": severity,
        "sanctions_programme_name": None,
        "effective_date": "2024-01-01",
        "expiration_date": None,
        "is_currently_active": True,
        "applies_to_country": "ALL",
        "fatf_mutual_evaluation_rating": None,
        "basel_aml_index_score": score,
        "basel_aml_index_year": 2024,
        "source_reference_url": "https://index.baselgovernance.org/ranking",
        "source_document_date": "2024-01-01",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    })

# ─────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────
output = {
    "table_name": "fact_country_risk_registry",
    "total_records": len(records),
    "sources": ["FATF", "BASEL"],
    "records": records
}

with open("fact_country_risk_registry_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ Done — {len(records)} records written.")
print(f"   FATF blacklist : {len(fatf_blacklist)}")
print(f"   FATF greylist  : {len(fatf_greylist)}")
print(f"   Basel entries  : {len(records) - len(fatf_blacklist) - len(fatf_greylist)}")