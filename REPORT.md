# Technical Report
# Healthcare AI Chatbot with Intelligent Tool Selection

**Author:** Arjun Posni  
**Repository:** https://github.com/Arjunposni/ai-chatbot-tool-selection  
**Domain:** Healthcare

---

# 1. Problem & Approach Summary

The objective of this project was to build an intelligent healthcare chatbot capable of understanding user intent, selecting the correct healthcare tool, extracting the required parameters, and executing the requested operation. Rather than implementing a simple request-response chatbot, the system evolved into a stateful conversational AI orchestrated by **LangGraph** after several design iterations.

The final chatbot supports:

- Hybrid intent detection (rule-based + LLM)
- Stateful multi-turn conversations with slot filling
- Multi-intent execution
- Retrieval-Augmented Generation (RAG) for healthcare FAQs
- Swappable LLM providers (Gemini, Groq, Nebius)
- Conversation resume and cancellation

---

# 2. System Architecture

## Initial Architecture

```text
Frontend → FastAPI → chat_service.py → Intent Detection
         → Parameter Extraction → Slot Filling → Tool Execution
```

The sequential pipeline worked well for simple requests but became difficult to extend as conversation memory, slot filling, and multi-intent support were introduced.

## Final Architecture

```text
Frontend
    │
FastAPI → graph.invoke(state)
    │
LangGraph
├── Resume Conversation
├── Continue Conversation
├── Hybrid Intent Detection
├── Parameter Extraction
├── Slot Filling
├── Execute Tool
└── FAQ Retrieval (RAG)
```

Each node has a single responsibility, making the workflow modular, easier to debug, and easier to extend.

---

# 3. LangGraph Workflow

| Node | Responsibility |
|------|----------------|
| Resume Conversation | Restore previous session |
| Continue Conversation | Resume slot filling, handle cancellation and past-date validation |
| Hybrid Intent Detection | Rule-based first, LLM fallback |
| Parameter Extraction | Extract specialty, medication, and dates |
| Slot Filling | Request only the missing parameters |
| Execute Tool | Execute one or multiple tools |
| FAQ Retrieval | Semantic FAQ search using ChromaDB |

---

# 4. Tool Layer

| Tool | Description |
|------|-------------|
| `book_appointment` | Books an appointment |
| `check_appointment_status` | Retrieves appointments |
| `request_prescription_refill` | Requests a prescription refill |
| `get_test_results` | Returns laboratory results |

SQLite was selected because it is lightweight, portable, and requires no setup, making it ideal for a prototype. FAQ documents are embedded using **sentence-transformers** and indexed in **ChromaDB** for semantic retrieval.

---

# 5. Intent Detection: Approach Comparison

| Approach | Accuracy | Speed | Cost | Paraphrasing | Multi-intent | Parameter Extraction |
|----------|----------|-------|------|--------------|--------------|----------------------|
| Rule-based | Good on exact phrases | Very Fast | Free | ❌ | ❌ | ❌ |
| LLM-based | High | Slower | API Cost | ✅ | ✅ | ✅ |
| **Hybrid (Final)** | **100% functional correctness** | Fast + LLM fallback | Lower | ✅ | ✅ | ✅ |

The hybrid approach combines the speed of rule-based matching with the flexibility of LLMs. Straightforward requests are handled instantly, while ambiguous or multi-intent queries are delegated to the LLM.

Among the integrated providers, **Gemini** proved the most reliable. **Groq** occasionally generated malformed tool calls, while **Nebius** was integrated but could not be fully evaluated because of account verification restrictions.

---

# 6. Engineering Challenges & Solutions

### 6.1 Sequential Architecture

The original service-based pipeline became difficult to maintain as conversational features increased. Migrating to LangGraph separated responsibilities into independent workflow nodes.

### 6.2 Missing Parameters

Incomplete requests such as *"Book an appointment"* cannot execute immediately. Slot filling asks only for the missing information before continuing.

### 6.3 Multi-turn Conversation Memory

Per-patient session state stores the active intent and collected parameters, allowing conversations to continue naturally across multiple messages.

### 6.4 Multi-intent Requests

Initially, only the first detected tool call was executed. The solution was to process every returned function call and ensure compound requests bypass the rule-based fast path so the LLM can detect multiple intents correctly.

### 6.5 Parameter Validation

- Placeholder values such as `"unknown"` are treated as missing inputs.
- Shared date validation rejects appointments scheduled in the past.

### 6.6 LLM Reliability

