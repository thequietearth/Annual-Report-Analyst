# FUTURE.md — clever options deferred, v2 ideas

Simple-vs-clever decisions where we took the simple path, plus everything
explicitly out of scope for v1.

## Deferred clever options (from v1 decisions)

- **Dependency pinning**: requirements.txt is unpinned during development for
  simplicity; pin exact versions at milestone 6 (polish) for reproducible
  deploys.
- **Per-page chunking** (milestone 2): chunks never span PDF pages, so every
  chunk has an exact page number for citations. Costs a little recall when a
  sentence crosses a page break. Clever option: structure-aware splitting that
  merges across pages and tracks page ranges.
- **Collection-per-report** (milestone 2): each report is its own ChromaDB
  collection — trivial report listing and isolation. Clever option: one
  collection with a `source` metadata filter, which would enable cross-report
  search (v2 multi-document comparison).
- **pypdf directly instead of LangChain's PyPDFLoader** (milestone 2): avoids
  the heavyweight `langchain-community` dependency; we build the per-page
  `Document` objects ourselves in ~10 lines.
- **No OCR fallback** (milestone 2): some publisher PDFs (e.g. Salesforce's
  EDGAR-filed ARS) have broken font encodings and extract as gibberish — we
  source clean PDFs instead. Clever option: detect gibberish at ingest time
  and OCR those pages (Tesseract) in v2.

## Findings from the first full eval run (2026-07-19, baseline)

Hit-rate 14/20, grades 8 CORRECT / 9 PARTIAL / 3 INCORRECT. Patterns worth
attacking in v2 (not tuned in v1 — the contract ships the honest baseline):

- **Retrieval misses cluster on financial-statement line items** (buybacks,
  capex, DRAM revenue): the question's wording is semantically closer to
  narrative/definitional pages than to the dense numeric tables that hold the
  answer. Classic embedding-retrieval weakness; v2 levers: larger k, hybrid
  (BM25 + dense) search, or table-aware chunking.
- **Most PARTIALs are omitted year-over-year context**: the answer states the
  right headline figure but not the prior-year comparison the gold answer
  includes. Lever: prompt the answerer to always include YoY context when the
  excerpts contain it.
- **One true miss becomes a false "not disclosed"** (Micron concentration):
  when retrieval fails entirely, the strict grounding prompt makes the model
  decline — honest, but graded INCORRECT because the report does disclose it.
  This is the designed failure mode: better a visible decline than a
  hallucination.

## Eval-driven improvement loop (branch `v3-portfolio`, 2026-09-07)

Applied the two cheapest levers named in the baseline findings above — hybrid
retrieval and a YoY prompt instruction — then re-ran the identical 20
questions. Reporting the real before/after, including where it didn't help:

| | Baseline (2026-07-19) | After hybrid + YoY (2026-09-07) |
|---|---|---|
| Retrieval hit-rate @ 5 | 14/20 (70%) | 15/20 (75%) |
| CORRECT | 8 | 9 |
| PARTIAL | 9 | 7 |
| INCORRECT | 3 | 4 |

**What actually moved, question by question** (`rag.py`, `_bm25_index` /
`retrieve`, and the YoY line in both system prompts):

- **The YoY prompt line worked as intended**, cleanly: two PARTIALs
  (Netflix net income, Micron net income) became CORRECT once the model was
  told to volunteer the prior-year figure. Free win, no retrieval change
  needed — this is a fix worth having by default.
- **BM25 recovered one retrieval miss** (Micron customer/end-market
  concentration, previously a false "not disclosed"), but the answer was
  still graded INCORRECT for an unrelated reading-comprehension slip
  (misattributed a 3-year figure to one year). Retrieval and generation are
  separate problems — fixing one doesn't guarantee the other.
- **Four retrieval misses were unmoved** (Netflix buybacks, Salesforce RPO,
  Micron DRAM revenue, Micron capex): BM25 term-matches on a word like "DRAM"
  or "capital expenditures" that appears on dozens of pages throughout a
  10-K, so it doesn't reliably surface the *one* page with the actual table.
  Keyword search alone isn't precise enough for financial-statement lookups;
  the next lever is table-aware chunking or a reranker over a wider
  candidate set, not more keyword matching.
