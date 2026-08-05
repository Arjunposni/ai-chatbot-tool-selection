from app.intent.rule_based import detect_intent_rule_based
from app.intent.llm_based import detect_intent_llm_based
from app.tools.schema import TOOL_SCHEMA


# Intent -> required parameters (excluding patient_id)
_REQUIRED_PARAMS = {
    tool["name"]: [
        param for param in tool["parameters"]
        if param != "patient_id"
    ]
    for tool in TOOL_SCHEMA
}


def detect_intent_hybrid(user_query: str, patient_id: str = "p1") -> dict:
    """
    Hybrid intent detection strategy.

    1. Rule-based detection identifies the intent quickly.
    2. If required parameters are needed, Gemini extracts them.
    3. If Gemini fails, keep the rule-based intent instead of failing.
    """

    # Step 1: Rule-based detection
    rule_result = detect_intent_rule_based(user_query)

    # -------------------------------------------------
    # High-confidence rule-based match
    # -------------------------------------------------
    if rule_result["matched"] and rule_result["confidence"] == "high":

        intent = rule_result["intent"]

        required = _REQUIRED_PARAMS.get(intent, [])

        # Tool doesn't require additional parameters
        if not required:

            rule_result["parameters"] = {
                "patient_id": patient_id
            }

            rule_result["method"] = "hybrid (rule_based)"

            return rule_result

        # Tool requires parameters -> ask Gemini to extract them
        llm_result = detect_intent_llm_based(
            user_query,
            patient_id=patient_id
        )

        # Gemini successfully extracted parameters
        if llm_result.get("matched"):

            params = llm_result.get("parameters", {})

            params.setdefault("patient_id", patient_id)

            return {
                "matched": True,
                "intent": intent,
                "parameters": params,
                "confidence": "high",
                "method": "hybrid (rule + llm)"
            }

        # -------------------------------------------------
        # Gemini failed
        # -------------------------------------------------
        # Keep the detected intent and let the chatbot
        # collect the missing information later.
        return {
            "matched": True,
            "intent": intent,
            "parameters": {
                "patient_id": patient_id
            },
            "confidence": "high",
            "method": "hybrid (rule only)",
            "warning": llm_result.get("reason")
        }

    # -------------------------------------------------
    # No rule-based match -> let Gemini decide
    # -------------------------------------------------

    llm_result = detect_intent_llm_based(
        user_query,
        patient_id=patient_id
    )

    llm_result["method"] = "hybrid (llm)"

    return llm_result