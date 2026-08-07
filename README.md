# 🏥 Healthcare AI Chatbot with Intelligent Tool Selection

> **An intelligent healthcare chatbot built using LangGraph, FastAPI, SQLite, ChromaDB, and multiple LLM providers to understand user intent, manage conversations, execute healthcare tools, and answer healthcare FAQs using Retrieval-Augmented Generation (RAG).**

---

## 📌 Overview

Healthcare conversations are rarely a single question followed by a single answer. Users may provide incomplete information, ask multiple questions in one message, change their minds midway, or continue an earlier conversation.

This project addresses these challenges by implementing a **stateful AI healthcare assistant** powered by **LangGraph**, enabling the chatbot to orchestrate conversations instead of following a rigid sequential pipeline.

The chatbot intelligently:

* Understands user intent
* Extracts required parameters
* Handles missing information through slot filling
* Maintains conversation state
* Supports multiple intents in one request
* Executes healthcare tools
* Retrieves FAQ answers using semantic search (RAG)

---

# ✨ Features

## Healthcare Tools

* ✅ Book Appointment
* ✅ Check Appointment Status
* ✅ Request Prescription Refill
* ✅ View Test Results
* ✅ Healthcare FAQ Retrieval

---

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

---

## Intelligent Intent Detection

Hybrid architecture:

```
User Query
      │
      ▼
Regex Rule Detection
      │
Intent Found?
   │         │
 Yes        No
   │         ▼
   │     LLM Detection
   │
   ▼
Parameter Extraction
      │
      ▼
Slot Filling
      │
      ▼
Tool Execution
```

Supports multiple LLM providers:

* Google Gemini
* Groq
* Nebius

---

## Multi-Intent Support

Unlike traditional chatbots, this project supports **multiple intents within a single user request**.

Example:

```text
Check my appointments and show my test results.
```

The workflow detects both intents, executes both tools, and combines the responses into a single reply.

---

## Retrieval-Augmented Generation (RAG)

Healthcare FAQs are stored inside **ChromaDB**.

Instead of relying only on an LLM, the chatbot retrieves semantically relevant information using sentence embeddings.

Embedding model:

```
all-MiniLM-L6-v2
```

Pipeline:

```
User Question
      │
      ▼
Sentence Transformer
      │
      ▼
Vector Embedding
      │
      ▼
ChromaDB Similarity Search
      │
      ▼
Relevant FAQ
      │
      ▼
Response
```

---

# 🏗 Architecture Evolution

## Initial Architecture

The project originally followed a sequential pipeline.

```
Frontend
    │
    ▼
FastAPI
    │
    ▼
chat_service.py
    │
    ▼
Intent Detection
    │
    ▼
Parameter Extraction
    │
    ▼
Tool Execution
```

### Limitations

* No conversation memory
* Difficult to extend
* No resume capability
* No slot filling
* No multi-intent handling
* Increasing complexity as new features were added

---

## Current Architecture

The application was completely refactored using **LangGraph**.

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
     │ Continue Conversation                │
     │ Cancel Conversation                  │
     │ Hybrid Intent Detection              │
     │ Parameter Extraction                 │
     │ Slot Filling                         │
     │ Execute Tool                         │
     │ FAQ Retrieval (RAG)                  │
     └──────────────────────────────────────┘
                        │
                        ▼
                 Final Response
```

LangGraph now acts as the orchestration engine for the entire chatbot.

FastAPI no longer communicates with a sequential service.

Instead it invokes:

```python
graph.invoke(state)
```

---

# 🔄 LangGraph Workflow

The chatbot executes the following workflow:

```
Start
  │
  ▼
Resume Previous Conversation
  │
  ▼
Continue Pending Conversation?
  │
 ┌─────────────┐
 │ Yes         │
 ▼             │
Continue       │
 │             │
 ▼             │
No Pending ----┘
 │
 ▼
Cancel Request?
 │
 ▼
Hybrid Intent Detection
 │
 ▼
Parameter Extraction
 │
 ▼
Missing Parameters?
 │
 ├────────► Slot Filling
 │              │
 │              ▼
 │        Save Conversation
 │              │
 │              ▼
 │        Wait for User
 │
 ▼
Execute Tool(s)
 │
 ▼
