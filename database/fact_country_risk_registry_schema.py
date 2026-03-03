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
TABLE_NAME = "fact_country_risk_registry"


def create_database(cursor):
    cursor.execute(f"""
        CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}
        DEFAULT CHARACTER SET utf8mb4
        DEFAULT COLLATE utf8mb4_unicode_ci
    """)


def create_table(cursor):
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.{TABLE_NAME} (

        risk_registry_id CHAR(36) NOT NULL,

        country_code_iso3 CHAR(3) NOT NULL,

        country_name VARCHAR(100) NOT NULL,

        source_framework VARCHAR(20) NOT NULL,

        framework_body_full_name VARCHAR(200) NOT NULL,

        classification_type VARCHAR(50) NOT NULL,

        classification_severity INT NOT NULL,

        sanctions_programme_name VARCHAR(200) NULL,

        effective_date DATE NOT NULL,

        expiration_date DATE NULL,

        is_currently_active BOOLEAN NOT NULL DEFAULT TRUE,

        applies_to_country VARCHAR(50) NOT NULL DEFAULT 'ALL',

        fatf_mutual_evaluation_rating VARCHAR(30) NULL,

        basel_aml_index_score DECIMAL(4,2) NULL,

        basel_aml_index_year INT NULL,

        source_reference_url VARCHAR(1024) NOT NULL,

        source_document_date DATE NOT NULL,

        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP,

        -- =============================
        -- Primary Key
        -- =============================
        PRIMARY KEY (risk_registry_id),

        -- =============================
        -- Constraints (Globally Unique)
        -- =============================

        CONSTRAINT chk_fcrr_framework
            CHECK (source_framework IN
                ('FATF','OFAC','BASEL','UN','EU','HMTO','OSFI')),

        CONSTRAINT chk_fcrr_classification_type
            CHECK (classification_type IN
                ('grey_list','black_list','sanctioned',
                 'high_risk','increased_monitoring',
                 'non_cooperative','elevated_concern','standard')),

        CONSTRAINT chk_fcrr_severity
            CHECK (classification_severity BETWEEN 1 AND 5),

        CONSTRAINT chk_fcrr_effective_date
            CHECK (effective_date BETWEEN '1900-01-01' AND '2099-12-31'),

        CONSTRAINT chk_fcrr_expiration_date
            CHECK (expiration_date IS NULL OR
                   expiration_date BETWEEN '1900-01-01' AND '2099-12-31'),

        CONSTRAINT chk_fcrr_basel_score
            CHECK (basel_aml_index_score IS NULL OR
                   basel_aml_index_score BETWEEN 0 AND 10),

        CONSTRAINT chk_fcrr_basel_year
            CHECK (basel_aml_index_year IS NULL OR
                   basel_aml_index_year BETWEEN 2012 AND 2099),

        CONSTRAINT chk_fcrr_applies_to
            CHECK (applies_to_country IN ('CAN','GBR','USA','ALL'))
    )
    ENGINE=InnoDB;
    """

    cursor.execute(create_table_sql)

    # ======================================
    # Unique active classification constraint
    # Only one active row per:
    # (country, framework, classification_type)
    # ======================================
    try:
        cursor.execute(f"""
            CREATE UNIQUE INDEX ux_fcrr_active_record
            ON {DATABASE_NAME}.{TABLE_NAME}
            (country_code_iso3, source_framework,
             classification_type, is_currently_active)
        """)
    except mysql.connector.Error:
        pass

    # ======================================
    # Indexes for query performance
    # ======================================

    try:
        cursor.execute(f"""
            CREATE INDEX idx_fcrr_country
            ON {DATABASE_NAME}.{TABLE_NAME}
            (country_code_iso3)
        """)
    except mysql.connector.Error:
        pass

    try:
        cursor.execute(f"""
            CREATE INDEX idx_fcrr_framework
            ON {DATABASE_NAME}.{TABLE_NAME}
            (source_framework)
        """)
    except mysql.connector.Error:
        pass

    try:
        cursor.execute(f"""
            CREATE INDEX idx_fcrr_severity
            ON {DATABASE_NAME}.{TABLE_NAME}
            (classification_severity)
        """)
    except mysql.connector.Error:
        pass

    try:
        cursor.execute(f"""
            CREATE INDEX idx_fcrr_effective_date
            ON {DATABASE_NAME}.{TABLE_NAME}
            (effective_date)
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