- **One case got worse in a way worth naming**: the Informatica revenue
  question regressed from CORRECT to INCORRECT. The report legitimately
  contains two different Informatica revenue figures (total revenue
  contribution vs. subscription-only revenue), both already retrievable
  before this change; the added BM25 chunk didn't introduce the ambiguity but
  plausibly diluted the context enough to tip which figure the model
  foregrounded. **Lesson: unioning more context is not free** — bigger
  context windows can dilute attention even when nothing relevant was
  removed. Next lever: rerank the merged candidate set instead of
  concatenating dense ∪ keyword unfiltered.

Net effect: a modest, real improvement (+1 hit, +1 correct), not a clean win.
Both remaining levers (rerank instead of union; table-aware chunking) are
named, not built — consistent with shipping the honest number and scoping the
next cheapest experiment rather than tuning until the demo looks good.

## Deep-analysis agent (branch `v3-portfolio`, 2026-09-07)

`agent.py`: a plain function-calling loop (`ChatOpenAI.bind_tools` + a manual
loop, no LangGraph/AgentExecutor) with three tools - `search_report`,
`get_quote` (live market data via `market.py`), `list_available_reports` -
capped at 6 tool calls. For questions a single retrieval pass can't answer
well (cross-report comparisons entangled with live market context).

Two findings from testing it against the real tools, both fixed:

- **A real bug, not just an agent quirk**: an early test had the agent guess
  a plausible-but-wrong report name (`CRM_AR2023` instead of `CRM_AR2026`).
  `rag.get_store()` passed that name straight to LangChain's `Chroma`
  wrapper, which **silently auto-creates an empty collection for any name
  it's given** - so the typo permanently persisted a junk empty collection
  to `chroma_db/` (caught only because the *next* search against it raised
  "division by zero" from similarity search over zero documents). Fixed at
  the source: `get_store()` now checks the name against
  `list_collections()` first and raises a clear `ValueError` - this
  protects every caller (CLI, UI, agent), not just the new one. The agent's
  `search_report` tool also validates independently and returns the exact
  valid-report list in its error string, so a wrong guess is a one-step
  self-correction instead of a permanent side effect.
- **Model choice matters more for agentic orchestration than for one-shot
  answering**: with `gpt-4.1-mini` (the model used everywhere else in this
  app), the agent responded to that same wrong-name error by retrying the
  *same* wrong name with a *rephrased query*, twice, before eventually
  falling back to listing reports - burning 4 of 6 tool calls on a mistake
  the error message already corrected. Swapping only the agent's model to
  `gpt-4.1` fixed it: one wrong guess, immediate correction, done in 3-4
  calls. `rag.answer()` stays on `gpt-4.1-mini` (single-shot retrieval
  synthesis doesn't need this), so cost only goes up on the opt-in deep
  path - and it stayed low cents per call.

## Started in v2 (branch `v2-features`, 2026-07-19)

- **Multi-document comparison** — `rag.answer_multi()`: per-report retrieval
  (k=3 each) so every company is represented; citations become
  `[REPORT p. N]`; UI multiselect; CLI accepts comma-separated reports.
  Known gap: reports don't carry fiscal-year-end metadata, so the model can
  assume wrong year-ends when excerpts omit them (seen with Micron's August
  FYE). Fix candidate: store fiscal_year_end in collection metadata at ingest.
- **Live market data (minimal)** — `market.py`: yfinance (keyless) sidebar
  snapshot (last price, day change, 52-week range) for selected reports'
  tickers, 5-min cache, degrades silently offline. Deeper integration (SGX,
  historical charts, linking market data into answers) still open.

## Out of scope for v1 (per contract)

- ~~Multi-document comparison queries~~ → v2 branch
- ~~Live market data / stock price integration~~ → v2 branch (minimal)
- Chat history or memory
- User uploads in the UI
- Fine-tuning, rerankers, hybrid search
- Fancy UI styling beyond Streamlit defaults
