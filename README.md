# 🩺 Healthcare AI Chatbot with Intelligent Tool Selection

An AI-powered healthcare chatbot built with **FastAPI**, **Python**, **Gemini/Groq LLMs**, **SQLite**, and **ChromaDB**.

The chatbot detects a user's intent, selects the correct healthcare tool, asks follow-up questions when required (slot filling), retrieves FAQ answers using Retrieval-Augmented Generation (RAG), and supports multi-turn, multi-intent conversations.

---

## 🚀 Features

✅ Hybrid Intent Detection (Rule-based + LLM)
✅ Intelligent Tool Selection
✅ Multi-turn Conversation with Slot Filling
✅ Conversation Memory
✅ Appointment Booking
✅ Appointment Status Checking
✅ Prescription Refill
✅ Lab/Test Results Retrieval
✅ FAQ Retrieval using ChromaDB (RAG)
✅ Multi-Intent Support (one message, multiple actions)
✅ Simple Web Chat Interface
✅ Multi-provider LLM support (Gemini primary, Groq fallback)

---

## 📂 Project Structure

```
ai-chatbot-tool-selection/
│
├── app/
│   ├── conversation/         → multi-turn state, slot filling, cancel handling
│   ├── intent/                → rule-based, LLM-based (Gemini/Groq), hybrid detection
│   ├── rag/                   → FAQ retrieval (ChromaDB)
│   ├── services/               → chat_service (orchestrator), tool_executor
│   ├── tools/                  → appointment, prescription, results tools + schema
│   ├── static/                 → script.js, style.css
│   ├── templates/              → index.html (chat UI)
│   ├── db.py                   → creates the local SQLite database
│   └── main.py                 → FastAPI app + /chat endpoint
│
├── chroma_db/                  → auto-generated vector index (not committed)
│
├── data/
│   ├── faq_docs.md             → source content for the FAQ/RAG layer
│   └── test_cases.json         → 25 evaluation test cases
│
├── tests/
│   └── run_test_cases.py       → runs all 25 test cases and reports results
│
├── healthcare_chatbot.db       → auto-generated local database (not committed)
├── requirements.txt
├── .env.example
├── README.md
└── REPORT.md
```

---

## 🛠 Tech Stack

**Backend:** Python, FastAPI, Uvicorn
**Database:** SQLite
**LLMs:** Google Gemini, Groq (swappable via `.env`)
**Embeddings / RAG:** sentence-transformers, ChromaDB
**Frontend:** HTML, CSS, JavaScript (no framework)

---

## ⚙ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Arjunposni/ai-chatbot-tool-selection.git
cd ai-chatbot-tool-selection
```

### 2. Requirements

- Python 3.10 or later (check with `python3 --version`)
- Git
- A **Gemini** API key ([aistudio.google.com/apikey](https://aistudio.google.com/apikey)) and/or a **Groq** API key ([console.groq.com/keys](https://console.groq.com/keys)) — both are free. You only need one, but having both lets the app fall back automatically if you hit a free-tier rate limit.
- Internet connection (for LLM API calls)

### 3. Create a virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> ⚠️ You need to run the activation command again every time you open a new terminal for this project. You'll know it's active when your prompt starts with `(venv)`.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Create your `.env` file

Create a file named `.env` in the project root (see `.env.example` for reference):

```env
LLM_PROVIDER=gemini

GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

