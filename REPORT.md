# Technical Report

## Healthcare AI Chatbot with Intelligent Tool Selection

**Author:** Arjun Posni

---

# 1. Introduction

The objective of this project was to build an intelligent healthcare chatbot capable of understanding user requests, identifying the correct healthcare service, extracting required information, and executing the appropriate tool.

Rather than implementing a simple rule-based chatbot, the project evolved into a **stateful conversational AI system** that supports multi-turn conversations, conversation memory, multi-intent execution, and Retrieval-Augmented Generation (RAG) for healthcare FAQs.

The final implementation focuses on clean architecture, modularity, and extensibility while demonstrating practical software engineering principles.

---

# 2. Problem Statement

Healthcare conversations are rarely straightforward. Users often:

* provide incomplete information,
* ask multiple questions in a single message,
* continue previous conversations,
* or request general healthcare information alongside transactional tasks.

A traditional sequential chatbot struggles to manage these scenarios efficiently.

The goal was therefore to design a chatbot capable of:

* Understanding user intent
* Managing conversation state
* Collecting missing information
* Executing healthcare tools
* Retrieving healthcare knowledge through semantic search

---

# 3. Technology Stack

| Component            | Technology                  |
| -------------------- | --------------------------- |
| Backend              | FastAPI                     |
| Workflow Engine      | LangGraph                   |
| Programming Language | Python                      |
| Database             | SQLite                      |
| Vector Database      | ChromaDB                    |
| Embeddings           | all-MiniLM-L6-v2            |
| LLM Providers        | Google Gemini, Groq, Nebius |
| Frontend             | HTML, CSS, JavaScript       |

---

# 4. Architecture Evolution

The project initially followed a traditional sequential architecture.

```text
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

Although functional, this architecture became increasingly difficult to extend as new capabilities such as conversation memory, slot filling, and multi-intent execution were introduced.

To address these limitations, the project was completely refactored using **LangGraph**.

```text
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
├── Execute Tool
└── FAQ Retrieval (RAG)
```

Instead of executing a fixed sequence of steps, LangGraph orchestrates the conversation through independent nodes, making the workflow modular, maintainable, and easier to extend.

---

# 5. LangGraph Workflow

The chatbot workflow is composed of specialized nodes, each responsible for a single task.

| Node                    | Responsibility                                  |
| ----------------------- | ----------------------------------------------- |
| Resume Conversation     | Restores unfinished conversations               |
| Continue Conversation   | Continues slot filling using stored session     |
| Cancel Conversation     | Clears active conversation state                |
| Hybrid Intent Detection | Combines rule-based detection with LLM fallback |
| Parameter Extraction    | Extracts specialty, dates, and patient details  |
| Slot Filling            | Requests missing parameters from the user       |
| Execute Tool            | Executes one or multiple healthcare tools       |
| FAQ Retrieval           | Retrieves healthcare information using ChromaDB |

This modular workflow makes adding new features significantly easier without affecting the rest of the system.

---

# 6. Design Decisions

Several architectural decisions were made to improve both performance and maintainability.

| Decision                | Reason                                                  |
| ----------------------- | ------------------------------------------------------- |
| LangGraph               | Stateful workflow orchestration                         |
| Hybrid Intent Detection | Fast rule-based execution with intelligent LLM fallback |
| SQLite                  | Lightweight database suitable for rapid development     |
| ChromaDB                | Efficient semantic retrieval of healthcare FAQs         |
| Multiple LLM Providers  | Flexibility and provider independence                   |
| Modular Components      | Easier testing, maintenance, and future expansion       |

These decisions reduced coupling between components and improved the scalability of the application.

---

# 7. Key Features

The final chatbot includes:

* Appointment booking
* Appointment status checking
* Prescription refill requests
* Test result retrieval
* Hybrid intent detection
* Multi-provider LLM support
* Slot filling
* Conversation memory
* Resume conversations
* Cancel conversations
* Multi-intent execution
* RAG-powered FAQ retrieval

---

# 8. Engineering Improvements

Throughout development, the project underwent several architectural improvements.

* Replaced sequential architecture with LangGraph
* Removed the monolithic orchestration layer
* Introduced graph-based workflow execution
* Added conversation state management
* Implemented slot filling for incomplete requests
* Added resume and cancel conversation support
* Enabled execution of multiple intents in a single request
* Integrated semantic FAQ retrieval using ChromaDB
* Improved modularity and separation of concerns

These improvements transformed the chatbot from a simple request-response system into a stateful conversational AI application.

---

# 9. Results

The completed system successfully demonstrates:

* Intelligent intent detection
* Structured parameter extraction
* Stateful conversation management
* Multi-turn dialogue handling
* Multi-intent execution
* Semantic FAQ retrieval
* Modular workflow orchestration through LangGraph

The final architecture is significantly more maintainable than the original implementation and provides a strong foundation for future enhancements.

---

# 10. Future Scope

Potential future improvements include:

* Electronic Health Record (EHR) integration
* Authentication and user profiles
* Doctor availability APIs
* Voice-based interaction
* Medication reminders
* Cloud deployment using Docker and Kubernetes
* Monitoring and observability
* Automated testing and CI/CD

---

# 11. Conclusion

This project evolved from a traditional intent-based chatbot into a modular, stateful conversational AI system.

Migrating from a sequential architecture to **LangGraph** enabled conversation memory, slot filling, multi-intent execution, and semantic FAQ retrieval while improving code organization and maintainability.

Beyond implementing healthcare tools, the project demonstrates an understanding of modern conversational AI architecture, workflow orchestration, and software engineering best practices. The resulting solution is scalable, extensible, and well-suited as a foundation for more advanced healthcare assistant applications.
