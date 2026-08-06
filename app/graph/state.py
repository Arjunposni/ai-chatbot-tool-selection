"""
state.py

Defines the shared state passed between LangGraph nodes.
"""

from typing import TypedDict, Optional, List, Dict, Any


class ChatState(TypedDict, total=False):
    """
    Shared state for the Healthcare AI chatbot.

    Every LangGraph node receives this dictionary,
    updates it, and returns it.
    """

    # ==========================================================
    # User Input
    # ==========================================================

    message: str
    patient_id: str

    # ==========================================================
    # Conversation
    # ==========================================================

    session: Optional[dict]
    waiting_for: Optional[str]

    # ==========================================================
    # Intent Detection
    # ==========================================================

    matched: bool
    intent: Optional[str]
    all_intents: List[dict]
    method: str

    # ==========================================================
    # Parameters
    # ==========================================================

    parameters: Dict[str, Any]

    # ==========================================================
    # FAQ / RAG
    # ==========================================================

    faq: Optional[dict]

    # ==========================================================
    # Tool Execution
    # ==========================================================

    tool_result: Optional[dict]

    # ==========================================================
    # Final Response
    # ==========================================================

    response: str

    # ==========================================================
    # Error Handling
    # ==========================================================

    error: Optional[str]

    # ==========================================================
    # Multi-intent Support
    # ==========================================================

    current_intent: Optional[str]
    multi_results: List[dict]