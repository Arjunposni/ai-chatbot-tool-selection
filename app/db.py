import sqlite3

"""
Database setup for the Healthcare AI Chatbot.

This module is responsible for:
- Creating SQLite connections
- Initializing the database schema
- Seeding sample data for demonstration/testing
"""

DB_PATH = "healthcare_chatbot.db"


def get_connection():
    """
    Returns a SQLite connection configured to expose
    query results as dictionary-like objects.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates the required tables (if they do not exist)
    and inserts sample records for demo purposes.
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        # Core patient information.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)

        # Appointment records.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                specialty TEXT NOT NULL,
                date TEXT NOT NULL,
                status TEXT DEFAULT 'confirmed',
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """)

        # Prescription and refill information.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                prescription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                medication TEXT NOT NULL,
                refill_status TEXT DEFAULT 'not_requested',
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """)

        # Laboratory and diagnostic test results.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                test_name TEXT NOT NULL,
                result TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """)

        # Demo records used during development and testing.
        cursor.execute("""
            INSERT OR IGNORE INTO patients (patient_id, name)
            VALUES ('p1', 'Arjun')
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO prescriptions (patient_id, medication)
            VALUES ('p1', 'Metformin 500mg')
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO test_results (
                patient_id,
                test_name,
                result,
                date
            )
            VALUES (
                'p1',
                'Blood Sugar',
                '110 mg/dL',
                '2026-07-20'
            )
        """)

        conn.commit()


if __name__ == "__main__":
    init_db()
    print("Healthcare database initialized.")