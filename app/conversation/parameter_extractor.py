"""
parameter_extractor.py

Extracts parameter values from the user's reply during
a multi-turn conversation.
"""

import re

from app.conversation.date_utils import normalize_date


SUPPORTED_SPECIALTIES = {
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


def extract_parameter(slot: str, message: str):
    """
    Extract the value for the requested slot
    from the user's latest reply.

    Returns an empty string ("") when the value is invalid so
    slot_filling.py continues asking for that slot.
    """

    text = message.strip()

    # ==========================================================
    # Specialty
    # ==========================================================

    if slot == "specialty":

        candidate = text.lower().strip()

        if candidate in SUPPORTED_SPECIALTIES:
            return candidate.title()

        # Invalid specialty -> ask again
        return ""

    # ==========================================================
    # Medication
    # ==========================================================

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

    # ==========================================================
    # Date
    # ==========================================================

    if slot == "date":

        normalized = normalize_date(text)

        # Invalid or past date
        if normalized is None:
            return ""

        return normalized

    # ==========================================================
    # Default
    # ==========================================================

    return text