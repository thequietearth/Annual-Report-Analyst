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

## Out of scope for v1 (per contract)

- Multi-document comparison queries
- Live market data / SGX / stock price integration
- Chat history or memory
- User uploads in the UI
- Fine-tuning, rerankers, hybrid search
- Fancy UI styling beyond Streamlit defaults
