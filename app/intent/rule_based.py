import re

# Maps each supported intent to regex patterns
INTENT_KEYWORDS = {
    "book_appointment": [
        r"\bbook\b.*\bappointment\b",
        r"\bschedule\b.*\bappointment\b",
        r"\bsee\b.*\bdoctor\b",
        r"\bappointment\b.*\bwith\b",
    ],
    "check_appointment_status": [
        r"\bcheck\b.*\bappointment\b",
        r"\bmy\b.*\bappointments\b",
        r"\bappointment\b.*\bstatus\b",
        r"\bupcoming\b.*\bappointment\b",
    ],
    "request_prescription_refill": [
        r"\brefill\b",
        r"\bprescription\b.*\brefill\b",
        r"\brenew\b.*\bmedication\b",
    ],
    "get_test_results": [
        r"\btest\b.*\bresults?\b",
        r"\blab\b.*\bresults?\b",
        r"\bmy\b.*\breports?\b",
    ],
}


def detect_intent_rule_based(user_query: str) -> dict:
    """
    Fast regex-based intent detection.
    Supports both single-intent and multi-intent queries.
    """

    query = user_query.lower()

    matches = []

    for intent, patterns in INTENT_KEYWORDS.items():

        for pattern in patterns:

            if re.search(pattern, query):

                matches.append(
                    {
                        "intent": intent,
                        "parameters": {},
                    }
                )

                break

    # ------------------------------------------------------
    # No match
    # ------------------------------------------------------

    if not matches:

        return {
            "matched": False,
            "intent": None,
            "confidence": "none",
            "method": "rule_based",
            "reason": "No keyword pattern matched",
        }

    # ------------------------------------------------------
    # Single intent
    # ------------------------------------------------------

    if len(matches) == 1:

        return {
            "matched": True,
            "intent": matches[0]["intent"],
            "parameters": {},
            "confidence": "high",
            "method": "rule_based",
        }

    # ------------------------------------------------------
    # Multi-intent
    # ------------------------------------------------------

    return {
        "matched": True,
        "all_intents": matches,
        "confidence": "high",
        "method": "rule_based",
    }