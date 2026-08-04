import re

# Maps each supported intent to regex patterns for fast rule-based detection
INTENT_KEYWORDS = {
    "book_appointment": [
        r"\bbook\b.*\bappointment\b",
        r"\bschedule\b.*\bappointment\b",
        r"\bsee\b.*\bdoctor\b",
        r"\bappointment\b.*\bwith\b"
    ],
    "check_appointment_status": [
        r"\bcheck\b.*\bappointment\b",
        r"\bmy\b.*\bappointments\b",
        r"\bappointment\b.*\bstatus\b",
        r"\bupcoming\b.*\bappointment\b"
    ],
    "request_prescription_refill": [
        r"\brefill\b",
        r"\bprescription\b.*\brefill\b",
        r"\brenew\b.*\bmedication\b"
    ],
    "get_test_results": [
        r"\btest\b.*\bresults?\b",
        r"\blab\b.*\bresults?\b",
        r"\bmy\b.*\breports?\b"
    ]
}


def detect_intent_rule_based(user_query: str) -> dict:
    """
    Matches the user query against predefined regex patterns.
    Returns the detected intent with confidence, or no match.
    """
    query_lower = user_query.lower()
    matches = []

    # Check the query against each intent's patterns
    for intent, patterns in INTENT_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                matches.append(intent)
                break

    # Exactly one intent matched
    if len(matches) == 1:
        return {
            "matched": True,
            "intent": matches[0],
            "confidence": "high",
            "method": "rule_based"
        }

    # Multiple matches require LLM disambiguation
    elif len(matches) > 1:
        return {
            "matched": False,
            "intent": None,
            "confidence": "low",
            "method": "rule_based",
            "reason": f"Multiple possible intents matched: {matches}"
        }

    # No matching pattern found
    else:
        return {
            "matched": False,
            "intent": None,
            "confidence": "none",
            "method": "rule_based",
            "reason": "No keyword pattern matched"
        }