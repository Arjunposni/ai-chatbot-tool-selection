from app.db import get_connection


def get_test_results(patient_id: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM test_results
        WHERE patient_id = ?
        ORDER BY date DESC
        """,
        (patient_id,),
    )

    rows = cursor.fetchall()

    conn.close()

    results = [dict(row) for row in rows]

    if not results:
        return {
            "success": True,
            "message": "No test results found.",
            "results": [],
        }

    return {
        "success": True,
        "message": f"Found {len(results)} test result(s).",
        "results": results,
    }