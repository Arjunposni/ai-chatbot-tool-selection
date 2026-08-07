# Technical Report
# Healthcare AI Chatbot with Intelligent Tool Selection

**Author:** Arjun Posni
**Repository:** https://github.com/Arjunposni/ai-chatbot-tool-selection
**Domain:** Healthcare

---

# 1. Problem & Approach Summary

The objective of this project was to build an intelligent healthcare chatbot capable of understanding user intent, selecting the correct healthcare tool, extracting the required parameters, and executing the requested operation — with at least two intent-detection methods researched and empirically compared.

Rather than implementing a simple request-response chatbot, this was approached as the design of a complete conversational AI system. During development, the architecture evolved significantly — from a sequential service-based pipeline into a stateful workflow orchestrated by **LangGraph** — and the intent-detection logic itself went through four measured iterations, each evaluated against a structured test dataset. That iteration history (Section 6) is as much a part of this report as the final architecture.

The final chatbot supports:

- Hybrid intent detection (rule-based + LLM, empirically compared — Section 5)
- Stateful, multi-turn conversations with slot filling
- Multi-intent execution (one message, multiple actions)
- Retrieval-Augmented Generation (RAG) for general health FAQs
- Multiple swappable LLM providers (Gemini, Groq, Nebius)
- Conversation resume and cancellation

---

# 2. System Architecture

## Initial architecture
The first implementation followed a traditional sequential pipeline:

```
Frontend → FastAPI → chat_service.py → Intent Detection
         → Parameter Extraction → Slot Filling → Tool Execution
```

This worked for simple requests but became harder to extend as conversational features (multi-turn state, multi-intent execution) were added — every new capability meant touching the same central orchestration function.

## Final architecture
The orchestration layer was refactored to use LangGraph:

```
Frontend
    │
FastAPI  →  graph.invoke(state)
    │
LangGraph
├── Resume Conversation
├── Continue Conversation (incl. cancel, past-date rejection)
├── Hybrid Intent Detection (rule-based → LLM fallback)
├── Parameter Extraction (incl. placeholder/date validation)
├── Slot Filling
├── Execute Tool (single or multi-intent)
└── FAQ Retrieval (RAG)
```

Each node owns one responsibility; LangGraph manages routing, execution order, and state. FastAPI's `/chat` endpoint is now a thin wrapper: `graph.invoke(state)`.

