"""Shared RAG core: retrieval + answer generation.

Used by query.py (terminal CLI, milestone 3) and app.py (Streamlit UI,
milestone 4). Keeping this logic in one module means the CLI and UI can
never drift apart.
"""

import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

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
- If the excerpts do not contain the answer, say exactly that — never guess.
- Be concise: a direct answer first, brief supporting detail after."""

USER_PROMPT = """\
Report excerpts:

{context}

Question: {question}"""


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
    return Chroma(
        client=_client(),
        collection_name=report,
        embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
    )


def retrieve(report: str, question: str, k: int = DEFAULT_K) -> list[Document]:
    """Top-k most similar chunks for the question."""
    return get_store(report).similarity_search(question, k=k)


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
