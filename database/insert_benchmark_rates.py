import mysql.connector
from mysql.connector import errorcode
import json
from pathlib import Path
from datetime import datetime

# ==============================
# MySQL Connection Config
# ==============================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": ""
}

DATABASE_NAME = "ext_reference"
TABLE_NAME = "fact_benchmark_rates"

# Rate JSON files to process
RATE_FILES = [
    {
        "path": "../can_prime_rate.json",
        "country": "CA",
        "description": "Canada Prime Rate"
    },
    {
        "path": "../can_overnight_rate.json",
        "country": "CA",
        "description": "Canada Overnight Rate"
    },
    {
        "path": "../us_federal_reserve_limit.json",
        "country": "US",
        "description": "US Federal Reserve Rate"
    },
    {
        "path": "../us_prime_rate.json",
        "country": "US",
        "description": "US Prime Rate"
    },
    {
        "path": "../uk_bank_england_rate.json",
        "country": "GB",
        "description": "UK Bank of England Rate"
    },
    {
        "path": "../uk_sonia_rate.json",
        "country": "GB",
        "description": "UK SONIA Rate"
    }
]


def load_all_rate_data(base_path):
    """Load and combine data from all rate JSON files"""
    all_records = []

    for file_info in RATE_FILES:
        file_path = base_path / file_info["path"]

        if not file_path.exists():
            print(f"Warning: File not found - {file_path}")
            continue

        print(f"Loading {file_info['description']}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                all_records.extend(data)
                print(f"  ✓ Loaded {len(data)} record(s) from {file_info['country']}")
            elif isinstance(data, dict):
                # Single record wrapped in a dict
                all_records.append(data)
                print(f"  ✓ Loaded 1 record from {file_info['country']}")
            else:
                print(f"  ✗ Unexpected data format in {file_path}")

        except json.JSONDecodeError as err:
            print(f"  ✗ Error parsing JSON: {err}")
        except Exception as err:
            print(f"  ✗ Error reading file: {err}")

    print(f"\nTotal rate records loaded: {len(all_records)}")
    return all_records


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


def insert_records(cursor, records):
    """Insert rate records into the database"""

    insert_sql = f"""
    INSERT INTO {DATABASE_NAME}.{TABLE_NAME} (
        rate_entry_id,
        rate_country_code,
        rate_type,
        rate_authority_name,
        rate_effective_date,
        rate_expiry_date,
        is_rate_current,
        rate_current_value_pct,
        rate_current_value_bps,
        rate_prev_value_pct,
        rate_change_bps,
        rate_direction,
        rate_source_url,
        created_at,
        updated_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """

    inserted_count = 0
    error_count = 0
    skipped_count = 0

    for record in records:
        try:
            # Validate required fields
            if not record.get('rate_entry_id') or not record.get('rate_country_code'):
                skipped_count += 1
                continue

            # Clean timestamp fields
            created_at = clean_timestamp(record.get('created_at'))
            updated_at = clean_timestamp(record.get('updated_at'))

            values = (
                record.get('rate_entry_id'),
                record.get('rate_country_code'),
                record.get('rate_type'),
                record.get('rate_authority_name'),
                record.get('rate_effective_date'),
                record.get('rate_expiry_date'),
                record.get('is_rate_current', False),
                record.get('rate_current_value_pct'),
                record.get('rate_current_value_bps'),
                record.get('rate_prev_value_pct'),
                record.get('rate_change_bps'),
                record.get('rate_direction'),
                record.get('rate_source_url'),
                created_at,
                updated_at
            )

            cursor.execute(insert_sql, values)
            inserted_count += 1

            rate_info = f"{record.get('rate_country_code')} - {record.get('rate_type')}"
            print(f"  ✓ Inserted: {rate_info}")

        except mysql.connector.IntegrityError as err:
            # Duplicate key - record already exists
            if "Duplicate entry" in str(err):
                skipped_count += 1
                rate_info = f"{record.get('rate_country_code')} - {record.get('rate_type')}"
                print(f"  ⊘ Skipped (duplicate): {rate_info}")
            else:
                error_count += 1
                print(f"  ✗ Integrity error: {err}")
        except mysql.connector.Error as err:
            error_count += 1
            rate_info = f"{record.get('rate_country_code', 'unknown')} - {record.get('rate_type', 'unknown')}"
            print(f"  ✗ Error inserting {rate_info}: {err}")
            continue

    return inserted_count, error_count, skipped_count


def main():
    try:
        # Load all rate data
        base_path = Path(__file__).parent
        records = load_all_rate_data(base_path)

        if not records:
            print("No records to insert. Exiting.")
            return

        # Connect to MySQL
        print("\nConnecting to MySQL...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Connected successfully!")

        # Insert records
        print(f"\nInserting records into {DATABASE_NAME}.{TABLE_NAME}...")
        print("-" * 50)
        inserted, errors, skipped = insert_records(cursor, records)

        # Commit transaction
        conn.commit()

        # Print summary
        print("\n" + "="*50)
        print("INSERTION SUMMARY")
        print("="*50)
        print(f"Total records processed: {len(records)}")
        print(f"Successfully inserted: {inserted}")
        print(f"Skipped (duplicates/invalid): {skipped}")
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
    except Exception as err:
        print(f"Unexpected error: {err}")


if __name__ == "__main__":
    main()
