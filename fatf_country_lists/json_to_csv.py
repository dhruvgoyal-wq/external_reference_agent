import json
import csv
import os

# Paths
json_path = 'fact_country_risk_registry_data.json'
csv_path = 'fact_country_risk_registry_data.csv'

def convert_json_to_csv():
    if not os.path.exists(json_path):
        print(f"❌ Error: {json_path} not found.")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        records = data.get('records', [])
        
        if not records:
            print("⚠️ No records found in JSON file.")
            return

        # Use the keys from the first record as headers
        headers = list(records[0].keys())

        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(records)

        print(f"✅ Successfully converted {len(records)} records from JSON to {csv_path}")
        
    except Exception as e:
        print(f"❌ An error occurred during conversion: {e}")

if __name__ == "__main__":
    convert_json_to_csv()
