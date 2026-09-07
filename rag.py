"""Shared RAG core: retrieval + answer generation.

Used by query.py (terminal CLI, milestone 3) and app.py (Streamlit UI,
milestone 4). Keeping this logic in one module means the CLI and UI can
never drift apart.
"""

import os
import re
from functools import lru_cache
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from rank_bm25 import BM25Okapi

PROJECT_DIR = Path(__file__).parent
CHROMA_DIR = str(PROJECT_DIR / "chroma_db")
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"
DEFAULT_K = 5

load_dotenv(PROJECT_DIR / ".env")

SYSTEM_PROMPT = """\
You are a financial research assistant answering questions about a company's
annual report. Follow these rules strictly:

- Use ONLY the report excerpts provided. Do not use outside knowledge.
- Cite the page for every factual claim, inline, like [p. 12].
- Quote figures exactly as stated in the report (units, currency, fiscal year).
- If the excerpts include a prior-year or prior-period figure for the same
  metric, state it alongside the current figure for comparison, even if the
  question doesn't explicitly ask for it.
- If the excerpts do not contain the answer, say exactly that — never guess.
- Be concise: a direct answer first, brief supporting detail after."""

USER_PROMPT = """\
Report excerpts:

{context}

Question: {question}"""

MULTI_SYSTEM_PROMPT = """\
You are a financial research assistant comparing multiple companies' annual
reports. Follow these rules strictly:

- Use ONLY the report excerpts provided. Do not use outside knowledge.
- Cite the report and page for every factual claim, inline, like
  [NFLX_AR2025 p. 12].
- Quote figures exactly as stated in each report (units, currency, fiscal
  year). The companies may have DIFFERENT fiscal year ends — say so when it
  affects comparability.
- If the excerpts include a prior-year or prior-period figure for the same
  metric, state it alongside the current figure for comparison, even if the
  question doesn't explicitly ask for it.
- If an excerpt set does not contain a company's side of the answer, say
  exactly that for that company — never guess.
- Structure comparisons clearly: answer first, then per-company support."""


def require_api_key() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY not set. Copy .env.example to .env and add your key."
        )


def _client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=CHROMA_DIR)


def list_reports() -> list[str]:
    """Names of all ingested reports (one ChromaDB collection each)."""
    return sorted(c.name for c in _client().list_collections())


def get_store(report: str) -> Chroma:
    """Open an existing report's collection.

    Checks existence first: the underlying Chroma wrapper otherwise
    auto-creates an empty collection for any name it's given, which would
    silently persist a junk collection to chroma_db/ for a mistyped report
    name (found via the agent's search_report tool guessing a wrong report
    name during testing - see FUTURE.md).
    """
    client = _client()
    known = {c.name for c in client.list_collections()}
    if report not in known:
        raise ValueError(f"Unknown report '{report}'. Ingested reports: {sorted(known)}")
    return Chroma(
        client=client,
        collection_name=report,
        embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
    )


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@lru_cache(maxsize=None)
def _bm25_index(report: str) -> tuple[BM25Okapi, tuple[Document, ...]]:
    """Build a keyword index over every chunk in a report, once per process.

    chroma_db/ is read-only at query time (ingestion is a separate CLI step),
    so caching for the life of the process is safe - the eval run (milestone
    5) showed dense embeddings under-rank questions whose answer sits in a
    dense numeric table (e.g. "how much did Netflix repurchase in 2025?"
    retrieved narrative pages, missing the cash-flow statement). BM25 catches
    those because it matches on the exact terms in the question.
    """
    data = get_store(report).get(include=["documents", "metadatas"])
    docs = tuple(
        Document(page_content=text, metadata=meta)
        for text, meta in zip(data["documents"], data["metadatas"])
    )
    corpus = [_tokenize(d.page_content) for d in docs]
    return BM25Okapi(corpus), docs


def retrieve(report: str, question: str, k: int = DEFAULT_K) -> list[Document]:
    """Hybrid retrieval: dense top-k unioned with BM25 keyword top-(k//2).

    Dense embeddings and keyword search fail on different questions, so the
    union recovers hits either one would miss alone, at the cost of a bit
    more context per answer.
    """
    dense = get_store(report).similarity_search(question, k=k)

    bm25, docs = _bm25_index(report)
    scores = bm25.get_scores(_tokenize(question))
    bm25_k = max(1, k // 2)
    ranked = sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)
    keyword_hits = [docs[i] for i in ranked[:bm25_k] if scores[i] > 0]

    seen = set()
    merged = []
    for doc in dense + keyword_hits:
        key = (doc.metadata.get("source"), doc.metadata.get("page"), doc.page_content)
        if key not in seen:
            seen.add(key)
            merged.append(doc)
    return merged


def answer(report: str, question: str, k: int = DEFAULT_K) -> dict:
    """Retrieve top-k chunks and generate a cited answer.

    Returns {"answer": str, "chunks": list[Document]} so callers can show
    the sources that were actually used.
    """
    require_api_key()
    chunks = retrieve(report, question, k)
    context = "\n\n".join(
        f"[p. {doc.metadata['page']}]\n{doc.page_content}" for doc in chunks
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", USER_PROMPT)]
    )
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    message = (prompt | llm).invoke({"context": context, "question": question})
    return {"answer": message.content, "chunks": chunks}


def answer_multi(reports: list[str], question: str, k_per_report: int = 3) -> dict:
    """Compare across several reports: retrieve per report, answer with
    report+page citations.

    k_per_report is lower than single-report k so a 3-report comparison stays
    at <=9 chunks of context. Each report gets its own retrieval pass, which
    guarantees every company is represented even if one dominates the
    similarity scores.
    """
    require_api_key()
    chunks = []
    for report in reports:
        chunks.extend(retrieve(report, question, k_per_report))
    context = "\n\n".join(
        f"[{doc.metadata['source'].removesuffix('.pdf')} p. {doc.metadata['page']}]\n"
        f"{doc.page_content}"
        for doc in chunks
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", MULTI_SYSTEM_PROMPT), ("human", USER_PROMPT)]
    )
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    message = (prompt | llm).invoke({"context": context, "question": question})
    return {"answer": message.content, "chunks": chunks}
