from fastapi import FastAPI
from pydantic import BaseModel

from app.intent.hybrid import detect_intent_hybrid
from app.tools.appointment_tool import book_appointment, check_appointment_status
from app.tools.prescription_tool import request_prescription_refill
from app.tools.results_tool import get_test_results
from app.rag.faq_retriever import search_faq

app = FastAPI(title="Healthcare AI Chatbot with Intelligent Tool Selection")


# Maps intent name -> actual Python function
TOOL_EXECUTORS = {
    "book_appointment": book_appointment,
    "check_appointment_status": check_appointment_status,
    "request_prescription_refill": request_prescription_refill,
    "get_test_results": get_test_results,
}


class ChatRequest(BaseModel):
    message: str
    patient_id: str = "p1"


class ChatResponse(BaseModel):
    user_message: str
    intent_detected: str | None
    method_used: str
    tool_result: dict | None
    response: str


@app.get("/")
def root():
    return {"status": "Healthcare chatbot API is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    intent_result = detect_intent_hybrid(request.message, patient_id=request.patient_id)

    if not intent_result.get("matched"):
        # No tool matched — try RAG for general knowledge/FAQ questions
        faq_result = search_faq(request.message)

        if faq_result["matched"]:
            return ChatResponse(
                user_message=request.message,
                intent_detected="faq_lookup",
                method_used="rag",
                tool_result=faq_result,
                response=faq_result["answer"]
            )

        return ChatResponse(
            user_message=request.message,
            intent_detected=None,
            method_used=intent_result.get("method", "unknown"),
            tool_result=None,
            response=(
                "I'm not sure what you need help with. Could you clarify — "
                "are you looking to book an appointment, check an appointment, "
                "refill a prescription, view test results, or ask a general "
                "health question?"
            )
        )

    intent_name = intent_result["intent"]
    params = intent_result.get("parameters", {})

    # Always ensure patient_id is present, fallback to request's patient_id
    params.setdefault("patient_id", request.patient_id)

    executor = TOOL_EXECUTORS.get(intent_name)

    if not executor:
        return ChatResponse(
            user_message=request.message,
            intent_detected=intent_name,
            method_used=intent_result.get("method", "unknown"),
            tool_result=None,
            response=f"Detected intent '{intent_name}' but no matching tool executor found."
        )

    try:
        tool_result = executor(**params)
    except TypeError as e:
        return ChatResponse(
            user_message=request.message,
            intent_detected=intent_name,
            method_used=intent_result.get("method", "unknown"),
            tool_result=None,
            response=f"Tool call failed due to missing/invalid parameters: {str(e)}"
        )

    return ChatResponse(
        user_message=request.message,
        intent_detected=intent_name,
        method_used=intent_result.get("method", "unknown"),
        tool_result=tool_result,
        response=tool_result.get("message", "Action completed.")
    )