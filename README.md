# InterviewGPT Pro (Working Prototype)

A local, runnable implementation of the multi-agent AI interview coaching
platform. This is a **real, functional build** — not a mockup — but it is
scoped down from the full 8-agent spec in a few honest ways explained below.

## Quick Start

```bash
cd interviewgpt_pro
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and add your GROQ_API_KEY (free at console.groq.com/keys)

streamlit run app.py
```

This build runs on **Groq** (fast, free-tier LLM inference — currently
`llama-3.3-70b-versatile` by default). Swap `INTERVIEWGPT_MODEL` in `.env`
for a different Groq-hosted model any time.

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## Workflow

1. **Resume Analysis** — upload a PDF or paste resume text → get ATS score,
   extracted skills, missing skills for your target role, strengths/weaknesses.
2. **Interview Plan** — generates a round-by-round interview strategy based
   on your resume gaps, target role, and company type (FAANG-style,
   startup, mid-size product, service-based).
3. **Live Interview** — adaptive Q&A, now with:
   - **Voice input**: record your answer out loud via the browser mic; it's
     transcribed by Groq's hosted Whisper and dropped into an editable text box.
   - **Live code execution**: DSA rounds present an auto-gradable coding
     problem with a starter function — click "Run Tests" to execute your
     solution against real test cases in a sandboxed subprocess before submitting.
   - **Panel Interview Mode** (sidebar toggle): Technical and HR questions
     alternate within the same session, simulating a real onsite panel loop.
   - Technical questions get harder/easier based on your answers; behavioral
     answers are scored against the STAR method. Hints available on request.
4. **Gap Report & Roadmap** — after the interview, get a readiness score,
   identified weak topics with real knowledge-base citations (now including
   an expanded Google/Amazon/Microsoft-style pattern bank), and a
   personalized week-by-week study roadmap.
5. **Dashboard** — every session is saved to SQLite, so weak topics and
   scores persist and accumulate across visits for the same candidate ID.
6. **Leaderboard** — ranks every candidate who has saved a session by
   average score, for coaching-institute / cohort-style use cases.

## Architecture: Spec → Implementation Mapping

| Original Spec Component | This Build |
|---|---|
| Agent 1: Resume Intelligence | `agents/resume_agent.py` — LLM-based skill extraction, ATS scoring, gap analysis (replaces a BERT/NER pipeline with a single well-prompted model call — simpler to run, no GPU needed) |
| Agent 2: Interview Planner | `agents/planner_agent.py` |
| Agent 3: Technical Interview | `agents/technical_agent.py` — real adaptive difficulty loop |
| Agent 4: HR & Behavioral | `agents/hr_agent.py` — real STAR-method scoring |
| Agent 7: Knowledge Gap Detection | `agents/gap_agent.py` — LLM-based gap detection instead of XGBoost/Random Forest (see note below) |
| Agent 8: Career Coach | `agents/coach_agent.py` |
| Multi-Modal RAG | `core/rag.py` — TF-IDF retrieval over `data/kb/*.md` (swap for ChromaDB/FAISS + embeddings, see below) |
| Long-Term Memory | `core/memory.py` — SQLite (swap for Postgres for production) |
| Multi-agent orchestration | Streamlit session state acts as the orchestrator, calling agents in sequence. Each agent function is stateless and pure, so it's a straightforward swap into LangGraph/CrewAI later. |
| Voice Intelligence (transcription slice) | `core/voice_client.py` — real speech-to-text via Groq's hosted Whisper API, captured in-browser with `streamlit-mic-recorder`. Confidence/filler-word/speaking-speed analysis on top of the transcript is a natural next layer. |
| Live Code Execution | `core/code_executor.py` — sandboxed subprocess runner with a timeout, used by the DSA coding sub-flow in `agents/technical_agent.py` (`generate_coding_question` / `evaluate_code_solution`). |
| Multi-Candidate Leaderboard | `memory.get_leaderboard()` + Dashboard page 6 in `app.py`. |
| Mock Panel Interview | "Panel Interview Mode" sidebar toggle in `app.py` — alternates Technical/HR agents turn by turn instead of running them as separate rounds. |

## What's Deliberately Out of Scope Here (and how to add it)

