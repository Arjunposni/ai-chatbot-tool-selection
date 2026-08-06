"""
date_utils.py

Utility functions for parsing and validating
appointment dates.
"""

import re
from datetime import datetime, timedelta


def normalize_date(text: str) -> str | None:
    """
    Normalize a user-supplied date.

    Returns
    -------
    str
        Date in YYYY-MM-DD format.

    None
        If the date is invalid or in the past.
    """

    text = text.strip()
    lower = text.lower()

    today = datetime.today().date()

    # ==========================================================
    # Natural language dates
    # ==========================================================

    if lower == "today":
        return today.strftime("%Y-%m-%d")

    if lower == "tomorrow":
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    if lower == "yesterday":
        return None

    # ==========================================================
    # YYYY-MM-DD
    # ==========================================================

    match = re.search(
        r"\b\d{4}-\d{2}-\d{2}\b",
        text,
    )

    if match:

        try:

            date_obj = datetime.strptime(
                match.group(),
                "%Y-%m-%d",
            ).date()

            if date_obj < today:
                return None

            return date_obj.strftime("%Y-%m-%d")

        except ValueError:
            return None

    # ==========================================================
    # DD/MM/YYYY or DD/MM/YY
    # ==========================================================

    match = re.search(
        r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b",
        text,
    )

    if match:

        value = match.group()

        for fmt in ("%d/%m/%Y", "%d/%m/%y"):

            try:

                date_obj = datetime.strptime(
                    value,
                    fmt,
                ).date()

                if date_obj < today:
                    return None

                return date_obj.strftime("%Y-%m-%d")

            except ValueError:
                continue

        return None

    # ==========================================================
    # Unknown format
    # ==========================================================

    return None