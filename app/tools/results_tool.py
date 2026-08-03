from app.db import get_connection

def get_test_results(patient_id: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    # Retrieve all test results for the patient
    cursor.execute("SELECT * FROM test_results WHERE patient_id = ?", (patient_id,))
    rows = cursor.fetchall()

    conn.close()

    # Convert SQLite rows into dictionaries for the API response
    results = [dict(row) for row in rows]

    if not results:
        return {
            "success": True,
            "message": "No test results found.",
            "results": []
        }

    return {
        "success": True,
        "results": results
    }