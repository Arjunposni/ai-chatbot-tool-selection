import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from app.tools.schema import TOOL_SCHEMA

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _build_tool():
    function_declarations = []
    for tool in TOOL_SCHEMA:
        function_declarations.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters_json_schema={
                    "type": "object",
                    "properties": {
                        param: {"type": "string"} for param in tool["parameters"]
                    },
                    "required": list(tool["parameters"].keys())
                }
            )
        )
    return types.Tool(function_declarations=function_declarations)


_tool = _build_tool()


def detect_intent_llm_based(user_query: str, patient_id: str = "p1") -> dict:
    prompt = (
        f"You are a healthcare assistant. The current patient_id is '{patient_id}'. "
        f"Based on the user's message, call the correct tool with the right parameters. "
        f"If the request is unclear or doesn't match any tool, do not call any function.\n\n"
        f"User message: {user_query}"
    )

    try:
        response = _client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[_tool],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            )
        )

        if response.function_calls:
            fn_call = response.function_calls[0]
            params = dict(fn_call.args) if fn_call.args else {}
            return {
                "matched": True,
                "intent": fn_call.name,
                "parameters": params,
                "confidence": "high",
                "method": "llm_based"
            }

        return {
            "matched": False,
            "intent": None,
            "confidence": "none",
            "method": "llm_based",
            "reason": "Model did not select any tool"
        }

    except Exception as e:
        return {
            "matched": False,
            "intent": None,
            "confidence": "none",
            "method": "llm_based",
            "reason": f"Error calling Gemini API: {str(e)}"
        }
