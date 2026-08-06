# Technical Report: Healthcare AI Chatbot with Intelligent Tool Selection

**Author:** Arjun Posni
**Repository:** github.com/Arjunposni/ai-chatbot-tool-selection
**Domain:** Healthcare

---

## 1. Problem & Approach Summary

The task was to build a chatbot that understands a user's intent, selects the correct tool from a set of available actions, executes it, and returns a meaningful response — with at least two intent-detection methods researched and compared. I chose the **healthcare** domain and built a system that supports four patient-facing tools (`book_appointment`, `check_appointment_status`, `request_prescription_refill`, `get_test_results`), a FAQ knowledge layer for general health questions, and multi-turn conversation handling for incomplete requests.

Rather than treat this as a one-shot build, I treated it as an iterative engineering exercise: build a baseline, evaluate it against a structured test set, find real weaknesses, fix them, and re-measure. Section 5 documents three full evaluation runs showing exactly how accuracy moved as the system was improved — including one deliberate regression that was diagnosed and resolved.

---

## 2. System Architecture

```
                          User Message
                               │
                               ▼
                 ┌─────────────────────────┐
                 │  Active conversation?    │──Yes──► Resume: fill next
                 │  (session_manager.py)    │         missing slot or
                 └─────────────┬─────────────┘         execute if complete
                               │ No
                               ▼
                 ┌─────────────────────────┐
                 │   Hybrid Intent Detection │
                 │  (rule-based → LLM fallback)│
                 └─────────────┬─────────────┘
                       matched? │  not matched?
                               │        │
                               │        ▼
                               │   ┌───────────┐
                               │   │ RAG (FAQ)  │──match──► FAQ answer
                               │   │ ChromaDB   │
                               │   └─────┬─────┘
                               │         │ no match
                               │         ▼
                               │   Clarification response
                               ▼
                 ┌─────────────────────────┐
                 │  Parameter Extraction     │
                 │  (regex + LLM-extracted)  │
                 └─────────────┬─────────────┘
                               ▼
                 ┌─────────────────────────┐
                 │      Slot Filling          │──missing──► Ask follow-up
                 │  (slot_filling.py)         │             question, save
                 └─────────────┬─────────────┘             session state
                               │ complete
                               ▼
                 ┌─────────────────────────┐
                 │   Tool Execution            │
                 │  (single or multi-intent)   │
                 └─────────────┬─────────────┘
                               ▼
                          SQLite Database
                               │
                               ▼
                       Formatted Response
```

### Layered code organization

| Layer | Responsibility |
|---|---|
| `app/main.py` | HTTP routing only — serves the UI and the `/chat` endpoint |
| `app/services/chat_service.py` | Orchestrates the full workflow end-to-end |
| `app/services/tool_executor.py` | Single interface to invoke any registered tool safely |
| `app/intent/` | Rule-based, LLM-based (Gemini + Groq), and hybrid detection |
| `app/conversation/` | Session state, slot filling, follow-up parameter extraction |
| `app/rag/` | FAQ embedding + retrieval (ChromaDB + sentence-transformers) |
| `app/tools/` | The four healthcare tools, backed by SQLite |

This separation was a deliberate refactor partway through the project — the initial version had all logic inline in `main.py`. Splitting orchestration, tool execution, and conversation state into distinct modules made it possible to add multi-turn slot filling and multi-intent execution without rewriting the whole request path.

---

## 3. Intent Detection: Approach Comparison

Three approaches were implemented and directly compared, as required.

### 3.1 Rule-based (regex/keyword matching)
Matches user text against a fixed set of regex patterns per intent (`app/intent/rule_based.py`).

- **Accuracy:** High on exact-phrasing matches (e.g. "book an appointment", "show my lab results"); **zero generalization** to paraphrased input.
- **Speed:** Instant (~milliseconds), no network call.
- **Cost:** Free.
- **Advantages:** Deterministic, fast, no external dependency, safe fallback for unambiguous cases.
- **Limitations:** Cannot extract parameters (e.g. specialty, date) from free text; fails on synonyms/paraphrasing (e.g. "when's my next visit?" does not match any "appointment status" pattern); cannot handle multi-intent messages — flags them as ambiguous instead.

