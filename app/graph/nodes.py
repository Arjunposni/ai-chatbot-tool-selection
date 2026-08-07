"""
nodes.py

LangGraph nodes for the Healthcare AI chatbot.

Each node performs one step of the chatbot workflow and
updates the shared ChatState.
"""

from app.graph.state import ChatState
from app.conversation.parameter_extractor import extract_parameter
from app.conversation.date_utils import normalize_date, check_past_date
from app.intent.hybrid import detect_intent_hybrid
from app.intent.parameter_parser import extract_parameters

from app.rag.faq_retriever import search_faq

from app.services.tool_executor import execute_tool

from app.conversation.constants import CANCEL_KEYWORDS
from app.conversation.slot_filling import next_question

from app.conversation.session_manager import (
    create_session,
    get_session,
    update_parameter,
    set_waiting_for,
    clear_session,
)


# Markers that indicate a genuine system/API failure rather than a
# real "no match" — must be surfaced distinctly, not silently routed
# into RAG or a generic "couldn't understand" response.
_SYSTEM_ERROR_MARKERS = [
    "429",
    "resource_exhausted",
    "authentication",
    "invalid api key",
    "connection",
    "timeout",
    "network",
    "internal server error",
]


# ==========================================================
# Resume Conversation
# ==========================================================

def resume_conversation_node(state: ChatState) -> ChatState:
    """
    Load any existing conversation session.
    """

    patient_id = state["patient_id"]

    session = get_session(patient_id)

    state["session"] = session

    return state


# ==========================================================
# Continue Existing Conversation
# ==========================================================

def continue_conversation_node(state: ChatState) -> ChatState:
    """
    Continue an existing slot-filling conversation.

    Also handles cancellation here (only meaningful while a
    conversation is actually active) and rejects invalid dates
    (e.g. a past date) before accepting them.
    """

    session = state.get("session")

    if not session:
        return state

    message = state["message"].strip().lower()

    # Cancel only applies to an active conversation, and only on an
    # exact keyword match — not a substring match on any message.
    if message in CANCEL_KEYWORDS:
        clear_session(state["patient_id"])
        state["matched"] = False
        state["intent"] = None
        state["waiting_for"] = None
        state["method"] = "conversation"
        state["response"] = (
            "No problem, I've cancelled that. How else can I help?"
        )
        return state

    waiting_for = session.get("waiting_for")

    if not waiting_for:
        return state

    # Reject an invalid/past date before accepting it as the answer.
    if waiting_for == "date":
        past_error = check_past_date(state["message"])
        if past_error:
            state["date_error"] = past_error
            state["intent"] = session["intent"]
            state["parameters"] = session["parameters"]
            state["waiting_for"] = waiting_for
            return state

    value = extract_parameter(
        waiting_for,
        state["message"],
    )

    update_parameter(
        state["patient_id"],
        waiting_for,
        value,
    )

    session = get_session(
        state["patient_id"],
    )

    state["intent"] = session["intent"]
    state["parameters"] = session["parameters"]

    # We have already filled the missing slot,
    # so don't keep waiting for the old one.
    state["waiting_for"] = None

    return state


# ==========================================================
# Detect Intent
# ==========================================================

def detect_intent_node(state: ChatState) -> ChatState:
    """
    Detect user intent using the hybrid detector.

    Distinguishes a genuine system/API error from a real
    "no tool matched" case, so rate limits and API failures
    aren't silently treated as ambiguous input.
    """

    result = detect_intent_hybrid(
        state["message"],
        state["patient_id"],
    )

    state["matched"] = result["matched"]
    state["method"] = result["method"]
    state["intent"] = result.get("intent")
    state["all_intents"] = result.get("all_intents", [])
    state["parameters"] = result.get("parameters", {})

    if not result["matched"]:
        reason = (result.get("reason") or "").lower()
        if any(marker in reason for marker in _SYSTEM_ERROR_MARKERS):
            state["method"] = "error"
            state["response"] = (
                "⚠️ The AI service is temporarily unavailable. "
                "Please try again later."
            )

    return state


# ==========================================================
# Extract Parameters
# ==========================================================

