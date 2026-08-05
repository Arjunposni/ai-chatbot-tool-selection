"""
tool_executor.py

Executes healthcare tools through a single interface.
"""

from app.tools.appointment_tool import (
    book_appointment,
    check_appointment_status,
)

from app.tools.prescription_tool import (
    request_prescription_refill,
)

from app.tools.results_tool import (
    get_test_results,
)


# Intent -> Function mapping
TOOLS = {
    "book_appointment": book_appointment,
    "check_appointment_status": check_appointment_status,
    "request_prescription_refill": request_prescription_refill,
    "get_test_results": get_test_results,
}


def execute_tool(intent: str, parameters: dict):
    """
    Executes the tool corresponding to the detected intent.

    Returns
    -------
    success : bool
    tool_result : dict
    """

    executor = TOOLS.get(intent)

    if executor is None:
        return (
            False,
            {
                "message": f"No tool registered for '{intent}'."
            }
        )

    try:

        result = executor(**parameters)

        return (
            True,
            result,
        )

    except TypeError as e:

        return (
            False,
            {
                "message": "Missing or invalid tool parameters.",
                "error": str(e),
            },
        )

    except Exception as e:

        return (
            False,
            {
                "message": "Unexpected tool execution error.",
                "error": str(e),
            },
        )