import os
from dotenv import load_dotenv
from app.intent.llm_gemini import detect_intent_llm_based as detect_gemini
from app.intent.llm_groq import detect_intent_llm_groq as detect_groq

load_dotenv()


def detect_intent_llm_based(user_query: str, patient_id: str = "p1") -> dict:
    """
    Dispatches to the configured LLM provider (gemini or groq) based on
    the LLM_PROVIDER environment variable.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "groq":
        return detect_groq(user_query, patient_id=patient_id)
    elif provider == "gemini":
        return detect_gemini(user_query, patient_id=patient_id)
    else:
        return {
            "matched": False,
            "intent": None,
            "confidence": "none",
            "method": "llm_based",
            "reason": f"Unknown LLM_PROVIDER '{provider}' — expected 'gemini' or 'groq'"
        }