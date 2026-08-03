from app.db import get_connection

def request_prescription_refill(patient_id: str, medication: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    # Verify that the prescription exists
    cursor.execute(
        "SELECT * FROM prescriptions WHERE patient_id = ? AND medication = ?",
        (patient_id, medication)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {
            "success": False,
            "message": f"No existing prescription found for {medication}."
        }

    # Mark the refill as requested
    cursor.execute(
        "UPDATE prescriptions SET refill_status = 'requested' WHERE patient_id = ? AND medication = ?",
        (patient_id, medication)
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Refill requested for {medication}."
    }