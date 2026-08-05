"""
chat_service.py

Coordinates the complete chatbot workflow.

Flow
----
User
    ↓
Resume Existing Conversation?
    ↓
Intent Detection
    ↓
Extract Parameters
    ↓
Slot Filling
    ↓
Execute Tool(s)
"""

from app.intent.hybrid import detect_intent_hybrid
from app.intent.parameter_parser import extract_parameters

from app.rag.faq_retriever import search_faq

from app.conversation.constants import CANCEL_KEYWORDS
from app.conversation.session_manager import (
    create_session,
    get_session,
    update_parameter,
    set_waiting_for,
    clear_session,
)

from app.conversation.slot_filling import next_question
from app.conversation.parameter_extractor import extract_parameter

from app.services.tool_executor import execute_tool


def process_chat(message: str, patient_id: str = "p1") -> dict:
    """
    Main chatbot workflow.
    """

    # ==========================================================
    # STEP 1 : Resume an existing conversation
    # ==========================================================

    session = get_session(patient_id)

    # User cancelled an active conversation.
    if session and message.strip().lower() in CANCEL_KEYWORDS:
        clear_session(patient_id)

        return {
            "intent_detected": None,
            "method_used": "conversation",
            "tool_result": None,
            "response": (
                "No problem, I've cancelled that. "
                "How else can I help?"
            ),
        }

    # ----------------------------------------------------------
    # Continue an existing conversation
    # ----------------------------------------------------------

    if session:

        intent = session["intent"]
        waiting_for = session["waiting_for"]

        if waiting_for:

            value = extract_parameter(
                waiting_for,
                message,
            )

            update_parameter(
                patient_id,
                waiting_for,
                value,
            )

        session = get_session(patient_id)

        params = session["parameters"]
        params["patient_id"] = patient_id

        slot, question = next_question(
            intent,
            params,
        )

        if slot:

            set_waiting_for(
                patient_id,
                slot,
            )

            return {
                "intent_detected": intent,
                "method_used": "conversation",
                "tool_result": None,
                "response": question,
            }

        success, tool_result = execute_tool(
            intent,
            params,
        )

        clear_session(patient_id)

        response = tool_result.get("message")

        if response is None:

            if "appointments" in tool_result:

                appointments = tool_result["appointments"]

                response = (
                    f"Found {len(appointments)} appointment(s)."
                    if appointments
                    else "No appointments found."
                )

            elif "results" in tool_result:

                results = tool_result["results"]

                response = (
                    f"Found {len(results)} test result(s)."
                    if results
                    else "No test results found."
                )

            else:

                response = "Action completed successfully."

        return {
            "intent_detected": intent,
            "method_used": "conversation",
            "tool_result": tool_result,
            "response": response,
        }

    # ==========================================================
    # STEP 2 : Detect Intent
    # ==========================================================

    intent_result = detect_intent_hybrid(
        message,
        patient_id,
    )
        # ==========================================================
    # STEP 3 : FAQ / RAG
    # ==========================================================

    if not intent_result["matched"]:

        reason = (intent_result.get("reason") or "").lower()

        # Only genuine API failures should stop execution.
        # Groq tool validation failures should simply fall back to RAG.
        is_system_error = any(
            marker in reason
            for marker in [
                "429",
                "resource_exhausted",
                "authentication",
                "invalid api key",
                "connection",
                "timeout",
                "network",
                "internal server error",
            ]
        )

        if is_system_error:
            return {
                "intent_detected": None,
                "method_used": "error",
                "tool_result": None,
                "response": (
                    "⚠️ The AI service is temporarily unavailable. "
                    "Please try again later."
                ),
            }

        faq = search_faq(message)

        if faq["matched"]:

            return {
                "intent_detected": "faq_lookup",
                "method_used": "rag",
                "tool_result": faq,
                "response": faq["answer"],
            }

        return {
            "intent_detected": None,
            "method_used": "unknown",
            "tool_result": None,
            "response": (
                "I'm sorry, I couldn't understand your request. "
                "I can help with appointments, prescriptions, "
                "test results, and healthcare questions."
            ),
        }

    # ==========================================================
    # STEP 4 : Extract Parameters
    # ==========================================================

    intent = intent_result["intent"]

    params = intent_result.get(
        "parameters",
        {},
    )

    parsed_params = extract_parameters(
        intent,
        message,
    )

    params.update(parsed_params)

    params["patient_id"] = patient_id

    # ==========================================================
    # STEP 5 : Slot Filling
    # ==========================================================

    slot, question = next_question(
        intent,
        params,
    )

    if slot:

        create_session(
            patient_id,
            intent,
        )

        for key, value in params.items():

            update_parameter(
                patient_id,
                key,
                value,
            )

        set_waiting_for(
            patient_id,
            slot,
        )

        return {
            "intent_detected": intent,
            "method_used": intent_result["method"],
            "tool_result": None,
            "response": question,
        }
    # ==========================================================
    # STEP 6 : Execute Tool(s)
    # ==========================================================

    all_intents = intent_result.get(
        "all_intents",
        [
            {
                "intent": intent,
                "parameters": params,
            }
        ],
    )

    # ----------------------------------------------------------
    # Multi-intent execution
    # ----------------------------------------------------------

    can_execute_all = (
        len(all_intents) > 1
        and all(
            next_question(
                item["intent"],
                {
                    **item["parameters"],
                    "patient_id": patient_id,
                },
            )[0]
            is None
            for item in all_intents
        )
    )

    if can_execute_all:

        combined_results = []
        response_parts = []

        for item in all_intents:

            item_params = {
                **item["parameters"],
                "patient_id": patient_id,
            }

            success, tool_result = execute_tool(
                item["intent"],
                item_params,
            )

            combined_results.append(
                {
                    "intent": item["intent"],
                    "result": tool_result,
                }
            )

            msg = tool_result.get("message")

            if msg is None:

                if "appointments" in tool_result:

                    appointments = tool_result["appointments"]

                    msg = (
                        f"Found {len(appointments)} appointment(s)."
                        if appointments
                        else "No appointments found."
                    )

                elif "results" in tool_result:

                    results = tool_result["results"]

                    msg = (
                        f"Found {len(results)} test result(s)."
                        if results
                        else "No test results found."
                    )

                elif "medication" in tool_result:

                    msg = (
                        f"Refill requested for "
                        f"{tool_result['medication']}."
                    )

                else:

                    msg = "Action completed successfully."

            response_parts.append(msg)

        return {
            "intent_detected": [
                item["intent"]
                for item in all_intents
            ],
            "method_used": intent_result["method"],
            "tool_result": {
                "multi_results": combined_results
            },
            "response": " ".join(response_parts),
        }

    # ----------------------------------------------------------
    # Single-intent execution
    # ----------------------------------------------------------

    success, tool_result = execute_tool(
        intent,
        params,
    )

    response = tool_result.get("message")

    if response is None:

        if "appointments" in tool_result:

            appointments = tool_result["appointments"]

            response = (
                f"Found {len(appointments)} appointment(s)."
                if appointments
                else "No appointments found."
            )

        elif "results" in tool_result:

            results = tool_result["results"]

            response = (
                f"Found {len(results)} test result(s)."
                if results
                else "No test results found."
            )

        elif "medication" in tool_result:

            response = (
                f"Refill requested for "
                f"{tool_result['medication']}."
            )

        else:

            response = "Action completed successfully."

    return {
        "intent_detected": intent,
        "method_used": intent_result["method"],
        "tool_result": tool_result,
        "response": response,
    }