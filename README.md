# 🏥 Healthcare AI Chatbot with Intelligent Tool Selection

> **An intelligent healthcare chatbot built using LangGraph, FastAPI, SQLite, ChromaDB, and multiple LLM providers to understand user intent, manage conversations, execute healthcare tools, and answer healthcare FAQs using Retrieval-Augmented Generation (RAG).**

---

## 📌 Overview

Healthcare conversations are rarely a single question followed by a single answer. Users may provide incomplete information, ask multiple questions in one message, change their minds midway, or continue an earlier conversation.

This project addresses these challenges with a **stateful AI healthcare assistant** powered by **LangGraph**, which orchestrates the conversation instead of following a rigid sequential pipeline.

The chatbot intelligently:

* Understands user intent
* Extracts required parameters
* Handles missing information through slot filling
* Maintains conversation state
* Supports multiple intents in one request
* Executes healthcare tools
* Retrieves FAQ answers using semantic search (RAG)

Full architecture details, the intent-detection approach comparison, and evaluation results are documented in **`REPORT.md`**.

---

# ✨ Features

## Healthcare Tools

* ✅ Book Appointment
* ✅ Check Appointment Status
* ✅ Request Prescription Refill
* ✅ View Test Results
* ✅ Healthcare FAQ Retrieval

## Conversation Intelligence

* ✅ Stateful conversations
* ✅ Conversation resume
* ✅ Slot filling
* ✅ Conversation cancellation
* ✅ Session management
* ✅ Follow-up question handling

Example:

```text
User:
Book an appointment

Bot:
Which specialty would you like?

User:
Cardiology

Bot:
Which date?

User:
Tomorrow

Bot:
Your cardiology appointment has been booked for tomorrow.
```

## Intelligent Intent Detection

Hybrid architecture:

```
User Query
      │
      ▼
Regex Rule Detection
      │
Intent Found (and message isn't a compound "X and Y" request)?
   │         │
 Yes        No
   │         ▼
   │     LLM Detection (also handles multi-intent messages)
   │
   ▼
Parameter Extraction + Validation (rejects placeholders, past dates)
      │
      ▼
Slot Filling
      │
      ▼
Tool Execution
```

Supports multiple LLM providers, switchable via `.env` with no code changes:

