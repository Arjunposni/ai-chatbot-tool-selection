from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.graph import graph


app = FastAPI(
    title="Healthcare AI Chatbot with Intelligent Tool Selection"
)

# ----------------------------------------------------------
# Static Files
# ----------------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

# ----------------------------------------------------------
# Templates
# ----------------------------------------------------------

templates = Jinja2Templates(
    directory="app/templates",
)


# ----------------------------------------------------------
# Request Model
# ----------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    patient_id: str = "p1"


# ----------------------------------------------------------
# Response Model
# ----------------------------------------------------------

class ChatResponse(BaseModel):
    user_message: str
    intent_detected: str | list[str] | None
    method_used: str
    tool_result: dict | None
    response: str


# ----------------------------------------------------------
# Home Page
# ----------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


# ----------------------------------------------------------
# Chat Endpoint
# ----------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Process a chat message directly through LangGraph.
    """

    state = {
        "message": request.message,
        "patient_id": request.patient_id,
    }

    result = graph.invoke(state)

    print("\n" + "=" * 80)
    print("LANGGRAPH FINAL STATE")
    print(result)
    print("=" * 80 + "\n")

    if result.get("all_intents"):
        intent_detected = [
            item["intent"]
            for item in result["all_intents"]
        ]
    else:
        intent_detected = result.get("intent")

    return ChatResponse(
        user_message=request.message,
        intent_detected=intent_detected,
        method_used=result.get(
            "method",
            "langgraph",
        ),
        tool_result=result.get(
            "tool_result",
        ),
        response=result.get(
            "response",
            "Sorry, I couldn't process your request.",
        ),
    )