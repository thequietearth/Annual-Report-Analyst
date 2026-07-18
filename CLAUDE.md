# AI Financial Research Assistant

RAG tool for querying company annual reports in natural language. This project
has been scoped before and never shipped. **The #1 priority is FINISHING.**
Treat the scope below as a hard contract.

## Definition of DONE (v1 — nothing beyond this)

1. **Ingestion**: CLI script that takes a PDF annual report → extracts text →
   chunks it (start simple: ~800 tokens, 150 overlap) → embeds → stores in
   ChromaDB with metadata (source file, page number).
2. **Query**: retrieve top-k chunks for a question, generate an answer with an
   LLM, and cite page numbers in the response.
3. **UI**: single-page Streamlit app — pick from pre-ingested reports, ask a
   question, see answer + cited sources. No auth, no upload feature in v1
   (ingest via CLI).
4. **Evals**: `evals/questions.json` with 20 hand-written Q&A pairs from the
   actual reports (the user writes questions and gold answers themselves —
   scaffold the file and the runner, leave the content to them). A script that
   runs all 20, reports (a) retrieval hit-rate: did the gold page appear in
   top-k, and (b) answer grades via LLM-as-judge with a strict rubric. Output
   a simple markdown scorecard.
5. Deployed on **Streamlit Community Cloud** with 2–3 reports pre-ingested.
6. **README**: what it does, architecture diagram (mermaid), how to run, eval
   results table, screenshots.

## Stack (fixed — do not substitute)

Python 3.11+, LangChain, ChromaDB (persisted locally / bundled for deploy),
Streamlit, OpenAI API for embeddings + generation (key via `.env`, never
committed). Keep dependencies minimal — **no** agent frameworks, **no**
LlamaIndex, **no** docker, **no** vector DB services.

## Explicitly OUT of scope for v1 (refuse if asked; remind the user it's v2)

- Multi-document comparison queries
- Live market data / SGX / stock price integration
- Chat history or memory
- User uploads in the UI
- Fine-tuning, rerankers, hybrid search
- Fancy UI styling beyond Streamlit defaults

## Working style

- Ship in **vertical slices**: after each work session the app must RUN
  end-to-end, even if crudely.
- Milestone order:
  1. Skeleton + deployed hello-world
  2. Ingestion CLI
  3. Retrieval + answer in terminal
  4. Streamlit UI
  5. Eval harness
  6. README + polish
- After each milestone, tell the user exactly what to test manually before
  moving on.
- If a step has a simple option and a clever option, take the simple one and
  note the clever one in `FUTURE.md`.
- The user is a strong analyst but not a daily coder: explain non-obvious
  design decisions in 2–3 lines as they're made, so they can defend every
  choice in a technical interview.

## Environment & conventions

- Windows 11, PowerShell. Python 3.12 at
  `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`.
- Virtualenv at `.venv\` — activate with `.venv\Scripts\Activate.ps1`, or call
  `.venv\Scripts\python.exe` directly.
- Run the app: `.venv\Scripts\python.exe -m streamlit run app.py`
- `chroma_db/` **is committed** to git — it's how pre-ingested reports ship to
  Streamlit Community Cloud (the contract says bundle, no vector DB service).
- `data/reports/` (source PDFs) is **gitignored** — annual reports are large
  and only the embeddings need to ship.
- `.env` holds `OPENAI_API_KEY`; never committed. `.env.example` shows the
  shape. On Streamlit Cloud the key goes in app Secrets instead.
