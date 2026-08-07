"""
date_utils.py

Shared date parsing/validation used by both the first-message
parameter parser and the follow-up slot-filling extractor.
"""

import re
from datetime import datetime, timedelta


PAST_DATE_MESSAGE = (
    "That date has already passed. Please provide a valid date — "
    "today or a date in the future."
)


def normalize_date(text: str):
    """
    Converts natural-language date references into an actual date
    (YYYY-MM-DD). Returns None for anything invalid/past so the
    caller can treat it as missing. Returns the original text
    unchanged if no recognizable date pattern is found at all.
    """
    lower = text.strip().lower()
    today = datetime.today().date()

    if lower == "today":
        return today.strftime("%Y-%m-%d")

    if lower == "tomorrow":
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    if lower == "yesterday":
        return None

    match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if match:
        try:
            parsed = datetime.strptime(match.group(), "%Y-%m-%d").date()
            return match.group() if parsed >= today else None
        except ValueError:
            pass

    match = re.search(r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b", text)
    if match:
        value = match.group()
        fmt = "%d/%m/%Y" if len(value.split("/")[-1]) == 4 else "%d/%m/%y"
        try:
            parsed = datetime.strptime(value, fmt).date()
            return value if parsed >= today else None
        except ValueError:
            pass

    return text


def check_past_date(text: str):
    """
    Returns a user-facing error message if `text` clearly resolves
    to a date that has already passed (e.g. "yesterday", or an
    explicit past date like 2024-01-01). Returns None if the text
    doesn't resolve to a recognizable past date — including cases
    where it isn't a recognizable date at all.
    """
    raw = text.strip().lower()
    today = datetime.today().date()

    if raw == "yesterday":
        return PAST_DATE_MESSAGE

    match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if match:
        try:
            parsed = datetime.strptime(match.group(), "%Y-%m-%d").date()
            if parsed < today:
                return PAST_DATE_MESSAGE
        except ValueError:
            pass

    match = re.search(r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b", text)
    if match:
        value = match.group()
        fmt = "%d/%m/%Y" if len(value.split("/")[-1]) == 4 else "%d/%m/%y"
        try:
            parsed = datetime.strptime(value, fmt).date()
            if parsed < today:
                return PAST_DATE_MESSAGE
        except ValueError:
            pass

    return None