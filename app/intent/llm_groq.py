import os
import json
from dotenv import load_dotenv
from groq import Groq
from app.tools.schema import TOOL_SCHEMA

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _build_groq_tools():
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
                        param: {"type": "string"} for param in tool["parameters"]
                    },
                    "required": list(tool["parameters"].keys())
                }
            }
        })
    return tools


_tools = _build_groq_tools()


def detect_intent_llm_groq(user_query: str, patient_id: str = "p1", max_retries: int = 1) -> dict:
    """
    Uses Groq's OpenAI-compatible function calling to detect intent + extract parameters.
    Retries once on malformed tool-call output (a known occasional issue with
    Llama models on Groq), since a repeat attempt often succeeds cleanly.
    """
    system_prompt = (
        f"You are a healthcare assistant. The current patient_id is '{patient_id}'. "
        f"Based on the user's message, call the correct tool with the right parameters. "
        f"If the request is unclear or doesn't match any tool, do not call any function."
    )

    for attempt in range(max_retries + 1):
        try:
            response = _client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                tools=_tools,
                tool_choice="auto"
            )

            message = response.choices[0].message

            if message.tool_calls:
                tool_call = message.tool_calls[0]
                params = json.loads(tool_call.function.arguments)
                return {
                    "matched": True,
                    "intent": tool_call.function.name,
                    "parameters": params,
                    "confidence": "high",
                    "method": "llm_based (groq)"
                }

            return {
                "matched": False,
                "intent": None,
                "confidence": "none",
                "method": "llm_based (groq)",
                "reason": "Model did not select any tool"
            }

        except Exception as e:
            error_str = str(e)
            if "tool_use_failed" in error_str and attempt < max_retries:
                continue  # malformed output from model, retry once
            return {
                "matched": False,
                "intent": None,
                "confidence": "none",
                "method": "llm_based (groq)",
                "reason": f"Error calling Groq API: {error_str}"
            }