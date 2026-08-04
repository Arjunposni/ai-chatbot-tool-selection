from app.intent.rule_based import detect_intent_rule_based
from app.intent.llm_based import detect_intent_llm_based
from app.tools.schema import TOOL_SCHEMA

# Build a lookup: intent name -> list of required params (excluding patient_id)
_REQUIRED_PARAMS = {
    tool["name"]: [p for p in tool["parameters"] if p != "patient_id"]
    for tool in TOOL_SCHEMA
}


def detect_intent_hybrid(user_query: str, patient_id: str = "p1") -> dict:
    rule_result = detect_intent_rule_based(user_query)

    if rule_result["matched"] and rule_result["confidence"] == "high":
        intent = rule_result["intent"]
        extra_params_needed = _REQUIRED_PARAMS.get(intent, [])

        if not extra_params_needed:
            # Rule-based is fully sufficient — no extra params needed
            rule_result["method"] = "hybrid (rule_based path)"
            rule_result["parameters"] = {"patient_id": patient_id}
            return rule_result
        # else: intent is known, but we still need the LLM to extract params

    # Fall back to LLM — either no rule match, ambiguous, or params needed
    llm_result = detect_intent_llm_based(user_query, patient_id=patient_id)
    llm_result["method"] = "hybrid (llm_based fallback)"
    llm_result["rule_based_attempt"] = rule_result
    return llm_result