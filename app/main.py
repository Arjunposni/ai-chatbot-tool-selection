from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.services.chat_service import process_chat

app = FastAPI(
    title="Healthcare AI Chatbot with Intelligent Tool Selection"
)

# Serve CSS and JavaScript
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# HTML templates
templates = Jinja2Templates(directory="app/templates")


class ChatRequest(BaseModel):
    """Incoming request from the frontend."""

    message: str
    patient_id: str = "p1"


class ChatResponse(BaseModel):
    """Response returned to the frontend."""

    user_message: str
    intent_detected: str | list[str] | None
    method_used: str
    tool_result: dict | None
    response: str


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Serve the chatbot UI."""

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Delegate the chatbot workflow to chat_service.
    """

    result = process_chat(
        message=request.message,
        patient_id=request.patient_id,
    )

    return ChatResponse(
        user_message=request.message,
        intent_detected=result.get("intent_detected"),
        method_used=result.get("method_used"),
        tool_result=result.get("tool_result"),
        response=result.get("response"),
    )