def parameter_node(state: ChatState) -> ChatState:
    """
    Extract parameters from the user's message, then validate
    any date found (rejecting placeholders/past dates).
    """

    if not state.get("intent"):
        return state

    parsed = extract_parameters(
        state["intent"],
        state["message"],
    )

    state["parameters"].update(parsed)

    state["parameters"]["patient_id"] = state["patient_id"]

    if "date" in state["parameters"]:

        raw_date = str(state["parameters"]["date"])
        past_error = check_past_date(raw_date)

        if past_error:
            state["date_error"] = past_error
            del state["parameters"]["date"]
        else:
            normalized = normalize_date(raw_date)
            if normalized is None:
                del state["parameters"]["date"]
            else:
                state["parameters"]["date"] = normalized

    return state


# ==========================================================
# Multi Intent
# ==========================================================

def multi_intent_node(state: ChatState) -> ChatState:
    """
    Execute multiple detected intents.

    Only reached when the workflow router has already confirmed
    every intent has complete required parameters (see
    execution_router in workflow.py).
    """

    all_intents = state.get(
        "all_intents",
        [],
    )

    if len(all_intents) <= 1:
        return state

    combined_results = []
    response_parts = []

    for item in all_intents:

        params = {
            **item["parameters"],
            "patient_id": state["patient_id"],
        }

        success, result = execute_tool(
            item["intent"],
            params,
        )

        combined_results.append(
            {
                "intent": item["intent"],
                "result": result,
            }
        )

        message = result.get("message")

        if message is None:

            if "appointments" in result:

                appointments = result["appointments"]

                message = (
                    f"Found {len(appointments)} appointment(s)."
                    if appointments
                    else "No appointments found."
                )

            elif "results" in result:

                results = result["results"]

                message = (
                    f"Found {len(results)} test result(s)."
                    if results
                    else "No test results found."
                )

            else:

                message = (
                    "Action completed successfully."
                )

        response_parts.append(message)

    state["tool_result"] = {
        "multi_results": combined_results,
    }

    state["response"] = " ".join(response_parts)

    clear_session(
        state["patient_id"],
    )

    return state


# ==========================================================
# FAQ / RAG
# ==========================================================

def rag_node(state: ChatState) -> ChatState:
    """
    Search the FAQ knowledge base. Falls back to a clarification
    message if nothing relevant is found, rather than leaving
    state["response"] unset.
    """

    faq = search_faq(
        state["message"],
    )

    state["faq"] = faq

    if faq.get("matched"):
        state["response"] = faq["answer"]
        state["method"] = "rag"
    else:
        state["response"] = (
            "I'm sorry, I couldn't understand your request. "
            "I can help with appointments, prescriptions, "
            "test results, and healthcare questions."
        )
        state["method"] = "unknown"

    return state


# ==========================================================
# Slot Filling
# ==========================================================

def slot_filling_node(state: ChatState) -> ChatState:
    """
    Ask for any missing required parameters. If a date was just
    rejected as invalid, prepend that explanation to the question.
    """

    slot, question = next_question(
        state["intent"],
        state["parameters"],
    )

    if slot:

        if slot == "date" and state.get("date_error"):
            question = f"{state['date_error']} {question}"

        create_session(
            state["patient_id"],
            state["intent"],
        )

        for key, value in state["parameters"].items():

            update_parameter(
                state["patient_id"],
                key,
                value,
            )

        set_waiting_for(
            state["patient_id"],
            slot,
        )

        state["waiting_for"] = slot
        state["response"] = question

    else:

        state["waiting_for"] = None

    return state


# ==========================================================
# Execute Tool
# ==========================================================

def execute_tool_node(state: ChatState) -> ChatState:
    """
    Execute the selected healthcare tool.
    """

    success, result = execute_tool(
        state["intent"],
        state["parameters"],
    )

    state["tool_result"] = result

    response = result.get("message")

    if response is None:

        if "appointments" in result:

            appointments = result["appointments"]

            if appointments:
                response = (
                    f"Found {len(appointments)} appointment(s)."
                )
            else:
                response = "No appointments found."

        elif "results" in result:

            results = result["results"]

            response = (
                f"Found {len(results)} test result(s)."
                if results
                else "No test results found."
            )

        else:

            response = "Action completed successfully."

    state["response"] = response

    clear_session(
        state["patient_id"],
    )

    return state