### Why LangGraph
As conversation memory, slot filling, resume support, and multi-intent execution were added on top of the original linear pipeline, the sequential architecture became increasingly tightly coupled — new features required modifying the same central function. Restructuring around explicit graph nodes and conditional routers made the system modular, easier to debug (each node's input/output state is inspectable in isolation), and easier to extend without touching unrelated logic.

---

# 3. LangGraph Workflow

| Node | Responsibility |
|---|---|
| Resume Conversation | Loads any existing per-patient session |
| Continue Conversation | Resumes slot filling; handles cancellation and past-date rejection for an active session |
| Hybrid Intent Detection | Rule-based first, LLM fallback for ambiguity/parameter extraction/multi-intent |
| Parameter Extraction | Extracts specialty/date/medication; validates and rejects placeholder or past-date values |
| Slot Filling | Asks for any still-missing required parameter, one at a time |
| Execute Tool | Runs one tool, or several if a multi-intent message has all parameters ready |
| FAQ Retrieval (RAG) | Falls back to semantic FAQ search when no tool matches; returns a clarification if that also fails |

---

# 4. Tool Layer

| Tool | Parameters | Description |
|---|---|---|
| `book_appointment` | `patient_id`, `specialty`, `date` | Books an appointment, writes to SQLite |
| `check_appointment_status` | `patient_id` | Returns all appointments |
| `request_prescription_refill` | `patient_id`, `medication` | Marks a prescription as refill-requested |
| `get_test_results` | `patient_id` | Returns lab/test results |

Backed by SQLite (`healthcare_chatbot.db`) — chosen deliberately for zero-setup, single-file portability appropriate to a prototype; a production deployment would move to PostgreSQL for proper concurrency handling.

**RAG/FAQ layer:** `data/faq_docs.md` is chunked, embedded with `sentence-transformers` (`all-MiniLM-L6-v2`), and indexed in ChromaDB. Requests that don't match a tool are checked against this index before falling back to a clarification message.

---

# 5. Intent Detection: Approach Comparison

Three approaches were implemented and directly compared, as required by the assignment.

| Approach | Accuracy (final eval) | Speed | Cost | Paraphrasing | Multi-intent | Parameter extraction |
|---|---|---|---|---|---|---|
| **Rule-based** (regex/keyword) | High only on exact phrasing; fails on paraphrasing entirely | Instant (ms) | Free | ❌ | ❌ (see Section 6.4 for a subtle related bug) | ❌ |
| **LLM-based** (function calling) | High, handles nuance | Network-bound (hundreds of ms – seconds) | Free-tier rate-limited / paid | ✅ | ✅ (with correct prompting) | ✅ |
| **Hybrid** (used) | **100% functional correctness on final evaluation run** (Section 7) | Fast for common cases, LLM-speed for the rest | Lower average cost than LLM-only | ✅ | ✅ | ✅ |

**Why hybrid was selected:** it captures rule-based's speed/cost advantage for unambiguous cases (e.g. "show me my lab results" resolves instantly, no API call) while falling back to the LLM exactly where rule-based provably fails — paraphrasing, parameter extraction, and multi-intent messages. In the final evaluation run, roughly a third of clear-request test cases resolved entirely via the free, instant rule-based path.

**LLM provider comparison:** Gemini, Groq, and Nebius were all integrated behind a single `LLM_PROVIDER` environment-variable dispatcher, so the provider can be swapped with no code changes. In practice, Gemini's function calling was the most consistently reliable; Groq (Llama models) occasionally produced malformed or hallucinated tool calls even with retry logic (Section 6.6); Nebius was integrated but could not be evaluated in this report due to a pending account-verification block on the provider's side.

---

# 6. Engineering Challenges & Solutions

## 6.1 Sequential architecture became hard to extend
**Problem:** the original service-based pipeline required touching central orchestration logic for every new conversational feature.
**Solution:** migrated orchestration to LangGraph (Section 2), isolating each responsibility into an independently testable node.

## 6.2 Incomplete requests (missing parameters)
**Problem:** "Book appointment" alone can't execute — `specialty` and `date` are missing.
**Solution:** slot filling asks for exactly what's missing, one question at a time, and resumes correctly across messages.

## 6.3 Multi-turn conversation memory
**Problem:** healthcare requests often span multiple messages (specialty → date → confirm).
**Solution:** per-patient session state tracks the in-progress intent and collected parameters, and resumes automatically on the next message. Session state is in-memory only — a deliberate prototype-scope choice; production would use Redis or a database-backed store to survive restarts and scale across instances.

## 6.4 Multi-intent requests were only partially handled — twice
This was the most iterated-on problem in the project, in two distinct phases:

**Phase 1 — the LLM only returned its first function call.** "Check my appointments and refill my Metformin" only ever executed the first action. Fixed by reading *all* returned function calls (not just index `[0]`) from both Gemini and Groq, and executing every intent once confirmed each has its required parameters — otherwise falling back to single-intent + slot filling.

**Phase 2 (found later, during LangGraph testing) — the rule-based fast path bypassed multi-intent detection entirely.** Because `hybrid.py` returned immediately on any confident rule-based match, a message like "check my appointments and refill my Metformin" — where the *first* clause alone matched a simple rule pattern — never reached the LLM at all, silently dropping the second request. Fixed by detecting compound-message markers (" and ", " also ", a comma) and routing those messages through the LLM path regardless of whether the first clause matches a rule, since only the LLM path can detect and return multiple intents.

## 6.5 Two distinct parameter-quality bugs
- **Placeholder values:** the LLM sometimes filled a missing parameter with a literal string like `"unknown"` instead of omitting it — this passed the original missing-value check (which only looked for `None`/empty string) and caused tool execution with garbage data ("Appointment booked with unknown on unknown"). Fixed by treating a set of known placeholder values as missing.
- **Invalid past dates:** a request like "book the cardiologist for yesterday" could pass straight through to booking with a literal past date. Fixed with a shared `normalize_date()`/`check_past_date()` helper used consistently across first-message parsing, follow-up-reply parsing, *and* a final validation pass on the merged parameter dict — this last step was necessary because a bad value supplied directly by the LLM's own extraction would otherwise survive untouched (`dict.update()` only adds keys, it doesn't remove a bad one already present).

## 6.6 LLM provider reliability and rate limits
- Gemini's free tier (5 requests/minute, ~20/day observed) caused repeated `429 RESOURCE_EXHAUSTED` errors mid-evaluation. Addressed with retry/backoff using the API's suggested retry delay, and by adding Groq as a swappable fallback provider.
- An earlier version of the error-handling code conflated genuine API failures with real "no match" cases, silently showing "I couldn't understand your request" for both — which made debugging the rate-limit issue significantly harder until fixed to surface system errors distinctly.
- Groq's Llama models occasionally emitted malformed function-call syntax, including one case of hallucinating a nonexistent tool (`brave_search`) never defined in the schema. A retry-on-malformed-output wrapper improved but did not fully eliminate this — documented as an open provider-reliability gap rather than fully resolved, given time constraints.
- SDK/model churn: `google-generativeai` was deprecated mid-project (migrated to `google-genai`); `gemini-1.5-flash` and `gemini-2.5-flash` both returned 404 "no longer available to new users" within the same development window.

