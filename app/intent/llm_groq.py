import os
import json

from dotenv import load_dotenv
from groq import Groq

from app.tools.schema import TOOL_SCHEMA

load_dotenv()

_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def _build_groq_tools():
    """
    Convert TOOL_SCHEMA into Groq/OpenAI-compatible
    function definitions.
    """

    tools = []

    for tool in TOOL_SCHEMA:

        tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        parameter: {
                            "type": "string"
                        }
                        for parameter in tool["parameters"]
                    },
                    "required": list(tool["parameters"].keys())
                },
            },
        })

    return tools


_tools = _build_groq_tools()


def detect_intent_llm_groq(
    user_query: str,
    patient_id: str = "p1",
    max_retries: int = 1,
) -> dict:
    """
    Detect healthcare intent(s) using Groq Function Calling.
    """

    system_prompt = f"""
You are an intelligent healthcare assistant.

Current patient_id: {patient_id}

Available tools

1. book_appointment
2. check_appointment_status
3. request_prescription_refill
4. get_test_results

Your ONLY job is to select the correct tool(s).

RULES

• If the user asks ONE healthcare task,
call ONE function.

• If the user asks MULTIPLE independent tasks,
call ONE FUNCTION FOR EACH TASK.

Never ignore one request because another request
appears in the same message.

Examples

User:
"Check my appointments and refill my Metformin."

Call:

- check_appointment_status()

- request_prescription_refill(
    medication="Metformin"
)

------------------------------------------------

User:

"Book a cardiology appointment tomorrow
and show my lab results."

Call:

- book_appointment(
    specialty="Cardiology",
    date="tomorrow"
)

- get_test_results()

------------------------------------------------

User:

"Show my appointments,
refill my insulin,
and show my test results."

Call:

- check_appointment_status()

- request_prescription_refill(
    medication="insulin"
)

- get_test_results()

------------------------------------------------

If the request is vague such as:

"I need help"

"I have an issue"

"Something is wrong"

"I need to see someone"

do NOT guess.

Do NOT call any function.

Only call functions when the request clearly
matches one or more available tools.
"""

    for attempt in range(max_retries + 1):

        try:

            response = _client.chat.completions.create(
                model="llama-3.1-8b-instant",
                # Better if available:
                # model="llama-3.3-70b-versatile",

                temperature=0,

                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_query,
                    },
                ],

                tools=_tools,
                tool_choice="auto",
            )

            message = response.choices[0].message

            if message.tool_calls:

                all_intents = []

                for tool_call in message.tool_calls:

                    args = {}

                    if tool_call.function.arguments:
                        args = json.loads(
                            tool_call.function.arguments
                        )

                    all_intents.append(
                        {
                            "intent": tool_call.function.name,
                            "parameters": args,
                        }
                    )

                first = all_intents[0]

                return {
                    "matched": True,
                    "intent": first["intent"],
                    "parameters": first["parameters"],
                    "all_intents": all_intents,
                    "confidence": "high",
                    "method": "llm_based (groq)",
                }

            return {
                "matched": False,
                "intent": None,
                "parameters": {},
                "confidence": "none",
                "method": "llm_based (groq)",
                "reason": "Model did not select any tool",
            }

        except Exception as e:

            error = str(e)

            if (
                "tool_use_failed" in error
                and attempt < max_retries
            ):
                continue

            return {
                "matched": False,
                "intent": None,
                "parameters": {},
                "confidence": "none",
                "method": "llm_based (groq)",
                "reason": f"Error calling Groq API: {error}",
            }