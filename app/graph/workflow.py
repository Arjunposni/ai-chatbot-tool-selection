"""
workflow.py

Builds the LangGraph workflow for the Healthcare AI chatbot.
"""

from typing import Literal

from langgraph.graph import StateGraph, START, END

from app.graph.state import ChatState
from app.conversation.slot_filling import next_question

from app.graph.nodes import (
    resume_conversation_node,
    continue_conversation_node,
    detect_intent_node,
    parameter_node,
    multi_intent_node,
    rag_node,
    slot_filling_node,
    execute_tool_node,
)


# ==========================================================
# Router Functions
# ==========================================================

def resume_router(
    state: ChatState,
) -> Literal["continue_conversation", "detect_intent"]:
    """
    Continue an unfinished conversation if one exists.
    Cancellation is handled inside continue_conversation_node,
    since it's only meaningful while a conversation is active.
    """

    session = state.get("session")

    if session and session.get("waiting_for"):
        return "continue_conversation"

    return "detect_intent"


def continue_router(
    state: ChatState,
) -> Literal["slot_filling", "__end__"]:
    """
    If continue_conversation_node already produced a final
    response (e.g. cancellation), end here. Otherwise proceed
    to slot filling.
    """

    if state.get("response"):
        return END

    return "slot_filling"


def intent_router(
    state: ChatState,
) -> Literal["parameters", "rag", "__end__"]:
    """
    Route to parameter extraction or RAG — or end immediately
    if a system error response was already set.
    """

    if state.get("response"):
        return END

    if state.get("matched"):
        return "parameters"

    return "rag"


def slot_router(
    state: ChatState,
) -> Literal["router", "__end__"]:
    """
    If slot filling is complete,
    continue to execution routing.
    """

    if state.get("waiting_for"):
        return END

    return "router"


def execution_router(
    state: ChatState,
) -> Literal["execute_tool", "multi_intent"]:
    """
    Decide whether to execute one tool or multiple tools.

    Only routes to multi-intent execution if EVERY detected
    intent already has its required parameters — otherwise
    falls back to executing just the primary intent (which has
    already passed slot filling), matching the original
    single-intent + slot-filling behavior.
    """

    all_intents = state.get("all_intents", [])

    if len(all_intents) > 1:

        complete = all(
            next_question(
                item["intent"],
                {**item["parameters"], "patient_id": state["patient_id"]},
            )[0] is None
            for item in all_intents
        )

        if complete:
            return "multi_intent"

    return "execute_tool"


# ==========================================================
# Build Graph
# ==========================================================

builder = StateGraph(ChatState)

# ----------------------------------------------------------
# Nodes
# ----------------------------------------------------------

builder.add_node("resume", resume_conversation_node)
builder.add_node("continue_conversation", continue_conversation_node)
builder.add_node("detect_intent", detect_intent_node)
builder.add_node("parameters", parameter_node)
builder.add_node("slot_filling", slot_filling_node)
builder.add_node("router", lambda state: state)
builder.add_node("execute_tool", execute_tool_node)
builder.add_node("multi_intent", multi_intent_node)
builder.add_node("rag", rag_node)

# ----------------------------------------------------------
# Start
# ----------------------------------------------------------

builder.add_edge(START, "resume")

# ----------------------------------------------------------
# Resume Routing
# ----------------------------------------------------------

builder.add_conditional_edges(
    "resume",
    resume_router,
    {
        "continue_conversation": "continue_conversation",
        "detect_intent": "detect_intent",
    },
)

# ----------------------------------------------------------
# Continue Existing Conversation
# ----------------------------------------------------------

builder.add_conditional_edges(
    "continue_conversation",
    continue_router,
    {
        "slot_filling": "slot_filling",
        END: END,
    },
)

# ----------------------------------------------------------
# Intent Routing
# ----------------------------------------------------------

builder.add_conditional_edges(
    "detect_intent",
    intent_router,
    {
        "parameters": "parameters",
        "rag": "rag",
        END: END,
    },
)

# ----------------------------------------------------------
# Parameter Extraction
# ----------------------------------------------------------

builder.add_edge("parameters", "slot_filling")

# ----------------------------------------------------------
# Slot Filling Routing
# ----------------------------------------------------------

builder.add_conditional_edges(
    "slot_filling",
    slot_router,
    {
        "router": "router",
        END: END,
    },
)

# ----------------------------------------------------------
# Execution Routing
# ----------------------------------------------------------

builder.add_conditional_edges(
    "router",
    execution_router,
    {
        "execute_tool": "execute_tool",
        "multi_intent": "multi_intent",
    },
)

# ----------------------------------------------------------
# Tool Execution
# ----------------------------------------------------------

builder.add_edge("execute_tool", END)
builder.add_edge("multi_intent", END)

# ----------------------------------------------------------
# FAQ / RAG
# ----------------------------------------------------------

builder.add_edge("rag", END)

# ==========================================================
# Compile
# ==========================================================

graph = builder.compile()