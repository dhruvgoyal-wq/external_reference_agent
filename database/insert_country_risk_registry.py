import mysql.connector
from mysql.connector import errorcode
import json
from pathlib import Path

# ==============================
# MySQL Connection Config
# ==============================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": ""
}

DATABASE_NAME = "ext_reference"
TABLE_NAME = "fact_country_risk_registry"

# Path to JSON data file
JSON_FILE_PATH = "../fatf_country_lists/fact_country_risk_registry_data.json"


def clean_timestamp(timestamp_str):
    """Convert ISO timestamp to MySQL datetime format"""
    if not timestamp_str:
        return None
    try:
        if isinstance(timestamp_str, str):
            # Remove timezone info (Z or +00:00)
            if 'Z' in timestamp_str:
                timestamp_str = timestamp_str.replace('Z', '')
            if '+' in timestamp_str:
                timestamp_str = timestamp_str.split('+')[0]
            # Remove microseconds if too long
            if '.' in timestamp_str:
                parts = timestamp_str.split('.')
                if len(parts[1]) > 6:
                    timestamp_str = f"{parts[0]}.{parts[1][:6]}"
            # Convert T to space for MySQL format
            timestamp_str = timestamp_str.replace('T', ' ')
        return timestamp_str
    except:
        return timestamp_str


def load_json_data(file_path):
    """Load and parse JSON data from file"""
    print(f"Loading data from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract records from the JSON structure
    if isinstance(data, dict) and 'records' in data:
        records = data['records']
        total = data.get('total_records', len(records))
        print(f"Found {total} records to insert")
        return records
    else:
        print(f"Found {len(data)} records to insert")
        return data


def insert_records(cursor, records):
    """Insert records into the database"""

    insert_sql = f"""
    INSERT INTO {DATABASE_NAME}.{TABLE_NAME} (
        risk_registry_id,
        country_code_iso3,
        country_name,
        source_framework,
        framework_body_full_name,
        classification_type,
        classification_severity,
        sanctions_programme_name,
        effective_date,
        expiration_date,
        is_currently_active,
        applies_to_country,
        fatf_mutual_evaluation_rating,
        basel_aml_index_score,
        basel_aml_index_year,
        source_reference_url,
        source_document_date,
        created_at,
        updated_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """

    inserted_count = 0
    error_count = 0

    for record in records:
        try:
            # Handle source_framework - may contain comma-separated values
            source_framework = record.get('source_framework', '')
            # Take the first framework if multiple are present
            if ',' in source_framework:
                source_framework = source_framework.split(',')[0].strip()

            values = (
                record.get('risk_registry_id'),
                record.get('country_code_iso3'),
                record.get('country_name'),
                source_framework,
                record.get('framework_body_full_name'),
                record.get('classification_type'),
                record.get('classification_severity'),
                record.get('sanctions_programme_name'),
                record.get('effective_date'),
                record.get('expiration_date'),
                record.get('is_currently_active', True),
                record.get('applies_to_country', 'ALL'),
                record.get('fatf_mutual_evaluation_rating'),
                record.get('basel_aml_index_score'),
                record.get('basel_aml_index_year'),
                record.get('source_reference_url'),
                record.get('source_document_date'),
                clean_timestamp(record.get('created_at')),
                clean_timestamp(record.get('updated_at'))
            )

            cursor.execute(insert_sql, values)
            inserted_count += 1

            if inserted_count % 50 == 0:
                print(f"Inserted {inserted_count} records...")

        except mysql.connector.Error as err:
            error_count += 1
            print(f"Error inserting record {record.get('risk_registry_id', 'unknown')}: {err}")
            continue

    return inserted_count, error_count


def main():
    try:
        # Check if file exists
        json_path = Path(__file__).parent / JSON_FILE_PATH
        if not json_path.exists():
            print(f"Error: JSON file not found at {json_path}")
            return

        # Load JSON data
        records = load_json_data(json_path)

        # Connect to MySQL
        print("\nConnecting to MySQL...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Connected successfully!")

        # Insert records
        print(f"\nInserting records into {DATABASE_NAME}.{TABLE_NAME}...")
        inserted, errors = insert_records(cursor, records)

        # Commit transaction
        conn.commit()

        # Print summary
        print("\n" + "="*50)
        print("INSERTION SUMMARY")
        print("="*50)
        print(f"Total records processed: {len(records)}")
        print(f"Successfully inserted: {inserted}")
        print(f"Errors: {errors}")
        print("="*50)

        # Close connection
        cursor.close()
        conn.close()
        print("\nDatabase connection closed.")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Access denied - Check username or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"Error: Database '{DATABASE_NAME}' does not exist")
        else:
            print(f"MySQL Error: {err}")
    except json.JSONDecodeError as err:
        print(f"Error: Invalid JSON format - {err}")
    except Exception as err:
        print(f"Unexpected error: {err}")


if __name__ == "__main__":
    main()