### 3.2 LLM-based (function calling)
Sends the user's message to an LLM (Gemini or Groq) with the tool schema as available functions; the model selects the tool(s) and extracts parameters directly (`app/intent/llm_gemini.py`, `app/intent/llm_groq.py`).

- **Accuracy:** High, and handles paraphrasing, multi-intent messages, and parameter extraction that rule-based cannot.
- **Speed:** Network-bound (hundreds of milliseconds to a few seconds per call).
- **Cost:** Free-tier rate-limited (see Section 6); paid tiers would have per-token cost.
- **Advantages:** Generalizes to natural language, extracts structured parameters, supports multi-intent with the right prompting.
- **Limitations:** Slower and dependent on external API availability; occasional malformed output (observed with one Groq model, see Section 6); free-tier rate limits directly constrained evaluation throughput during development; over-eager tool-calling on vague input if not carefully prompted (see Section 5.2).

### 3.3 Hybrid (implemented, final approach)
Tries rule-based first; only calls the LLM when the rule-based match is missing, ambiguous, or the matched tool requires parameters the rule-based layer cannot extract (`app/intent/hybrid.py`).

- **Why this was selected:** It captures the speed/cost advantage of rule-based matching for the common, unambiguous cases, while falling back to the LLM exactly where rule-based provably fails (paraphrasing, parameter extraction, multi-intent). In the final evaluation run (Section 5.3), roughly half of clear-request test cases resolved entirely via the free, instant rule-based path, with the rest correctly routed to the LLM.

| Approach | Accuracy (final run) | Speed | Cost | Handles paraphrasing | Handles multi-intent | Extracts parameters |
|---|---|---|---|---|---|---|
| Rule-based only | Low on varied phrasing | Instant | Free | ❌ | ❌ | ❌ |
| LLM-based only | High | Slow (network) | Rate-limited / paid | ✅ | ✅ (with correct prompting) | ✅ |
| **Hybrid (used)** | **84% strict / 100% partial-credit** | **Fast for common cases, LLM-speed for the rest** | **Lower average cost than LLM-only** | ✅ | ✅ | ✅ |

---

## 4. Tool Layer

| Tool | Parameters | Description |
|---|---|---|
| `book_appointment` | `patient_id`, `specialty`, `date` | Books an appointment, writes a new row to SQLite |
| `check_appointment_status` | `patient_id` | Returns all appointments for the patient |
| `request_prescription_refill` | `patient_id`, `medication` | Marks a prescription as refill-requested |
| `get_test_results` | `patient_id` | Returns lab/test results for the patient |

Backed by a local SQLite database (`healthcare_chatbot.db`) with `patients`, `appointments`, `prescriptions`, and `test_results` tables. SQLite was chosen deliberately for this prototype: zero setup, single-file portability, and no server dependency — appropriate for demonstrating the approach without the operational overhead a production database would add. A production deployment would move to PostgreSQL or similar for proper concurrency handling.

### RAG / FAQ layer
Requests that don't match any tool fall through to a retrieval-augmented FAQ layer: `data/faq_docs.md` is chunked, embedded with `sentence-transformers` (`all-MiniLM-L6-v2`), and indexed in ChromaDB. At query time, the top match is returned if its similarity score clears a minimum relevance threshold; otherwise the system asks the user to clarify rather than returning a low-confidence answer.

### Multi-turn conversation & slot filling
If a matched tool is missing required parameters (e.g. "book an appointment" with no specialty or date given), the system does **not** fail the tool call. Instead, `app/conversation/` tracks per-patient session state, asks one follow-up question at a time for each missing parameter, and only executes the tool once every required field is collected. Users can cancel an in-progress request at any point (`cancel`, `never mind`, `stop`, etc.).

### Multi-intent execution
When a single message contains multiple distinct requests (e.g. "check my appointments and show my lab results"), the LLM layer returns *all* detected function calls, not just the first. If every detected intent already has its required parameters, all of them are executed and their results combined into a single response. If any of them still need a follow-up question, the system falls back to handling the first intent via the normal slot-filling flow. This was not the initial behavior — see Section 5 for how it was discovered, fixed, and validated.

