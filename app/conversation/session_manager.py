"""
session_manager.py

Maintains the conversation state for each patient.

For this assignment an in-memory dictionary is sufficient.
In production this would typically be Redis or a database.
"""

from copy import deepcopy


# patient_id -> conversation state
_SESSIONS = {}


def create_session(patient_id: str, intent: str):
    """
    Start a new conversation.
    """

    _SESSIONS[patient_id] = {
        "intent": intent,
        "parameters": {},
        "waiting_for": None,
        "active": True,
    }


def get_session(patient_id: str):
    """
    Return the current conversation.
    """

    return _SESSIONS.get(patient_id)


def update_parameter(patient_id: str, key: str, value):
    """
    Save one collected parameter.
    """

    session = get_session(patient_id)

    if session is None:
        return

    session["parameters"][key] = value


def set_waiting_for(patient_id: str, parameter: str | None):
    """
    Tell the chatbot which parameter
    it is currently waiting for.
    """

    session = get_session(patient_id)

    if session is None:
        return

    session["waiting_for"] = parameter


def clear_session(patient_id: str):
    """
    End the conversation.
    """

    _SESSIONS.pop(patient_id, None)


def has_active_session(patient_id: str) -> bool:
    """
    Returns True if the user is
    already in the middle of a conversation.
    """

    session = get_session(patient_id)

    return bool(session and session["active"])


def get_parameters(patient_id: str) -> dict:
    """
    Return all collected parameters.
    """

    session = get_session(patient_id)

    if session is None:
        return {}

    return deepcopy(session["parameters"])


def get_waiting_for(patient_id: str):
    """
    Returns the parameter the bot
    is currently expecting.
    """

    session = get_session(patient_id)

    if session is None:
        return None

    return session["waiting_for"]


def complete_session(patient_id: str):
    """
    Mark the conversation as completed.
    """

    session = get_session(patient_id)

    if session is None:
        return

    session["active"] = False