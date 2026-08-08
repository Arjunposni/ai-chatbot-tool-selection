"""
parameter_parser.py

Handles parameter extraction for both:
1. The user's initial message.
2. Follow-up messages during slot filling.
"""

import re

from app.conversation.date_utils import normalize_date


# ==========================================================
# Supported Specialties
# ==========================================================

SPECIALTIES = {
    "cardiology",
    "dermatology",
    "orthopedics",
    "neurology",
    "pediatrics",
    "dentistry",
    "ent",
    "ophthalmology",
    "gynecology",
}


# ==========================================================
# Initial Message Parameter Extraction
# ==========================================================

def extract_parameters(intent: str, message: str) -> dict:
    """
    Extract tool parameters from the user's initial message.

    Example:

        "Book a cardiology appointment tomorrow"

    Returns:

        {
            "specialty": "Cardiology",
            "date": "<normalized date>"
        }
    """

    text = message.lower().strip()
    params = {}

    # ======================================================
    # Book Appointment
    # ======================================================

    if intent == "book_appointment":

        # --------------------------------------------------
        # Extract specialty
        # --------------------------------------------------

        for specialty in SPECIALTIES:

            pattern = rf"\b{re.escape(specialty)}\b"

            if re.search(pattern, text):
                params["specialty"] = specialty.title()
                break

        # --------------------------------------------------
        # Extract date
        # --------------------------------------------------

        date_patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b",
        ]

        date_found = None

        for pattern in date_patterns:

            match = re.search(pattern, message)

            if match:
                date_found = match.group()
                break

        # Natural language dates

        if date_found is None:

            if "today" in text:
                date_found = "today"

            elif "tomorrow" in text:
                date_found = "tomorrow"

            elif "yesterday" in text:
                date_found = "yesterday"

        # Normalize and validate date

        if date_found is not None:

            normalized = normalize_date(date_found)

            # normalize_date returns None for
            # invalid/past dates.

            if normalized is not None:
                params["date"] = normalized

    # ======================================================
    # Prescription Refill
    # ======================================================

    elif intent == "request_prescription_refill":

        match = re.search(
            r"refill\s+(.+)",
            message,
            re.IGNORECASE,
        )

        if match:

            medication = match.group(1).strip()

            # These are not actual medication names.

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


# ==========================================================
# Follow-up Parameter Extraction
# ==========================================================

def extract_parameter(slot: str, message: str):
    """
    Extract the value for a specific missing slot
    from the user's latest reply.

    This is used during multi-turn slot filling.

    Returns:
        A valid parameter value.

        Returns "" when the value is invalid,
        so slot filling can ask again.
    """

    text = message.strip()

    # ======================================================
    # Specialty
    # ======================================================

    if slot == "specialty":

        candidate = text.lower().strip()

        if candidate in SPECIALTIES:
            return candidate.title()

        return ""

    # ======================================================
    # Medication
    # ======================================================

    if slot == "medication":

        match = re.search(
            r"refill\s+(.+)",
            text,
            re.IGNORECASE,
        )

        if match:

            medication = match.group(1).strip()

            if medication:
                return medication

            return ""

        return text if text else ""

    # ======================================================
    # Date
    # ======================================================

    if slot == "date":

        normalized = normalize_date(text)

        # Invalid or past date

        if normalized is None:
            return ""

        return normalized

    # ======================================================
    # Default
    # ======================================================

    return text