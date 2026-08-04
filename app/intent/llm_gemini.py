import time
import re

def detect_intent_llm_based(user_query: str, patient_id: str = "p1", max_retries: int = 2) -> dict:
    prompt = (
        f"You are a healthcare assistant. The current patient_id is '{patient_id}'. "
        f"Based on the user's message, call the correct tool with the right parameters. "
        f"If the request is unclear or doesn't match any tool, do not call any function.\n\n"
        f"User message: {user_query}"
    )

    for attempt in range(max_retries + 1):
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
            error_str = str(e)
            if "RESOURCE_EXHAUSTED" in error_str and "RequestsPerDay" not in error_str and attempt < max_retries:
                # Extract suggested retry delay, default to 15s if not found
                match = re.search(r"retryDelay['\"]?:\s*['\"]?(\d+)", error_str)
                wait_time = int(match.group(1)) + 2 if match else 15
                print(f"    Rate limited, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            return {
                "matched": False,
                "intent": None,
                "confidence": "none",
                "method": "llm_based",
                "reason": f"Error calling Gemini API: {error_str}"
            }