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
TABLE_NAME = "fact_federal_holidays"

# Paths to holiday JSON files
HOLIDAY_FILES = [
    {
        "path": "../holiday_lists/uk_bank_holidays.json",
        "country": "GBR",
        "description": "UK Bank Holidays"
    },
    {
        "path": "../holiday_lists/canada_system_closures.json",
        "country": "CAN",
        "description": "Canada System Closures"
    },
    {
        "path": "../holiday_lists/us_fedach_holiday_schedule.json",
        "country": "USA",
        "description": "US FedACH Holiday Schedule"
    }
]


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


def load_all_holiday_data(base_path):
    """Load and combine data from all holiday JSON files"""
    all_records = []

    for file_info in HOLIDAY_FILES:
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
                print(f"  ✓ Loaded {len(data)} records from {file_info['country']}")
            else:
                print(f"  ✗ Unexpected data format in {file_path}")

        except json.JSONDecodeError as err:
            print(f"  ✗ Error parsing JSON: {err}")
        except Exception as err:
            print(f"  ✗ Error reading file: {err}")

    print(f"\nTotal records loaded: {len(all_records)}")
    return all_records


def insert_records(cursor, records):
    """Insert holiday records into the database"""

    insert_sql = f"""
    INSERT INTO {DATABASE_NAME}.{TABLE_NAME} (
        holiday_id,
        holiday_country_code,
        holiday_date,
        holiday_month,
        holiday_year,
        holiday_day_of_week,
        holiday_name,
        is_bank_holiday,
        holiday_source_url,
        created_at,
        updated_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """

    inserted_count = 0
    error_count = 0
    skipped_count = 0

    for record in records:
        try:
            # Validate that the record has required fields
            if not record.get('holiday_id') or not record.get('holiday_date'):
                skipped_count += 1
                continue

            # Handle holiday_region field (UK data has this, others don't)
            # Extract country code from the record
            country_code = record.get('holiday_country_code', '')

            values = (
                record.get('holiday_id'),
                country_code,
                record.get('holiday_date'),
                record.get('holiday_month'),
                record.get('holiday_year'),
                record.get('holiday_day_of_week'),
                record.get('holiday_name'),
                record.get('is_bank_holiday', True),
                record.get('holiday_source_url'),
                clean_timestamp(record.get('created_at')),
                clean_timestamp(record.get('updated_at'))
            )

            cursor.execute(insert_sql, values)
            inserted_count += 1

            if inserted_count % 20 == 0:
                print(f"  Inserted {inserted_count} records...")

        except mysql.connector.IntegrityError as err:
            # Duplicate key - record already exists
            if "Duplicate entry" in str(err):
                skipped_count += 1
            else:
                error_count += 1
                print(f"  Integrity error for holiday {record.get('holiday_name', 'unknown')}: {err}")
        except mysql.connector.Error as err:
            error_count += 1
            print(f"  Error inserting record {record.get('holiday_id', 'unknown')}: {err}")
            continue

    return inserted_count, error_count, skipped_count


def main():
    try:
        # Load all holiday data
        base_path = Path(__file__).parent
        records = load_all_holiday_data(base_path)

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
