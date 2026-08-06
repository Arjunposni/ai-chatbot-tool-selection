"""
workflow.py

Builds the LangGraph workflow for the Healthcare AI chatbot.
"""

from typing import Literal

from langgraph.graph import StateGraph, START, END

from app.graph.state import ChatState

from app.graph.nodes import (
    resume_conversation_node,
    continue_conversation_node,
    cancel_node,
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
) -> Literal["continue_conversation", "cancel"]:
    """
    Continue an unfinished conversation if one exists.
    """

    session = state.get("session")

    if session and session.get("waiting_for"):
        return "continue_conversation"

    return "cancel"


def cancel_router(
    state: ChatState,
) -> Literal["detect_intent", "__end__"]:
    """
    End the workflow if the user cancelled.
    """

    if state.get("response"):
        return END

    return "detect_intent"


def intent_router(
    state: ChatState,
) -> Literal["parameters", "rag"]:
    """
    Route to parameter extraction or RAG.
    """

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
    Decide whether to execute one
    tool or multiple tools.
    """

    if len(
        state.get(
            "all_intents",
            [],
        )
    ) > 1:
        return "multi_intent"

    return "execute_tool"


# ==========================================================
# Build Graph
# ==========================================================

builder = StateGraph(ChatState)

# ----------------------------------------------------------
# Nodes
# ----------------------------------------------------------

builder.add_node(
    "resume",
    resume_conversation_node,
)

builder.add_node(
    "continue_conversation",
    continue_conversation_node,
)

builder.add_node(
    "cancel",
    cancel_node,
)

builder.add_node(
    "detect_intent",
    detect_intent_node,
)

builder.add_node(
    "parameters",
    parameter_node,
)

builder.add_node(
    "slot_filling",
    slot_filling_node,
)

builder.add_node(
    "router",
    lambda state: state,
)

builder.add_node(
    "execute_tool",
    execute_tool_node,
)

builder.add_node(
    "multi_intent",
    multi_intent_node,
)

builder.add_node(
    "rag",
    rag_node,
)

# ----------------------------------------------------------
# Start
# ----------------------------------------------------------

builder.add_edge(
    START,
    "resume",
)

# ----------------------------------------------------------
# Resume Routing
# ----------------------------------------------------------

builder.add_conditional_edges(
    "resume",
    resume_router,
    {
        "continue_conversation": "continue_conversation",
        "cancel": "cancel",
    },
)

# ----------------------------------------------------------
# Continue Existing Conversation
# ----------------------------------------------------------

builder.add_edge(
    "continue_conversation",
    "slot_filling",
)

# ----------------------------------------------------------
# Cancel Routing
# ----------------------------------------------------------

builder.add_conditional_edges(
    "cancel",
    cancel_router,
    {
        "detect_intent": "detect_intent",
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
    },
)

# ----------------------------------------------------------
# Parameter Extraction
# ----------------------------------------------------------

builder.add_edge(
    "parameters",
    "slot_filling",
)

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

builder.add_edge(
    "execute_tool",
    END,
)

builder.add_edge(
    "multi_intent",
    END,
)

# ----------------------------------------------------------
# FAQ / RAG
# ----------------------------------------------------------

builder.add_edge(
    "rag",
    END,
)

# ==========================================================
# Compile
# ==========================================================

graph = builder.compile()