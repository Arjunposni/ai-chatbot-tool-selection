from app.intent.rule_based import detect_intent_rule_based
from app.intent.llm_based import detect_intent_llm_based


def detect_intent_hybrid(user_query: str, patient_id: str = "p1") -> dict:
    """
    Tries rule-based first (fast, free). Falls back to LLM-based
    if rule-based fails to confidently match a single intent.
    """
    rule_result = detect_intent_rule_based(user_query)

    if rule_result["matched"] and rule_result["confidence"] == "high":
        # Rule-based succeeded confidently — use it, no LLM call needed
        rule_result["method"] = "hybrid (rule_based path)"
        return rule_result

    # Rule-based failed or was ambiguous — fall back to LLM
    llm_result = detect_intent_llm_based(user_query, patient_id=patient_id)
    llm_result["method"] = "hybrid (llm_based fallback)"
    llm_result["rule_based_attempt"] = rule_result  # keep for debugging/eval
    return llm_result