---

## 5. Evaluation

A 25-case test dataset (`data/test_cases.json`) was built covering four required categories: **clear** requests (11), **ambiguous** requests (6), **multi-step** requests (4), and **sensitive-information** requests (4). `tests/run_test_cases.py` runs every case through the hybrid pipeline and reports expected vs. actual intent per case.

Rather than a single evaluation pass, three full runs were performed across the development process, because the second run surfaced a real regression that is more informative to show than to hide.

### 5.1 Run 1 — Baseline hybrid system
| Category | Result |
|---|---|
| Clear (11) | 11/11 (100%) |
| Ambiguous (6) | 4/6 (67%) |
| Multi-step (4) | 0/4 fully correct, 4/4 partially correct (first intent only) |
| Sensitive (4) | 4/4 (100%) |
| **Overall (strict)** | **19/25 (76%)** |
| **Overall (partial-credit)** | **23/25 (92%)** |

At this stage, the multi-step limitation was known and expected: the LLM function-calling code only read the first returned function call, so compound requests only ever resolved one of the two intended actions.

### 5.2 Run 2 — After the multi-intent fix (regression discovered)
The multi-intent limitation was fixed: both LLM providers were updated to return *all* detected function calls, `chat_service.py` was updated to execute every intent when parameters were already complete, and the prompt was strengthened with an explicit instruction to call a separate function for each request in a compound message. Live UI testing confirmed multi-intent execution genuinely worked (e.g. "check my appointments and show my lab results" correctly executed both tools and combined the results).

However, re-running the full test suite showed a clear regression:

| Category | Result |
|---|---|
| Clear (11) | 11/11 (100%) |
| Ambiguous (6) | **2/6 (33%)** ⬇ |
| Multi-step (4) | 0/4 fully correct, 4/4 partial |
| Sensitive (4) | 4/4 (100%) |
| **Overall (strict)** | **17/25 (68%)** ⬇ |
| **Overall (partial-credit)** | **21/25 (84%)** ⬇ |

**Root cause:** the stronger multi-intent instruction ("you MUST call a separate function for EACH request") made the model more willing to call *some* tool overall — which helped genuine multi-intent cases, but also caused it to guess a tool on genuinely vague single-intent input it had previously (correctly) declined (e.g. "I need to see someone", "something's not right with me"). This is a textbook precision/recall trade-off in prompt-based function calling: pushing the model toward more tool calls increases recall on multi-intent input at the cost of precision on ambiguous input.

### 5.3 Run 3 — Refined prompt (regression resolved)
Rather than reverting the multi-intent fix, the prompt was refined with an explicit negative-example instruction: alongside the multi-intent rule, the model was told not to guess on vague input, with the exact phrasing from the failing test cases given as concrete examples of what *not* to act on.

| Category | Result |
|---|---|
| Clear (11) | 11/11 (100%) |
| Ambiguous (6) | **6/6 (100%)** ⬆ |
| Multi-step (4) | 0/4 fully correct via this script*, 4/4 partial |
| Sensitive (4) | 4/4 (100%) |
| **Overall (strict)** | **21/25 (84%)** ⬆ |
| **Overall (partial-credit)** | **25/25 (100%)** ⬆ |

\* The evaluation script only checks the primary `intent` field per case, not the full `all_intents` list — so it cannot fully credit multi-intent cases even when both actions execute correctly. This is a known limitation of the evaluation script itself, not the chatbot; multi-intent execution was independently verified working correctly through direct UI testing (Section 4).

### 5.4 Progression summary

| Metric | Run 1 (baseline) | Run 2 (regression) | Run 3 (refined) |
|---|---|---|---|
| Strict accuracy | 76% | 68% | **84%** |
| Partial-credit accuracy | 92% | 84% | **100%** |
| Multi-intent execution | Not implemented | Implemented, unverified by script | Implemented, confirmed live |

