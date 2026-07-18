"""Ingest a PDF annual report into ChromaDB.

Usage:
    python ingest.py data/reports/NFLX_AR2025.pdf
    python ingest.py data/reports/NFLX_AR2025.pdf --name NFLX_AR2025

Pipeline: extract text per page (pypdf) -> chunk (~800 tokens, 150 overlap)
-> embed (OpenAI text-embedding-3-small) -> store in chroma_db/ with
source-file and page-number metadata. Re-running replaces the report's
collection, so ingestion is safely repeatable.
"""

import argparse
import os
import re
import sys
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

CHROMA_DIR = "chroma_db"
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_TOKENS = 800
OVERLAP_TOKENS = 150
BATCH_SIZE = 100  # chunks per embedding request, keeps well under API token limits


def extract_pages(pdf_path: Path) -> list[Document]:
    """One Document per PDF page that has extractable text (1-based page numbers)."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(
                Document(
                    page_content=text,
                    metadata={"source": pdf_path.name, "page": i},
                )
            )
    return pages


def chunk_pages(pages: list[Document]) -> list[Document]:
    """Split pages into ~800-token chunks with 150-token overlap.

    Chunks never span pages, so every chunk keeps an exact page number for
    citations. Most annual-report pages fit in 1-2 chunks anyway.
    """
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=CHUNK_TOKENS,
        chunk_overlap=OVERLAP_TOKENS,
    )
    return splitter.split_documents(pages)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a PDF annual report into ChromaDB.")
    parser.add_argument("pdf", type=Path, help="Path to the PDF annual report")
    parser.add_argument("--name", help="Collection name (default: PDF filename without extension)")
    args = parser.parse_args()

    if not args.pdf.is_file():
        sys.exit(f"File not found: {args.pdf}")

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY not set. Copy .env.example to .env and add your key.")

    collection = args.name or args.pdf.stem
    collection = re.sub(r"[^a-zA-Z0-9_-]", "_", collection)

    print(f"Extracting text from {args.pdf.name} ...")
    pages = extract_pages(args.pdf)
    if not pages:
        sys.exit("No extractable text found (scanned/image-only PDF?).")
    print(f"  {len(pages)} pages with text")

    chunks = chunk_pages(pages)
    print(f"  {len(chunks)} chunks (~{CHUNK_TOKENS} tokens each, {OVERLAP_TOKENS} overlap)")

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(collection)
        print(f"  replaced existing collection '{collection}'")
    except Exception:
        pass  # collection didn't exist yet

    store = Chroma(
        client=client,
        collection_name=collection,
        embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
    )

    print(f"Embedding + storing into chroma_db/{collection} ...")
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        store.add_documents(batch)
        print(f"  {min(start + BATCH_SIZE, len(chunks))}/{len(chunks)}")

    print(f"Done: collection '{collection}' with {len(chunks)} chunks.")


if __name__ == "__main__":
    main()
