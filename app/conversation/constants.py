"""
constants.py

Shared conversation constants.
"""

# Words that cancel the current conversation
CANCEL_KEYWORDS = {
    "cancel",
    "stop",
    "quit",
    "exit",
    "abort",
    "never mind",
    "nevermind",
    "start over",
    "restart",
    "reset",
}

# Questions for missing parameters
SLOT_QUESTIONS = {

    "book_appointment": {
        "specialty": "Which specialty would you like to book an appointment for?",
        "date": "What date would you prefer?",
    },

    "request_prescription_refill": {
        "medication": "Which medication would you like to refill?",
    },

    "check_appointment_status": {},

    "get_test_results": {},
}