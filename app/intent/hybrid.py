from app.intent.rule_based import detect_intent_rule_based
from app.intent.llm_based import detect_intent_llm_based
from app.tools.schema import TOOL_SCHEMA


# Intent -> required parameters (excluding patient_id)
_REQUIRED_PARAMS = {
    tool["name"]: [
        param
        for param in tool["parameters"]
        if param != "patient_id"
    ]
    for tool in TOOL_SCHEMA
}


# Markers suggesting the message may contain more than one request.
# If present, we skip the rule-based fast path even on a confident
# single-intent match, since rule-based cannot detect a SECOND
# intent hiding in the same message — only the LLM path checks
# all_intents.
_MULTI_INTENT_MARKERS = [" and ", " also ", ","]


def _looks_multi_intent(text: str) -> bool:
    lower = f" {text.lower()} "
    return any(marker in lower for marker in _MULTI_INTENT_MARKERS)


def detect_intent_hybrid(
    user_query: str,
    patient_id: str = "p1",
) -> dict:
    """
    Hybrid intent detection strategy.

    1. Rule-based detection identifies the intent quickly, UNLESS
       the message looks like it may contain multiple requests
       (e.g. joined by "and"/"also"/a comma) — those always go
       through the LLM path, since only the LLM can detect and
       return multiple intents (all_intents).
    2. If required parameters are needed, the LLM extracts them.
    3. If the LLM fails, keep the rule-based intent.
    """

    # -------------------------------------------------
    # Step 1: Rule-based detection
    # -------------------------------------------------

    rule_result = detect_intent_rule_based(user_query)

    # -------------------------------------------------
    # High-confidence single intent (only trusted outright
    # if the message doesn't look like a compound request)
    # -------------------------------------------------

    if (
        rule_result.get("matched")
        and rule_result.get("confidence") == "high"
        and not _looks_multi_intent(user_query)
    ):

        intent = rule_result["intent"]

        required = _REQUIRED_PARAMS.get(
            intent,
            [],
        )

        # Tool doesn't require additional parameters
        if not required:

            return {
                "matched": True,
                "intent": intent,
                "parameters": {
                    "patient_id": patient_id,
                },
                "confidence": "high",
                "method": "hybrid (rule_based)",
            }

        # Ask the LLM to extract parameters
        llm_result = detect_intent_llm_based(
            user_query,
            patient_id=patient_id,
        )

        if llm_result.get("matched"):

            params = llm_result.get(
                "parameters",
                {},
            )

            params.setdefault(
                "patient_id",
                patient_id,
            )

            return {
                "matched": True,
                "intent": intent,
                "parameters": params,
                "confidence": "high",
                "method": "hybrid (rule + llm)",
            }

        # LLM failed -> use rule intent only
        return {
            "matched": True,
            "intent": intent,
            "parameters": {
                "patient_id": patient_id,
            },
            "confidence": "high",
            "method": "hybrid (rule only)",
            "warning": llm_result.get("reason"),
        }

    # -------------------------------------------------
    # No confident single-intent rule match, OR the message
    # looks like it may contain multiple requests -> LLM handles
    # it (and can return all_intents for genuine multi-intent
    # messages)
    # -------------------------------------------------

    llm_result = detect_intent_llm_based(
        user_query,
        patient_id=patient_id,
    )

    llm_result["method"] = "hybrid (llm)"

    return llm_result