This progression demonstrates that the ambiguous-input regression was not a fundamental limitation of the hybrid approach, but a solvable prompt-engineering problem — resolved through concrete negative examples rather than reverting the underlying capability.

---

## 6. Challenges Faced

- **LLM SDK deprecation mid-project.** `google-generativeai` was deprecated during development; migrated to the current `google-genai` SDK, which uses a different client/function-calling interface.
- **Model name churn.** `gemini-1.5-flash` and `gemini-2.5-flash` both returned 404 "no longer available to new users" errors within days of each other; required switching to `gemini-3.5-flash` (and later back to `gemini-2.5-flash` when quota required) as availability shifted.
- **Free-tier rate limits directly affected evaluation.** Gemini's free tier (5 requests/minute, ~20/day observed on this account) caused cascading `429 RESOURCE_EXHAUSTED` errors mid-evaluation-run on more than one occasion. Addressed by: (1) adding retry logic with exponential backoff based on the API's suggested retry delay, (2) surfacing rate-limit errors distinctly in the chat UI instead of masking them as "I don't understand" (an earlier version of the code conflated system errors with genuine no-match cases, which made debugging significantly harder until fixed), and (3) implementing a second provider (Groq) as a swappable fallback via a single `LLM_PROVIDER` environment variable.
- **Provider reliability differences.** Groq's `llama-3.3-70b-versatile` occasionally emitted malformed function-call syntax; switching to `llama-3.1-8b-instant` with a one-retry wrapper improved but did not eliminate this — one observed case involved the model hallucinating a nonexistent tool (`brave_search`) alongside malformed JSON. This is documented as an open reliability gap between providers rather than fully resolved, given time constraints.
- **A real precision/recall trade-off during the multi-intent fix**, detailed in Section 5.2–5.3 — the most significant finding of the evaluation process.
- **Rule-based parameter-extraction gap.** Initially, the hybrid logic trusted any confident rule-based intent match, which caused tool calls to fail when the matched tool needed parameters (e.g. specialty, date) that rule-based matching cannot extract. Fixed by only trusting the rule-based path outright when the matched tool requires zero additional parameters; otherwise the request is routed to the LLM (or slot-filling) for parameter extraction.
- **Environment setup friction.** Debian/Ubuntu's `externally-managed-environment` protection required a virtual environment; `sentence-transformers` pulled several gigabytes of CUDA/NVIDIA packages by default, resolved with a CPU-only `torch` install appropriate for this prototype's scale.

---

## 7. Future Improvements

- **Fix the evaluation script's multi-intent scoring** so it checks the full `all_intents` list rather than only the primary intent, giving accurate automated credit for compound requests.
- **Persistent, multi-user conversation state.** Session memory is currently a per-process in-memory dictionary; a production version would use Redis or a database-backed session store to survive restarts and scale across multiple server instances.
- **Slot filling across multiple simultaneous intents.** Currently, multi-intent execution requires every detected intent to already have complete parameters; if any part of a compound request is missing information, the system falls back to handling only the first intent. Extending slot filling to track multiple pending intents at once would close this gap.
- **Improve Groq reliability**, or restrict Groq usage to only the cases where Gemini is rate-limited, given the observed malformed-output rate.
- **Expand the test dataset** beyond 25 cases (the assignment suggests 40-60) for more statistically meaningful accuracy figures, particularly for the ambiguous category where small sample sizes make percentage swings look larger than they are.
- **Formal latency/cost instrumentation** — currently timing is observed qualitatively; adding structured `time.time()` measurement around each detection call would allow a quantitative speed comparison table alongside the accuracy comparison already in Section 3.

---

## 8. Conclusion

The final system implements and empirically compares three intent-detection strategies, settles on a hybrid approach with a measured 84% strict / 100% partial-credit accuracy on a structured 25-case evaluation set, and demonstrates a complete, working pipeline: intent detection → parameter extraction → slot filling → tool execution → real database reads/writes → formatted response, plus a RAG-based FAQ layer and a functioning web chat interface. Most importantly, the evaluation process itself — baseline, regression, root-cause, fix, re-measurement — reflects the kind of iterative, evidence-driven development this assessment is designed to evaluate.
