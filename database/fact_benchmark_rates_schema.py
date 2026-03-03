import mysql.connector
from mysql.connector import errorcode

DB_CONFIG = {
    "host": "localhost",
    "user": "root",         
    "password": ""
}

DATABASE_NAME = "ext_reference"
TABLE_NAME = "fact_benchmark_rates"


def create_database(cursor):
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} "
        "DEFAULT CHARACTER SET utf8mb4 "
        "DEFAULT COLLATE utf8mb4_unicode_ci"
    )


def create_table(cursor):
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.{TABLE_NAME} (
        rate_entry_id CHAR(36) NOT NULL,
        rate_country_code CHAR(2) NOT NULL,
        rate_type VARCHAR(50) NOT NULL,
        rate_authority_name VARCHAR(100) NOT NULL,
        rate_effective_date DATE NOT NULL,
        rate_expiry_date DATE NULL,
        is_rate_current BOOLEAN NOT NULL DEFAULT FALSE,
        rate_current_value_pct DECIMAL(6,4) NOT NULL,
        rate_current_value_bps INT NOT NULL,
        rate_prev_value_pct DECIMAL(6,4) NULL,
        rate_change_bps INT NULL,
        rate_direction VARCHAR(10) NULL,
        rate_source_url VARCHAR(1024) NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
                     ON UPDATE CURRENT_TIMESTAMP,

        PRIMARY KEY (rate_entry_id),
        CONSTRAINT chk_country_code 
            CHECK (rate_country_code IN ('US','CA','GB')),
        CONSTRAINT chk_rate_value_pct 
            CHECK (rate_current_value_pct >= 0),
        CONSTRAINT chk_rate_value_bps 
            CHECK (rate_current_value_bps >= 0),
        CONSTRAINT chk_rate_direction
            CHECK (rate_direction IN ('HIKE','CUT','HOLD') OR rate_direction IS NULL),
        CONSTRAINT chk_change_range
            CHECK (rate_change_bps BETWEEN -5000 AND 5000 OR rate_change_bps IS NULL),
        CONSTRAINT chk_effective_date_range
            CHECK (rate_effective_date BETWEEN '1900-01-01' AND '2099-12-31'),
        CONSTRAINT chk_expiry_date_range
            CHECK (
                rate_expiry_date IS NULL OR 
                rate_expiry_date BETWEEN '1900-01-01' AND '2099-12-31'
            )
    )
    ENGINE=InnoDB;
    """

    cursor.execute(create_table_sql)

    cursor.execute(f"""
        CREATE UNIQUE INDEX ux_current_rate
        ON {DATABASE_NAME}.{TABLE_NAME} 
        (rate_country_code, rate_type, is_rate_current)
    """)

    cursor.execute(f"""
        CREATE INDEX idx_country_type_date
        ON {DATABASE_NAME}.{TABLE_NAME}
        (rate_country_code, rate_type, rate_effective_date DESC)
    """)


def main():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("Connected to MySQL")

        create_database(cursor)
        print(f"Database `{DATABASE_NAME}` ensured.")

        create_table(cursor)
        print(f"Table `{TABLE_NAME}` created successfully.")

        conn.commit()
        cursor.close()
        conn.close()

        print("Schema setup completed successfully.")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Access denied: Check username or password.")
        else:
            print(f"MySQL Error: {err}")


if __name__ == "__main__":
    main()