Need FAQ?
 │
 ▼
RAG Retrieval
 │
 ▼
Return Response
```

---

# 🧠 LangGraph Nodes

| Node                    | Purpose                                       |
| ----------------------- | --------------------------------------------- |
| Resume Conversation     | Restores unfinished conversations             |
| Continue Conversation   | Continues slot filling using stored session   |
| Cancel Conversation     | Clears conversation state when user cancels   |
| Hybrid Intent Detection | Uses regex first, LLM fallback if needed      |
| Parameter Extraction    | Extracts specialty, patient details, dates    |
| Slot Filling            | Requests missing required parameters          |
| Execute Tool            | Executes healthcare functions                 |
| FAQ Retrieval           | Performs semantic search over healthcare FAQs |

---

# ⚙ Technology Stack

| Layer                | Technology                  |
| -------------------- | --------------------------- |
| Backend              | FastAPI                     |
| Workflow Engine      | LangGraph                   |
| Programming Language | Python                      |
| Database             | SQLite                      |
| Vector Database      | ChromaDB                    |
| Embedding Model      | Sentence Transformers       |
| Embedding Model Used | all-MiniLM-L6-v2            |
| LLM Providers        | Google Gemini, Groq, Nebius |
| Frontend             | HTML, CSS, JavaScript       |

---

# 📁 Project Structure

```text
app/
│
├── graph/
│   ├── workflow.py
│   ├── nodes.py
│   └── state.py
│
├── conversation/
│
├── intent/
│
├── rag/
│
├── services/
│   └── tool_executor.py
│
├── tools/
│
├── db.py
│
└── main.py
```

---

# 🚀 Getting Started

## Clone Repository

```bash
git clone https://github.com/<your-username>/ai-chatbot-tool-selection.git

cd ai-chatbot-tool-selection
```

---

## Create Virtual Environment

Linux/macOS

```bash
python -m venv venv

source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
GEMINI_API_KEY=your_gemini_api_key

GROQ_API_KEY=your_groq_api_key

NEBIUS_API_KEY=your_nebius_api_key
```

---

## Run FastAPI

```bash
uvicorn app.main:app --reload
```

Open:

```
http://127.0.0.1:8000
```

Interactive API documentation:

```
http://127.0.0.1:8000/docs
```

---

# 📡 Example API Request

```http
POST /chat
```

Request

```json
{
    "message": "Book a cardiology appointment tomorrow"
}
```

Response

```json
{
    "response": "Your cardiology appointment has been booked for tomorrow."
}
```

---

## Example — Slot Filling

Request

```json
{
    "message": "Book appointment"
}
```

Response

```json
{
    "response": "Which specialty would you like?"
}
```

---

## Example — Multi-Intent

Request

```json
{
    "message": "Check my appointments and show my test results"
}
```

Response

```json
{
    "appointment_status": "...",
    "test_results": "..."
}
```

---

## Example — FAQ Retrieval

Request

```json
{
    "message": "How long should I fast before a blood test?"
}
```

Response

```json
{
    "response": "Most blood tests require fasting for 8–12 hours. Please follow your healthcare provider's instructions."
}
```

---

# 🔄 Project Evolution

During development, the chatbot underwent a significant architectural redesign.

### Initial Implementation

* Sequential pipeline
* Service-based architecture
* Limited conversation handling

### Improvements

* Migrated to LangGraph
* Removed `chat_service.py`
* Direct graph execution through FastAPI
* Added conversation memory
* Added slot filling
* Added resume functionality
* Added cancel workflow
* Added multi-intent execution
* Added Retrieval-Augmented Generation
* Added support for multiple LLM providers
* Improved parameter extraction
* Improved modularity and maintainability

These changes transformed the project from a linear chatbot into a modular, stateful conversational AI system.

---

# 🤝 Acknowledgements

This project was developed as a take-home assignment to demonstrate modern conversational AI architecture using **LangGraph**, **FastAPI**, **LLMs**, and **Retrieval-Augmented Generation (RAG)**.

The implementation focuses on clean software architecture, modular design, extensibility, and practical conversational intelligence rather than a simple rule-based chatbot.

---

# 📄 License

This project is intended for educational and evaluation purposes as part of a software engineering take-home assignment.
