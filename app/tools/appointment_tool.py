from app.db import get_connection

def book_appointment(patient_id: str, specialty: str, date: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    # Save a new appointment
    cursor.execute(
        "INSERT INTO appointments (patient_id, specialty, date) VALUES (?, ?, ?)",
        (patient_id, specialty, date)
    )

    conn.commit()

    # Get the auto-generated appointment ID
    appointment_id = cursor.lastrowid

    conn.close()

    return {
        "success": True,
        "appointment_id": appointment_id,
        "message": f"Appointment booked with {specialty} on {date}."
    }


def check_appointment_status(patient_id: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    # Retrieve all appointments for the patient
    cursor.execute("SELECT * FROM appointments WHERE patient_id = ?", (patient_id,))
    rows = cursor.fetchall()

    conn.close()

    # Convert SQLite rows into dictionaries for the API response
    appointments = [dict(row) for row in rows]

    if not appointments:
        return {
            "success": True,
            "message": "No appointments found.",
            "appointments": []
        }

    return {
        "success": True,
        "appointments": appointments
    }