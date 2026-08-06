# Technical Report
# Healthcare AI Chatbot with Intelligent Tool Selection

**Author:** Arjun Posni

**Repository:** https://github.com/Arjunposni/ai-chatbot-tool-selection

**Domain:** Healthcare

---

# 1. Problem & Approach Summary

The objective of this project was to build an intelligent healthcare chatbot capable of understanding user intent, selecting the correct healthcare tool, extracting the required parameters, and executing the requested operation.

Rather than implementing a simple request-response chatbot, I approached the assignment as the design of a complete conversational AI system. During development, the project evolved significantly—from a sequential service-based architecture into a stateful workflow orchestrated by **LangGraph**.

The final chatbot supports:

- Hybrid intent detection
- Stateful conversations
- Slot filling
- Multi-intent execution
- Retrieval-Augmented Generation (RAG)
- Multiple LLM providers
- Conversation resume and cancellation

The project emphasizes software architecture, modularity, maintainability, and practical AI engineering rather than simply satisfying the functional requirements.

---

# 2. System Architecture

## Initial Architecture

The first implementation followed a traditional sequential pipeline.

```
Frontend
    │
FastAPI
    │
chat_service.py
    │
Intent Detection
    │
Parameter Extraction
    │
Tool Execution
```

This design worked well for simple requests but became increasingly difficult to extend as new conversational capabilities were introduced.

---

## Final Architecture

The application was completely refactored to use LangGraph as the orchestration engine.

```
Frontend
    │
FastAPI
    │
graph.invoke(state)
    │
LangGraph
├── Resume Conversation
├── Continue Conversation
├── Cancel Conversation
├── Hybrid Intent Detection
├── Parameter Extraction
├── Slot Filling
├── Execute Tool(s)
└── FAQ Retrieval (RAG)
```

Each node is responsible for a single task while LangGraph manages routing, execution order, and conversation state.

This modular architecture significantly improves maintainability and allows new capabilities to be added without rewriting the entire workflow.

---

# 3. Why LangGraph?

Initially, the chatbot followed a linear execution model where every request passed through the same sequence of operations.

As features such as conversation memory, slot filling, resume conversations, and multi-intent execution were introduced, the sequential architecture became difficult to maintain. New features required modifying the central orchestration logic, resulting in tightly coupled code.

LangGraph solved these problems by introducing graph-based workflow orchestration.

Instead of one large execution pipeline, every responsibility became an independent node. This made the application:

- Modular
- Easier to debug
- Easier to extend
- Better suited for conversational AI workflows
- More maintainable

FastAPI now simply invokes:

```python
graph.invoke(state)
```

while LangGraph controls the complete conversation lifecycle.

---

# 4. LangGraph Workflow

The workflow consists of specialized nodes.

| Node | Responsibility |
|------|----------------|
| Resume Conversation | Restore unfinished conversations |
| Continue Conversation | Continue slot filling |
| Cancel Conversation | Clear active sessions |
| Hybrid Intent Detection | Rule-based detection with LLM fallback |
| Parameter Extraction | Extract specialty, date and patient details |
| Slot Filling | Request missing parameters |
| Execute Tool | Execute healthcare tools |
| FAQ Retrieval | Retrieve healthcare FAQs using semantic search |

Each node performs one clearly defined responsibility, resulting in a clean separation of concerns.

---

# 5. Engineering Challenges & Solutions

## Challenge 1 – Sequential Architecture

### Problem

The original service-based architecture became increasingly complex as new conversational features were introduced.

### Solution

Migrated the entire orchestration layer to LangGraph.

### Result

- Cleaner workflow
- Better modularity
- Easier maintenance
- Simplified future development

---

## Challenge 2 – Incomplete User Requests

### Example

```
Book appointment
```

The chatbot could not execute the tool because important parameters such as specialty and appointment date were missing.

### Solution

Implemented slot filling that asks users only for the missing information before executing the tool.

---

## Challenge 3 – Conversation Memory

Healthcare conversations often span multiple user messages.

Example:

```
User:
Book appointment

Bot:
Which specialty?

User:
Cardiology

Bot:
Which date?

User:
Tomorrow
```

### Solution

Implemented conversation state management that stores pending conversations and automatically resumes them.

---

## Challenge 4 – Multi-Intent Requests

Example:

```
Check my appointments and show my test results.
```

Initially only one tool was executed.

### Solution

Enhanced intent detection and LangGraph execution so multiple healthcare tools can be executed within a single request.

---

## Challenge 5 – General Healthcare Questions

Not every user request corresponds to a healthcare tool.

Examples include:

- How long should I fast before a blood test?
- What is hypertension?

### Solution

Integrated ChromaDB with Sentence Transformers to perform semantic retrieval over healthcare FAQ documents.

---

## Challenge 6 – LLM Flexibility

Different LLM providers have different response quality, pricing, and availability.

### Solution

Designed the chatbot to support multiple providers including:

- Google Gemini
- Groq
- Nebius

This makes the system more flexible and provider-independent.

---

# 6. Design Decisions

| Decision | Reason |
|-----------|--------|
| LangGraph | Workflow orchestration |
| Hybrid Intent Detection | Balance speed and accuracy |
| SQLite | Lightweight local database |
| ChromaDB | Semantic FAQ retrieval |
| Sentence Transformers | Efficient embeddings |
| Multiple LLM Providers | Flexibility and reliability |
| Modular Architecture | Easier maintenance |

These design decisions improved both the performance and maintainability of the chatbot.

---

# 7. Key Features

The completed chatbot supports:

- Appointment booking
- Appointment status checking
- Prescription refill requests
- Test result retrieval
- Conversation memory
- Slot filling
- Multi-intent execution
- Session management
- Conversation cancellation
- Hybrid intent detection
- Semantic FAQ retrieval using RAG
- Multiple LLM providers

---

# 8. Project Evolution

| Initial Version | Final Version |
|-----------------|---------------|
| Sequential pipeline | LangGraph workflow |
| chat_service.py | Graph orchestration |
| Stateless requests | Stateful conversations |
| Single intent | Multi-intent execution |
| No slot filling | Automatic slot filling |
| No resume support | Conversation resume |
| No RAG | Semantic FAQ retrieval |
| Simple chatbot | Conversational AI system |

This evolution transformed the project from a simple chatbot into a modular conversational AI platform.

---

# 9. Results

The final implementation successfully demonstrates:

- Intelligent healthcare intent detection
- Structured parameter extraction
- Stateful conversation management
- Multi-turn dialogue support
- Multi-intent execution
- Semantic FAQ retrieval
- Modular workflow orchestration
- Extensible software architecture

The migration to LangGraph significantly improved code organization while making future enhancements considerably easier.

---

# 10. Conclusion

This project evolved well beyond the original assignment requirements.

What began as a sequential intent-based chatbot was transformed into a modular, stateful conversational AI system orchestrated by LangGraph. Through iterative refactoring, conversation memory, slot filling, multi-intent execution, and semantic FAQ retrieval were successfully integrated while maintaining a clean and extensible architecture.

The final solution demonstrates not only the ability to build an AI-powered healthcare chatbot but also an understanding of software architecture, workflow orchestration, and engineering best practices for modern conversational AI systems.
