import mysql.connector
from mysql.connector import errorcode

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


def create_database(cursor):
    cursor.execute(
        f"""
        CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}
        DEFAULT CHARACTER SET utf8mb4
        DEFAULT COLLATE utf8mb4_unicode_ci
        """
    )


def create_table(cursor):
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.{TABLE_NAME} (

        holiday_id CHAR(36) NOT NULL,

        holiday_country_code CHAR(3) NOT NULL,

        holiday_date DATE NOT NULL,

        holiday_month INT NOT NULL,

        holiday_year INT NOT NULL,

        holiday_day_of_week VARCHAR(10) NOT NULL,

        holiday_name VARCHAR(100) NOT NULL,

        is_bank_holiday BOOLEAN NOT NULL DEFAULT TRUE,

        holiday_source_url VARCHAR(1024) NOT NULL,

        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                   ON UPDATE CURRENT_TIMESTAMP,

        -- =============================
        -- Primary Key
        -- =============================
        PRIMARY KEY (holiday_id),

        -- =============================
        -- Constraints (Globally Unique Names)
        -- =============================

        CONSTRAINT chk_fact_federal_holidays_country_code
            CHECK (holiday_country_code IN ('USA')),

        CONSTRAINT chk_fact_federal_holidays_month
            CHECK (holiday_month BETWEEN 1 AND 12),

        CONSTRAINT chk_fact_federal_holidays_year
            CHECK (holiday_year BETWEEN 1900 AND 2099),

        CONSTRAINT chk_fact_federal_holidays_date
            CHECK (holiday_date BETWEEN '1900-01-01' AND '2099-12-31'),

        CONSTRAINT chk_fact_federal_holidays_day_of_week
            CHECK (
                holiday_day_of_week IN
                ('Monday','Tuesday','Wednesday','Thursday',
                 'Friday','Saturday','Sunday')
            )
    )
    ENGINE=InnoDB;
    """

    cursor.execute(create_table_sql)

    # ======================================
    # Indexes (Safe Creation Pattern)
    # ======================================

    try:
        cursor.execute(f"""
            CREATE UNIQUE INDEX ux_fact_federal_holidays_country_date
            ON {DATABASE_NAME}.{TABLE_NAME}
            (holiday_country_code, holiday_date)
        """)
    except mysql.connector.Error:
        pass  # Index already exists

    try:
        cursor.execute(f"""
            CREATE INDEX idx_fact_federal_holidays_year
            ON {DATABASE_NAME}.{TABLE_NAME}
            (holiday_year)
        """)
    except mysql.connector.Error:
        pass

    try:
        cursor.execute(f"""
            CREATE INDEX idx_fact_federal_holidays_country_year_month
            ON {DATABASE_NAME}.{TABLE_NAME}
            (holiday_country_code, holiday_year, holiday_month)
        """)
    except mysql.connector.Error:
        pass


def main():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("Connected to MySQL")

        create_database(cursor)
        print(f"Database `{DATABASE_NAME}` ensured.")

        create_table(cursor)
        print(f"Table `{TABLE_NAME}` ensured.")

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