- Retry and backoff handle Gemini rate limits.
- Groq occasionally produced malformed tool calls.
- Migration from `google-generativeai` to `google-genai` was required after SDK updates.

### 6.7 Precision vs Recall Trade-off

Improving multi-intent detection initially reduced performance on ambiguous requests because the model became more eager to call tools. Adding explicit negative prompting restored ambiguous-case accuracy to **100%** while preserving multi-intent capability.

### 6.8 Single-Dimension Evaluation Scoring

The original evaluation script (`tests/run_test_cases.py`) scored only the primary detected intent field, so it could not verify multi-intent correctness even after the underlying detection logic was fixed (Section 6.4) — Run 4's "100% functional correctness" had to be confirmed manually in the chat UI rather than by the script itself. This was resolved by replacing it with a dedicated eval harness (Section 7.1).

---

# 7. Evaluation

The chatbot was evaluated using a dataset containing clear requests, ambiguous prompts, multi-intent queries, complex-negative cases, and paraphrased natural-language requests.

| Run | Major Change | Overall |
|-----|--------------|---------|
| 1 | Initial Hybrid | 76% |
| 2 | Multi-intent Fix | 68% |
| 3 | Prompt Refinement | 84% |
| 4 | LangGraph + Final Hybrid | 100% functional correctness (confirmed manually; scoring script limited to primary intent) |
| 5 | Eval Harness (`app/eval/scorer.py`) | **25/25 (100%) — verified programmatically across all three scoring dimensions** |

## 7.1 Eval Harness

Run 4 exposed a real limitation: the evaluation script could confirm correctness of the *primary* detected intent, but not the full multi-intent behavior, parameter quality, or execute-vs-decline correctness — those had to be checked by hand. To close this gap, the evaluation script was rebuilt as a proper eval harness (`app/eval/scorer.py`) that scores each of the 25 cases in `data/test_cases.json` on three independent dimensions:

- **Intent match** — the full set of detected tool(s) matches the expected set, not just the first one
- **Behavior match** — correct execute vs. decline vs. multi-intent-execute classification, which specifically covers the ambiguous and complex-negative categories where the correct behavior is refusing to call a tool
- **Parameter match** — extracted parameters are present and correct, with placeholder values (e.g. `"unknown"`) explicitly treated as a failure

Run 5 results, broken down by category:

| Category | Cases | Pass Rate |
|----------|-------|-----------|
| Clear | 8 | 100% |
| Ambiguous | 6 | 100% |
| Multi-intent | 4 | 100% |
| Complex-negative | 4 | 100% |
| Natural language / paraphrased | 3 | 100% |

And by dimension (out of 25 total cases): intent match 25/25, behavior match 25/25, parameter match 25/25 — the first fully programmatic confirmation of what Run 4 could only demonstrate manually.

Each run is saved as a timestamped JSON report under `app/eval/runs/`, tagged via `--tag` (e.g. `baseline`), enabling regression comparison across future changes to prompts, hybrid logic, or LLM provider without re-deriving results by hand.

**Note on interpreting the 25/25 result:** this is a strong baseline, but the test set is fixed and has already been iterated against across five runs. It confirms the hybrid detector correctly handles every known case, not that it generalizes to unseen phrasing — see Section 8.

The final system successfully handled:

- Clear healthcare requests
- Ambiguous user input
- Multi-turn slot filling
- Multi-intent execution
- FAQ retrieval through RAG

---

# 8. Future Improvements

- Expand the evaluation dataset with adversarial cases not already tuned against (new phrasings of ambiguous inputs, three-intent messages, typos), to test generalization rather than memorization of the existing 25 cases.
- Replace in-memory sessions with Redis or a database-backed store.
- Complete Nebius evaluation.
- Improve fallback reliability for Groq.
- Measure latency and API cost quantitatively.
- Add unit tests for individual conversation/parameter-extraction functions (e.g. `date_utils.normalize_date()`, `slot_filling.missing_slots()`) as a complement to the end-to-end eval harness.

---

# 9. Conclusion

This project evolved from a simple sequential chatbot into a modular conversational AI system built with LangGraph. By combining hybrid intent detection, slot filling, multi-intent execution, conversation memory, RAG, and multiple LLM providers, the chatbot satisfies the assignment requirements while remaining modular and extensible. Most importantly, every major architectural decision was validated through iterative evaluation — culminating in a dimension-based eval harness that turned a manually-confirmed result into a programmatically verified one — making the final solution evidence-driven rather than assumption-driven.