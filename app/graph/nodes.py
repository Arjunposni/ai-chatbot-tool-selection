"""
nodes.py

LangGraph nodes for the Healthcare AI chatbot.

Each node performs one step of the chatbot workflow and
updates the shared ChatState.
"""

from app.graph.state import ChatState
from app.conversation.parameter_extractor import extract_parameter
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
# ==========================================================
# Resume Existing Conversation
# ==========================================================

def continue_conversation_node(state: ChatState) -> ChatState:
    """
    Continue an existing slot-filling conversation.
    """

    session = state.get("session")

    if not session:
        return state

    waiting_for = session.get("waiting_for")

    if not waiting_for:
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
# Cancel Conversation
# ==========================================================

def cancel_node(state: ChatState) -> ChatState:
    """
    Cancel an active conversation if the user requests it.
    """

    message = state["message"].strip().lower()

    if any(
        keyword in message
        for keyword in CANCEL_KEYWORDS
    ):

        clear_session(
            state["patient_id"],
        )

        state["matched"] = False
        state["intent"] = None
        state["response"] = (
            "No problem, I've cancelled that. "
            "How else can I help?"
        )

    return state


# ==========================================================
# Detect Intent
# ==========================================================

def detect_intent_node(state: ChatState) -> ChatState:
    """
    Detect user intent using the hybrid detector.
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

    return state


# ==========================================================
# Extract Parameters
# ==========================================================

def parameter_node(state: ChatState) -> ChatState:
    """
    Extract parameters from the user's message.
    """

    if not state.get("intent"):
        return state

    parsed = extract_parameters(
        state["intent"],
        state["message"],
    )

    state["parameters"].update(parsed)

    state["parameters"]["patient_id"] = state["patient_id"]

    return state

# ==========================================================
# Multi Intent
# ==========================================================

def multi_intent_node(state: ChatState) -> ChatState:
    """
    Execute multiple detected intents.
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

                message = (
                    "Retrieved your test results."
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
    Search the FAQ knowledge base.
    """

    faq = search_faq(
        state["message"],
    )

    state["faq"] = faq

    if faq.get("matched"):
        state["response"] = faq["answer"]

    return state


# ==========================================================
# Slot Filling
# ==========================================================

def slot_filling_node(state: ChatState) -> ChatState:
    """
    Ask for any missing required parameters.
    """

    slot, question = next_question(
        state["intent"],
        state["parameters"],
    )

    if slot:

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

            response = "Retrieved your test results."

        else:

            response = "Action completed successfully."

    state["response"] = response

    clear_session(
        state["patient_id"],
    )

    return state