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


def detect_intent_hybrid(
    user_query: str,
    patient_id: str = "p1",
) -> dict:
    """
    Hybrid intent detection strategy.

    1. Rule-based detection identifies the intent quickly.
    2. If required parameters are needed, the LLM extracts them.
    3. If the LLM fails, keep the rule-based intent.
    """

    # -------------------------------------------------
    # Step 1: Rule-based detection
    # -------------------------------------------------

    rule_result = detect_intent_rule_based(user_query)

    # -------------------------------------------------
    # Multi-intent detected by rule-based detector
    # -------------------------------------------------

    if rule_result.get("all_intents"):

        for item in rule_result["all_intents"]:

            item.setdefault("parameters", {})

            item["parameters"].setdefault(
                "patient_id",
                patient_id,
            )

        return {
            "matched": True,
            "all_intents": rule_result["all_intents"],
            "confidence": "high",
            "method": "hybrid (rule_based)",
        }

    # -------------------------------------------------
    # High-confidence single intent
    # -------------------------------------------------

    if (
        rule_result.get("matched")
        and rule_result.get("confidence") == "high"
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
    # No rule-based match -> LLM fallback
    # -------------------------------------------------

    llm_result = detect_intent_llm_based(
        user_query,
        patient_id=patient_id,
    )

    llm_result["method"] = "hybrid (llm)"

    return llm_result