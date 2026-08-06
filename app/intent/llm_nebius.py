import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from app.tools.schema import TOOL_SCHEMA

load_dotenv()

# ---------------------------------------------------------
# Nebius OpenAI-compatible client
# ---------------------------------------------------------

_client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)

# Example models:
# meta-llama/Meta-Llama-3.1-70B-Instruct
# Qwen/Qwen2.5-72B-Instruct
# google/gemma-3-27b-it
_MODEL_NAME = os.getenv(
    "NEBIUS_MODEL",
    "Qwen/Qwen3.5-397B-A17B",
)


# ---------------------------------------------------------
# Tool Definitions
# ---------------------------------------------------------

def _build_nebius_tools():

    tools = []

    for tool in TOOL_SCHEMA:

        tools.append(
            {
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
                        "required": list(tool["parameters"].keys()),
                    },
                },
            }
        )

    return tools


_tools = _build_nebius_tools()


# ---------------------------------------------------------
# Intent Detection
# ---------------------------------------------------------

def detect_intent_llm_nebius(
    user_query: str,
    patient_id: str = "p1",
    max_retries: int = 1,
) -> dict:
    """
    Uses Nebius OpenAI-compatible Function Calling
    for intent detection and parameter extraction.
    """

    system_prompt = f"""
You are an intelligent healthcare assistant.

Current patient_id: {patient_id}

Available tools

1. book_appointment
2. check_appointment_status
3. request_prescription_refill
4. get_test_results

Your ONLY job is to choose the correct tool(s).

RULES

• If the user requests ONE task,
call ONE function.

• If the user requests MULTIPLE tasks,
call ONE FUNCTION FOR EACH TASK.

• Never ignore one request because another request
appears in the same sentence.

Examples

User:
Check my appointments and refill my Metformin.

Functions:
- check_appointment_status()
- request_prescription_refill(medication="Metformin")

-----------------------------------------

User:
Book a cardiology appointment tomorrow and
show my test results.

Functions:
- book_appointment(
    specialty="Cardiology",
    date="tomorrow"
)

- get_test_results()

-----------------------------------------

If the request is vague such as

"I need help"

"I have an issue"

"What medicine was I prescribed?"

"I forgot my medication"

do NOT call any function.

Only call functions when the request clearly
matches one or more available tools.
"""

    for attempt in range(max_retries + 1):

        try:

            response = _client.chat.completions.create(

                model=_MODEL_NAME,

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
            print("\n" + "=" * 70)

            print("USER QUERY:")
            print(user_query)

            print("\nMESSAGE CONTENT:")
            print(message.content)

            print("\nTOOL CALLS:")
            print(message.tool_calls)

            print("=" * 70 + "\n")

            if message.tool_calls:

                all_intents = []

                for tool_call in message.tool_calls:

                    arguments = {}

                    if tool_call.function.arguments:

                        arguments = json.loads(
                            tool_call.function.arguments
                        )

                    all_intents.append(
                        {
                            "intent": tool_call.function.name,
                            "parameters": arguments,
                        }
                    )

                first = all_intents[0]

                return {
                    "matched": True,
                    "intent": first["intent"],
                    "parameters": first["parameters"],
                    "all_intents": all_intents,
                    "confidence": "high",
                    "method": "llm_based (nebius)",
                }

            return {
                "matched": False,
                "intent": None,
                "parameters": {},
                "confidence": "none",
                "method": "llm_based (nebius)",
                "reason": "Model did not select any tool",
            }

        except Exception as e:

            error = str(e)

            if (
                "tool" in error.lower()
                and attempt < max_retries
            ):
                continue

            return {
                "matched": False,
                "intent": None,
                "parameters": {},
                "confidence": "none",
                "method": "llm_based (nebius)",
                "reason": f"Error calling Nebius API: {error}",
            }