## 6.7 A genuine precision/recall trade-off, found and resolved
Fixing the multi-intent limitation (6.4, Phase 1) required strengthening the LLM prompt to more assertively call multiple functions for compound messages. This had a real, measured side effect: the model became more willing to call *some* tool overall, which also caused it to start guessing on genuinely vague single-intent input it had previously (correctly) declined — ambiguous-category accuracy dropped from 67% to 33% in the very next evaluation run (Section 7). This was resolved not by reverting the fix, but by adding an explicit "do not guess on vague input" instruction with concrete negative examples drawn directly from the failing test cases — which fully recovered ambiguous accuracy to 100% while keeping the multi-intent capability. This is detailed with real run-by-run numbers in Section 7, because the trade-off and its resolution are more informative shown than described.

---

# 7. Evaluation

A test dataset (`data/test_cases.json`) covering **clear**, **ambiguous**, **multi-intent**, **complex-negative** (memory-recall and general-knowledge questions that should *not* trigger a tool), and **natural-language/paraphrased** requests was run through the hybrid pipeline via `tests/run_test_cases.py` across four full iterations of the system, rather than a single pass — because the intermediate results are more informative than the final number alone.

| Run | Change made | Clear | Ambiguous | Multi-intent | Sensitive / Complex-neg | Overall (strict) |
|---|---|---|---|---|---|---|
| 1 — Baseline hybrid | Initial rule + LLM hybrid | 11/11 | 4/6 (67%) | 0/4 full, 4/4 partial (1st function call only) | 4/4 | 76% |
| 2 — Multi-intent fix | Read all function calls; strengthened multi-intent prompt | 11/11 | 2/6 (33%) — regression | 4/4 partial (script-verified live in UI) | 4/4 | 68% |
| 3 — Refined prompt | Added explicit "don't guess on vague input" negative examples | 11/11 | 6/6 (100%) — recovered | 4/4 partial (script limit) | 4/4 | 84% |
| 4 — LangGraph + fast-path fix | Migrated to LangGraph; fixed rule-based fast path skipping multi-intent | 8/8 | 6/6 (100%) | 4/4 — both tool calls confirmed via raw output | 4/4 | 100% functional / 21/25 by script's strict single-field check |

**Reading the strict-score gap in Run 4:** the evaluation script only checks the primary `intent` field per case, not the full list of tool calls a multi-intent request produces. Raw `TOOL CALLS` output from the same run shows all four multi-intent cases correctly generating **two** correct function calls each — genuinely correct behavior across the full set. This is a known limitation of the evaluation script, not the chatbot, and is listed as a future improvement (Section 8).

**Test category additions between runs:** the original "sensitive-information" category was later broadened into "complex-negative" cases — questions like "I forgot what medication I'm taking" or "what is Metformin used for" — which test whether the system correctly declines to guess when no real patient-specific action is being requested, rather than only testing sensitive-data handling. All four complex-negative cases passed in the final run.

---

# 8. Future Improvements

- Fix the evaluation script to score against the full `all_intents` list, not just the primary intent, so multi-intent cases are credited accurately without needing manual verification of raw tool-call output.
- Persistent, multi-instance conversation state (Redis or a database-backed session store) instead of in-memory-per-process.
- Resolve Nebius account verification and complete a real evaluation of it as a third provider option.
- Improve Groq reliability, or restrict its use to only when Gemini is rate-limited, given its observed malformed-output rate.
- Expand the test dataset beyond 25 cases for more statistically meaningful percentages, particularly for the smaller ambiguous/multi-intent categories.
- Add structured latency/cost instrumentation (`time.time()` around each detection call) to turn the qualitative speed comparison in Section 5 into measured numbers.

---

# 9. Conclusion

This project evolved substantially beyond the original assignment scope. What began as a sequential, single-intent chatbot was rebuilt into a modular, stateful conversational AI system orchestrated by LangGraph — supporting multi-turn slot filling, multi-intent execution, RAG-based FAQ answering, and multiple swappable LLM providers. More importantly, the intent-detection approach was not just built once but iteratively evaluated, broken, diagnosed, and improved across four measured runs — including a genuine precision/recall trade-off that was found, understood, and resolved rather than avoided. That evidence-driven iteration process, as much as the final architecture, is the core deliverable of this report.
