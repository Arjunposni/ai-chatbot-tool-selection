import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.tools.schema import TOOL_SCHEMA

load_dotenv()

_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def _build_tool():
    """
    Convert TOOL_SCHEMA into Gemini function declarations.
    """

    function_declarations = []

    for tool in TOOL_SCHEMA:
        function_declarations.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters_json_schema=tool["parameters"],
            )
        )

    return types.Tool(
        function_declarations=function_declarations
    )


_tool = _build_tool()


def detect_intent_llm_based(
    user_query: str,
    patient_id: str = "p1",
    max_retries: int = 2,
) -> dict:
    """
    Uses Gemini Function Calling to determine which healthcare
    tool(s) should be executed and extracts their parameters.
    """

    prompt = f"""
You are an intelligent healthcare assistant.

Current patient_id: {patient_id}

Available tools:

1. book_appointment
2. check_appointment_status
3. request_prescription_refill
4. get_test_results

Your job is to select the correct tool(s) using function calling.

IMPORTANT RULES

• If the user asks for ONE task, call ONE function.

• If the user asks for MULTIPLE independent tasks,
call ONE FUNCTION FOR EACH TASK.

Examples

User:
"Check my appointments and refill my Metformin."

Functions:
- check_appointment_status
- request_prescription_refill(medication="Metformin")

----------------------------------------------------

User:
"Book a cardiology appointment tomorrow and show my lab results."

Functions:
- book_appointment(
    specialty="Cardiology",
    date="tomorrow"
)

- get_test_results()

----------------------------------------------------

User:
"Show my appointments, refill my insulin, and show my test results."

Functions:
- check_appointment_status()
- request_prescription_refill(medication="insulin")
- get_test_results()

----------------------------------------------------

If the user message is vague such as:

"I need help"

"I have an issue"

"Something is wrong"

"I need to see someone"

do NOT guess.

Do NOT call any function.

Only call functions when the request clearly matches one or more tools.

User message:

{user_query}
"""

    for attempt in range(max_retries + 1):

        try:

            response = _client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[_tool],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )

            if response.function_calls:

                all_intents = [
                    {
                        "intent": fc.name,
                        "parameters": dict(fc.args)
                        if fc.args else {}
                    }
                    for fc in response.function_calls
                ]

                first = all_intents[0]

                return {
                    "matched": True,
                    "intent": first["intent"],
                    "parameters": first["parameters"],
                    "all_intents": all_intents,
                    "confidence": "high",
                    "method": "llm_based",
                }

            return {
                "matched": False,
                "intent": None,
                "parameters": {},
                "confidence": "none",
                "method": "llm_based",
                "reason": "Model did not select any tool",
            }

        except Exception as e:

            error = str(e)

            if (
                "RESOURCE_EXHAUSTED" in error
                and "RequestsPerDay" not in error
                and attempt < max_retries
            ):

                match = re.search(
                    r"retryDelay['\"]?:\s*['\"]?(\d+)",
                    error,
                )

                wait_time = (
                    int(match.group(1)) + 2
                    if match
                    else 15
                )

                print(f"Rate limited. Retrying in {wait_time}s...")

                time.sleep(wait_time)

                continue

            return {
                "matched": False,
                "intent": None,
                "parameters": {},
                "confidence": "none",
                "method": "llm_based",
                "reason": error,
            }