**Agent 5 (Voice Intelligence)** is now partially implemented: real
speech-to-text works via `core/voice_client.py` (Groq-hosted Whisper).
Still missing from the original spec: confidence estimation, speaking
speed analysis, filler-word detection, and pronunciation evaluation on
top of the transcript. These are all doable as a follow-up LLM pass over
the transcript + basic audio-duration math (words-per-minute), no extra
model needed — add a `analyze_delivery(transcript, audio_duration_sec)`
function to `core/voice_client.py` following the same pattern.

**Agent 6 (Emotion & Facial Intelligence)** requires live webcam capture
and heavy specialized models (MediaPipe, FER, Vision Transformers) that
need a GPU-backed inference server for real-time use. To add it:
- Use `streamlit-webrtc` for browser-side webcam capture (same pattern
  as `streamlit-mic-recorder` for audio, used elsewhere in this app).
- Stand up a separate model-serving microservice for the CV models.
- Create `agents/emotion_agent.py` following the same stateless,
  structured-JSON pattern as the other agents.

**Code execution sandboxing**: `core/code_executor.py` uses a bare
subprocess with a timeout, which is fine for a local single-user
prototype but is NOT a hardened sandbox. Before exposing this to
untrusted multi-tenant users, swap in a real sandbox (Docker container
with no network access, gVisor, Firecracker microVM, or a hosted service
like E2B/Judge0) — see the security note at the top of that file.

**Agent 7's ML models (XGBoost/Random Forest/transformer classifiers)**
need a labeled dataset of past interview outcomes (pass/fail) to train
on, which doesn't exist yet for a new deployment. This build uses the LLM
as a strong zero-shot substitute. Once you've logged enough real session
outcomes via `core/memory.py`, export them and train a classifier —
the `detect_gaps()` function signature won't need to change.

**Deployment stack** (Docker/Kubernetes/MLflow/Prometheus/Grafana) is not
included since this is a local prototype. The app is a single Streamlit
process + SQLite file, so containerizing it is a straightforward next
step (`Dockerfile` wrapping `streamlit run app.py`, mount `data/` as a
volume).

**RAG stack**: swapped ChromaDB/FAISS + embedding models for TF-IDF so
the whole thing runs with zero model downloads. To upgrade: replace
`core/rag.py`'s `TfidfVectorizer` with a `sentence-transformers` embedder
and store vectors in ChromaDB — the `retrieve(query, k)` function
signature stays identical, so nothing else in the codebase changes.

**LangGraph/CrewAI**: agents are called directly in sequence from
`app.py` rather than through a graph framework. This is functionally
equivalent for this linear workflow; introduce LangGraph if you later
want agents to dynamically decide which agent to call next (e.g., letting
the Planner Agent branch based on live interview performance mid-session).

## Project Structure

```
interviewgpt_pro/
├── app.py                    # Streamlit UI + orchestration
├── core/
│   ├── llm_client.py         # Shared Groq LLM wrapper (JSON + text calls)
│   ├── voice_client.py       # Speech-to-text via Groq Whisper
│   ├── code_executor.py      # Sandboxed Python code execution for DSA rounds
│   ├── memory.py             # SQLite long-term memory + leaderboard
│   └── rag.py                # TF-IDF knowledge base retrieval
├── agents/
│   ├── resume_agent.py       # Agent 1
│   ├── planner_agent.py      # Agent 2
│   ├── technical_agent.py    # Agent 3
│   ├── hr_agent.py           # Agent 4
│   ├── gap_agent.py          # Agent 7
│   └── coach_agent.py        # Agent 8
├── data/
│   ├── kb/                   # Sample knowledge base (DSA, system design,
│   │                           company patterns, behavioral framework)
│   └── db/                   # SQLite database (created on first run)
├── requirements.txt
└── .env.example
```

## Notes

- Every agent function is pure and testable in isolation (no hidden
  global state besides the shared Anthropic client) — you can call any
  `agents/*.py` function directly from a Python shell or a test suite.
- The knowledge base in `data/kb/` is a small starter set. Drop more
  `.md` files in there (interview experiences, company-specific
  question banks, your own notes) and they'll be automatically indexed
  on the next run.
# InterviewGPT
