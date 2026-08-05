"""
parameter_extractor.py

Extracts parameter values from the user's reply during
a multi-turn conversation.
"""

import re
from datetime import datetime, timedelta


def extract_parameter(slot: str, message: str):
    """
    Extract the value for the requested slot
    from the user's latest reply.
    """

    text = message.strip()

    # ==========================================================
    # Specialty
    # ==========================================================

    if slot == "specialty":
        return text.title()

    # ==========================================================
    # Medication
    # ==========================================================

    if slot == "medication":

        # User may reply:
        # "Refill Metformin 500mg"
        match = re.search(
            r"refill\s+(.+)",
            text,
            re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

        # User may simply reply:
        # "Metformin 500mg"
        return text

    # ==========================================================
    # Date
    # ==========================================================

    if slot == "date":

        lower = text.lower()

        # Natural language dates
        if lower == "today":
            return datetime.today().strftime("%Y-%m-%d")

        if lower == "tomorrow":
            return (
                datetime.today() +
                timedelta(days=1)
            ).strftime("%Y-%m-%d")

        # dd/mm/yyyy OR dd/mm/yy
        match = re.search(
            r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b",
            text,
        )

        if match:
            return match.group()

        # yyyy-mm-dd
        match = re.search(
            r"\b\d{4}-\d{2}-\d{2}\b",
            text,
        )

        if match:
            return match.group()

        # Return original text if no pattern matched
        return text

    # ==========================================================
    # Default
    # ==========================================================

    return text