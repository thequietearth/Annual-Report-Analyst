# FUTURE.md — clever options deferred, v2 ideas

Simple-vs-clever decisions where we took the simple path, plus everything
explicitly out of scope for v1.

## Deferred clever options (from v1 decisions)

- **Dependency pinning**: requirements.txt is unpinned during development for
  simplicity; pin exact versions at milestone 6 (polish) for reproducible
  deploys.

## Out of scope for v1 (per contract)

- Multi-document comparison queries
- Live market data / SGX / stock price integration
- Chat history or memory
- User uploads in the UI
- Fine-tuning, rerankers, hybrid search
- Fancy UI styling beyond Streamlit defaults
