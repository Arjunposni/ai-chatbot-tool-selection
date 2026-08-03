# Tool definitions used by the LLM for intent detection and tool selection
TOOL_SCHEMA = [
    {
        "name": "book_appointment",
        "description": "Books a doctor appointment for a patient with a given specialty and date.",
        "parameters": {
            "patient_id": "string",
            "specialty": "string",
            "date": "string"
        }
    },
    {
        "name": "check_appointment_status",
        "description": "Checks existing appointments for a patient.",
        "parameters": {
            "patient_id": "string"
        }
    },
    {
        "name": "request_prescription_refill",
        "description": "Requests a refill for a patient's existing medication.",
        "parameters": {
            "patient_id": "string",
            "medication": "string"
        }
    },
    {
        "name": "get_test_results",
        "description": "Retrieves lab or test results for a patient. Contains sensitive health data.",
        "parameters": {
            "patient_id": "string"
        }
    }
]