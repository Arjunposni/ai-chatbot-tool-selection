"""
parameter_parser.py

Extracts tool parameters directly from
the user's first message using lightweight rules.
"""

import re

from app.conversation.date_utils import normalize_date


SPECIALTIES = [
    "cardiology",
    "dermatology",
    "orthopedics",
    "neurology",
    "pediatrics",
    "dentistry",
    "ent",
    "ophthalmology",
    "gynecology",
]


def extract_parameters(intent: str, message: str) -> dict:
    """
    Extract tool parameters from the user's message.
    """

    text = message.lower().strip()
    params = {}

    # ==========================================================
    # Book Appointment
    # ==========================================================

    if intent == "book_appointment":

        # Extract specialty
        for specialty in SPECIALTIES:

            pattern = rf"\b{re.escape(specialty)}\b"

            if re.search(pattern, text):
                params["specialty"] = specialty.title()
                break

        # Extract date
        patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b",
        ]

        date_found = None

        for pattern in patterns:

            match = re.search(pattern, message)

            if match:
                date_found = match.group()
                break

        if date_found is None:

            if "today" in text:
                date_found = "today"

            elif "tomorrow" in text:
                date_found = "tomorrow"

            elif "yesterday" in text:
                date_found = "yesterday"

        if date_found is not None:

            normalized = normalize_date(date_found)

            # normalize_date returns None for invalid/past dates
            # (e.g. "yesterday") — only set the param if it's valid,
            # so slot filling correctly asks for a real date instead.
            if normalized is not None:
                params["date"] = normalized

    # ==========================================================
    # Prescription Refill
    # ==========================================================

    elif intent == "request_prescription_refill":

        match = re.search(
            r"refill\s+(.+)",
            message,
            re.IGNORECASE,
        )

        if match:

            medication = match.group(1).strip()

            # These phrases are not actual medication names.
            generic_phrases = {
                "my prescription",
                "prescription",
                "medicine",
                "my medicine",
                "medication",
                "my medication",
            }

            if medication.lower() not in generic_phrases:
                params["medication"] = medication

    return params