You only need the API key for the provider you set. To switch providers later (e.g. if Gemini's daily quota runs out), just change one line:
```env
LLM_PROVIDER=groq
```
and restart the server — no code changes needed.

### 6. Initialize the database

**This step is required before running the app — it creates the tables and one sample patient.**

```bash
python3 app/db.py
```

You should see:
```
Healthcare database initialized.
```

### 7. Build the FAQ vector index

Run this once, or again whenever you edit `data/faq_docs.md`:

```bash
python3 -m app.rag.faq_retriever
```

You should see:
```
Indexed 10 FAQ entries.
```

---

## ▶ Running the application

```bash
uvicorn app.main:app --reload
```

Then open your browser to:

```
http://127.0.0.1:8000
```

To stop the server, go to the terminal and press `Ctrl+C`.

---

## 💬 Example Queries

**Appointment booking (multi-turn):**
```
User: Book an appointment
Bot:  Which specialty would you like to book an appointment for?
User: Cardiology
Bot:  What date would you prefer?
User: Tomorrow
Bot:  Appointment booked with Cardiology on 2026-08-06.
```

**Appointment status:** `Show my appointments`
**Prescription refill:** `Refill my prescription`
**Test results:** `Show my lab results`
**FAQ:** `What are your clinic hours?`
**Multi-intent (one message, two actions):** `Check my appointments and show my lab results`
**Cancelling mid-conversation:** type `cancel` at any point during a follow-up question
**Vague input handled gracefully:** `I have an issue` → bot asks for clarification instead of guessing

---

## 🧠 How the chatbot works

```
User
  │
  ▼
Hybrid Intent Detection (Rule-based → LLM fallback)
  │
  ▼
Parameter Extraction
  │
  ▼
Slot Filling (ask for anything still missing)
  │
  ▼
Conversation Memory (remembers state between messages)
  │
  ▼
Tool Execution ──► SQLite Database
  │
  ▼
Formatted Response
```

If no tool matches the request, it falls through to RAG:

```
User Question → Sentence Embedding → ChromaDB Search → Best-matching FAQ → Answer
```

---

## 🧩 Healthcare Tools

| Tool | Required parameters |
|---|---|
| `book_appointment` | `patient_id`, `specialty`, `date` |
| `check_appointment_status` | `patient_id` |
| `request_prescription_refill` | `patient_id`, `medication` |
| `get_test_results` | `patient_id` |

`patient_id` is filled in automatically — you never need to provide it yourself in the chat UI.

---

## 🗣 Multi-turn conversation & cancellation

If a required parameter is missing, the bot asks for it and remembers your answer:

```
User: Book appointment
Bot:  Which specialty?
User: Cardiology
Bot:  What date?
User: Tomorrow
Bot:  Appointment booked.
```

You can cancel an in-progress request at any point by typing `cancel` (also accepts `stop`, `never mind`, `start over`, etc.).

> Note: conversation memory is stored **in-memory only** — it resets if the server restarts. This is a deliberate prototype-scope simplification; see `REPORT.md` for the production alternative (Redis/database-backed sessions).

---

## 🔍 Retrieval-Augmented Generation (RAG)

A lightweight FAQ layer answers general health questions that don't map to a specific patient action (e.g. clinic hours, normal blood pressure ranges). FAQ content lives in `data/faq_docs.md` and is embedded/indexed with `sentence-transformers` + `ChromaDB`.

---

## 🧪 Testing & Evaluation

Run the full evaluation suite (25 test cases covering clear, ambiguous, multi-step, and sensitive-information requests):

```bash
python -m tests.run_test_cases
```

This prints, for each case, the expected vs. actual intent and which detection method handled it (rule-based, LLM, or hybrid fallback). Full accuracy results, the approach comparison (rule-based vs. LLM-based vs. hybrid), and the iteration history are documented in **`REPORT.md`**.

---

## 🐛 Troubleshooting

**`pip install` fails with "externally-managed-environment"**
The virtual environment isn't activated. Re-run the Step 3 activation command, then retry.

**Chatbot replies with "⚠️ System error... 429 RESOURCE_EXHAUSTED"**
You've hit the Gemini free-tier daily limit. Switch to Groq in `.env` (`LLM_PROVIDER=groq`) and restart the server.

**`ModuleNotFoundError` when running any command**
Make sure the virtual environment is activated (`(venv)` should show in your prompt) and that `pip install -r requirements.txt` completed without errors.

**Browser shows "Unable to connect to the Healthcare AI server"**
Check the terminal running `uvicorn` for a Python traceback — this usually means Step 6 (database init) or Step 7 (FAQ index) was skipped.

**Want a clean database to start fresh?**
```bash
rm healthcare_chatbot.db
python3 app/db.py
```

---

## 📌 Design notes

- **SQLite** was chosen over a full database server for zero-setup portability — appropriate for a prototype, not intended for production concurrency. See `REPORT.md` for the full trade-off discussion.
- **Multi-provider LLM support** (Gemini + Groq) was added specifically to work around free-tier rate limits encountered during development — details and evidence are in `REPORT.md`.
- Known limitation: multi-intent execution requires all detected intents to already have their required parameters; if any part of a multi-intent request needs a follow-up question, the system currently handles only the first intent and asks for the rest separately.

---

## 👨‍💻 Author

**Arjun Posni** — [github.com/Arjunposni](https://github.com/Arjunposni)

---

## ⭐ Acknowledgements

FastAPI · Google Gemini · Groq · ChromaDB · Sentence Transformers

---

## 📄 License

This project was created as part of a technical assessment and is intended for educational and demonstration purposes.
