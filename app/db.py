import sqlite3

# SQLite database file used by the chatbot
DB_PATH = "healthcare_chatbot.db"

def get_connection():
    # Create and return a database connection
    conn = sqlite3.connect(DB_PATH)

    # Return query results as dictionary-like rows
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Initialize database schema and seed sample data
    conn = get_connection()
    cursor = conn.cursor()

    # Stores registered patients
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    # Stores appointment records
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

    # Stores patient prescriptions and refill status
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            prescription_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            medication TEXT NOT NULL,
            refill_status TEXT DEFAULT 'not_requested',
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)

    # Stores lab/test results
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

    # Seed sample data (ignored if already present)
    cursor.execute("""
        INSERT OR IGNORE INTO patients (patient_id, name)
        VALUES ('p1', 'Arjun')
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO prescriptions (patient_id, medication)
        VALUES ('p1', 'Metformin 500mg')
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO test_results (patient_id, test_name, result, date)
        VALUES ('p1', 'Blood Sugar', '110 mg/dL', '2026-07-20')
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Create tables and sample data on first run
    init_db()
    print("Healthcare database initialized.")