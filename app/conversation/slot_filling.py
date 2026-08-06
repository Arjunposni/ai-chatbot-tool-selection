"""
slot_filling.py

Determines which parameters are still required
before a healthcare tool can be executed.
"""

from app.tools.schema import TOOL_SCHEMA


# ---------------------------------------------------------
# Required parameters for every tool
# (patient_id is injected automatically)
# ---------------------------------------------------------

REQUIRED_SLOTS = {
    tool["name"]: [
        parameter
        for parameter in tool["parameters"]
        if parameter != "patient_id"
    ]
    for tool in TOOL_SCHEMA
}


# ---------------------------------------------------------
# Questions used for slot filling
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Values that indicate the LLM guessed a placeholder
# instead of a real value — these should be treated as
# missing, not as a valid answer.
# ---------------------------------------------------------

_PLACEHOLDER_VALUES = {
    "unknown",
    "n/a",
    "na",
    "none",
    "not specified",
    "unspecified",
    "tbd",
    "",
}


def required_slots(intent: str) -> list[str]:
    """
    Return the required parameters for a tool.
    """

    return REQUIRED_SLOTS.get(intent, [])


def missing_slots(intent: str, parameters: dict) -> list[str]:
    """
    Return all required parameters that
    are currently missing (including placeholder
    values like "unknown" that the LLM sometimes
    guesses instead of leaving the field empty).
    """

    missing = []

    for slot in required_slots(intent):

        value = parameters.get(slot)

        if value is None:
            missing.append(slot)

        elif isinstance(value, str) and value.strip().lower() in _PLACEHOLDER_VALUES:
            missing.append(slot)

    return missing


def next_question(intent: str, parameters: dict):
    """
    Return the next question to ask.

    Returns:
        (slot, question)

    or

        (None, None)
    """

    missing = missing_slots(intent, parameters)

    if not missing:
        return None, None

    slot = missing[0]

    question = (
        SLOT_QUESTIONS
        .get(intent, {})
        .get(slot, f"Please provide {slot}.")
    )

    return slot, question


def is_complete(intent: str, parameters: dict) -> bool:
    """
    Returns True if all required parameters
    have been collected.
    """

    return len(missing_slots(intent, parameters)) == 0