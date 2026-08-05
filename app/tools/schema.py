"""
Tool definitions used by the LLM for intent detection
and function calling.
"""

TOOL_SCHEMA = [

    {
        "name": "book_appointment",
        "description": (
            "Book or schedule a doctor's appointment for a patient. "
            "Use this whenever the user wants to book, schedule, "
            "arrange, reserve, or make an appointment with a doctor "
            "or specialist. Extract the specialty and appointment date "
            "whenever they are mentioned."
        ),
        "parameters": {
            "patient_id": "string",
            "specialty": "string",
            "date": "string",
        },
    },

    {
        "name": "check_appointment_status",
        "description": (
            "Retrieve, view, check, list, or show a patient's existing "
            "appointments. Use this whenever the user asks about upcoming, "
            "current, previous, scheduled, or next appointments."
        ),
        "parameters": {
            "patient_id": "string",
        },
    },

    {
        "name": "request_prescription_refill",
        "description": (
            "Request, renew, or refill a patient's prescription medication. "
            "Use this whenever the user asks to refill medication, renew a "
            "prescription, get more medicine, continue medication, or "
            "mentions medicines such as Metformin, insulin, antibiotics, "
            "blood pressure medication, or any other prescribed drug. "
            "Extract the medication name whenever it is provided."
        ),
        "parameters": {
            "patient_id": "string",
            "medication": "string",
        },
    },

    {
        "name": "get_test_results",
        "description": (
            "Retrieve, view, check, or show a patient's laboratory or "
            "diagnostic test results. Use this whenever the user asks for "
            "blood test results, lab reports, scan reports, X-ray results, "
            "MRI results, medical reports, or investigation results."
        ),
        "parameters": {
            "patient_id": "string",
        },
    },

]