* Google Gemini
* Groq
* Nebius *(integrated; may require account verification on Nebius's side before use — see Troubleshooting)*

## Multi-Intent Support

The chatbot supports **multiple intents within a single user request**.

Example:

```text
Check my appointments and show my test results.
```

The workflow detects both intents, executes both tools, and combines the responses into a single reply.

## Retrieval-Augmented Generation (RAG)

Healthcare FAQs are stored inside **ChromaDB**. Instead of relying only on an LLM, the chatbot retrieves semantically relevant information using sentence embeddings.

Embedding model: `all-MiniLM-L6-v2`

```
User Question → Sentence Transformer → Vector Embedding
             → ChromaDB Similarity Search → Relevant FAQ → Response
```

---

# 🏗 Architecture

```
                    Frontend
                        │
                        ▼
                    FastAPI API
                        │
                        ▼
               graph.invoke(state)
                        │
                        ▼
               ┌───────────────────┐
               │    LangGraph      │
               └───────────────────┘
                        │
     ┌──────────────────────────────────────┐
     │ Resume Conversation                  │
     │ Continue Conversation (incl. cancel) │
     │ Hybrid Intent Detection              │
     │ Parameter Extraction                 │
     │ Slot Filling                         │
     │ Execute Tool(s)                      │
     │ FAQ Retrieval (RAG)                  │
     └──────────────────────────────────────┘
                        │
                        ▼
                 Final Response
```

FastAPI's `/chat` endpoint is a thin wrapper — it just calls `graph.invoke(state)`; LangGraph owns the entire conversation lifecycle.

## LangGraph Nodes

| Node                    | Purpose                                       |
| ----------------------- | --------------------------------------------- |
| Resume Conversation     | Restores unfinished conversations             |
| Continue Conversation   | Continues slot filling; handles cancellation and rejects invalid (past) dates for an active session |
| Hybrid Intent Detection | Regex first; LLM fallback for ambiguity, parameter extraction, and multi-intent messages |
| Parameter Extraction    | Extracts specialty, dates, medication; validates and rejects placeholder or past-date values |
| Slot Filling            | Requests missing required parameters, one at a time |
| Execute Tool            | Executes one or more healthcare functions     |
| FAQ Retrieval           | Performs semantic search over healthcare FAQs; returns a clarification if nothing relevant is found |

---

# ⚙ Technology Stack

| Layer                | Technology                  |
| -------------------- | --------------------------- |
| Backend              | FastAPI                     |
| Workflow Engine      | LangGraph                   |
| Programming Language | Python 3.10+                |
| Database             | SQLite                      |
| Vector Database      | ChromaDB                    |
| Embedding Model      | Sentence Transformers (`all-MiniLM-L6-v2`) |
| LLM Providers        | Google Gemini, Groq, Nebius |
| Frontend             | HTML, CSS, JavaScript       |

---

# 📁 Project Structure

```text
app/
│
├── graph/
│   ├── workflow.py       → builds the LangGraph state graph
│   ├── nodes.py           → each workflow step
│   └── state.py           → shared ChatState schema
│
├── conversation/           → session state, slot filling, date validation
├── intent/                 → rule-based, LLM-based (Gemini/Groq/Nebius), hybrid
├── rag/                     → FAQ retrieval (ChromaDB)
├── services/
│   └── tool_executor.py    → single interface to run any tool
├── tools/                   → the 4 healthcare tools + schema
├── static/ + templates/     → chat UI
├── db.py                    → creates the local SQLite database
└── main.py                  → FastAPI app, /chat endpoint

data/
├── faq_docs.md               → source content for RAG
└── test_cases.json           → evaluation test set

tests/
└── run_test_cases.py         → runs the evaluation set
```

---

# 🚀 Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/Arjunposni/ai-chatbot-tool-selection.git
cd ai-chatbot-tool-selection
```

## 2. Requirements

- Python 3.10 or later (check with `python3 --version`)
- Git
- At least one LLM API key — Gemini ([aistudio.google.com/apikey](https://aistudio.google.com/apikey)) and/or Groq ([console.groq.com/keys](https://console.groq.com/keys)), both free. Nebius is optional (see note above).

## 3. Create a virtual environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

> ⚠️ Reactivate this every time you open a new terminal for this project — you'll know it's active when your prompt starts with `(venv)`.

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Configure environment variables

Create a `.env` file in the project root:

```env
LLM_PROVIDER=gemini

GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
NEBIUS_API_KEY=your_nebius_api_key
```

You only need the key for the provider you set as `LLM_PROVIDER`. Switch providers any time (e.g. if you hit a free-tier rate limit) by changing that one line and restarting the server — no code changes needed.

## 6. Initialize the database

**Required before first run** — creates the tables and one sample patient (`p1`):

```bash
python3 app/db.py
```
Expected output: `Healthcare database initialized.`

## 7. Build the FAQ vector index

Run once, and again whenever you edit `data/faq_docs.md`:

```bash
python3 -m app.rag.faq_retriever
```
Expected output: `Indexed N FAQ entries.`

## 8. Run the application

```bash
uvicorn app.main:app --reload
```

Open the chat UI: `http://127.0.0.1:8000`
Interactive API docs: `http://127.0.0.1:8000/docs`

To stop the server: `Ctrl+C`.

---

# 📡 Example API Usage

`POST /chat` accepts:
```json
{
    "message": "Book a cardiology appointment tomorrow",
    "patient_id": "p1"
}
```
(`patient_id` defaults to `"p1"` if omitted.)

The response always follows this shape:
```json
{
    "user_message": "Book a cardiology appointment tomorrow",
    "intent_detected": "book_appointment",
    "method_used": "hybrid (llm)",
    "tool_result": {
        "success": true,
        "appointment_id": 3,
        "message": "Appointment booked with Cardiology on 2026-08-08."
    },
    "response": "Appointment booked with Cardiology on 2026-08-08."
}
```

**Slot filling example** — `{"message": "Book appointment"}` →
```json
{
    "user_message": "Book appointment",
    "intent_detected": "book_appointment",
    "method_used": "conversation",
    "tool_result": null,
    "response": "Which specialty would you like to book an appointment for?"
}
```

**Multi-intent example** — `{"message": "Check my appointments and show my test results"}` → `intent_detected` becomes a list (`["check_appointment_status", "get_test_results"]`), and `tool_result` contains a `multi_results` array with one entry per executed tool.

**FAQ example** — `{"message": "How long should I fast before a blood test?"}` → `method_used: "rag"`, and `response` contains the matched FAQ answer.

---

# 💬 Try it in the chat UI

| Try typing... | What happens |
|---|---|
| `Show me my upcoming appointments` | Instant response via the rule-based fast path |
| `Book an appointment` | Bot asks for specialty, then date, then books it |
| `when's my next visit?` | Paraphrase correctly understood via LLM fallback |
| `What are your clinic hours?` | Answered from the FAQ knowledge base (RAG) |
| `I have an issue` | Bot asks for clarification instead of guessing |
| `Check my appointments and refill my Metformin` | Both actions handled in one reply |
| `cancel` (mid-conversation) | Cancels whatever is currently pending |

---

# 🧪 Testing & Evaluation

Run the full evaluation suite (covering clear, ambiguous, multi-intent, complex-negative, and natural-language/paraphrased test cases):

```bash
python -m tests.run_test_cases
```

This prints, per case, the expected vs. actual result and which method handled it. Full accuracy results and the iteration history behind them are in **`REPORT.md`**.

---

# 🐛 Troubleshooting

**`pip install` fails with "externally-managed-environment"**
The virtual environment isn't activated — re-run the Step 3 activation command, then retry.

**Chatbot replies with a rate-limit / system error message**
You've likely hit the Gemini free-tier limit (5 requests/min, ~20/day on the free tier). Switch providers in `.env` (`LLM_PROVIDER=groq`) and restart the server.

**Nebius returns a 401 Unauthorized error**
Nebius may require manual account verification before API keys work — this is a known, occasionally slow process on their end, unrelated to this codebase. Use Gemini or Groq in the meantime.

**`ModuleNotFoundError` on any command**
Confirm the virtual environment is active (`(venv)` in your prompt) and that Step 4 completed without errors.

**Browser shows "Unable to connect to the Healthcare AI server"**
Check the terminal running `uvicorn` for a traceback — this almost always means Step 6 or Step 7 was skipped.

**Want a clean database to start fresh?**
```bash
rm healthcare_chatbot.db
python3 app/db.py
```

---

# 🔄 Project Evolution

The chatbot underwent a significant architectural redesign during development:

**Initial implementation:** sequential pipeline, service-based orchestration (`chat_service.py`), limited conversation handling.

**Final implementation:** migrated to LangGraph, added conversation memory, slot filling, resume/cancel support, multi-intent execution, RAG, and multiple swappable LLM providers.

Beyond architecture, the intent-detection logic itself went through several rounds of measured evaluation, bug-fixing, and re-testing — including a real precision/recall trade-off that was discovered and resolved. See `REPORT.md` for the full run-by-run evaluation history.

---

# 🤝 Acknowledgements

Developed as a take-home assignment demonstrating conversational AI architecture using **LangGraph**, **FastAPI**, multiple **LLM providers**, and **Retrieval-Augmented Generation (RAG)** — with an emphasis on clean software architecture, modularity, and evidence-based iteration over a purely rule-based chatbot.

---

## 🎥 Demo Video
[Watch on Loom](https://www.loom.com/share/ff718195565543e3852742879332577b) · [Backup on Google Drive](https://drive.google.com/file/d/1E23SdU2cHM91QpW58ScgyeovREwVxbJO/view?usp=drive_link)

---

# 📄 License

This project is intended for educational and evaluation purposes as part of a software engineering take-home assignment.
