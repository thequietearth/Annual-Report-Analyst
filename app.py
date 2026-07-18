"""AI Financial Research Assistant — Streamlit UI.

Single page: pick a pre-ingested annual report, ask a question, get an
answer with page citations. All RAG logic lives in rag.py (shared with the
query.py CLI); this file is presentation only.
"""

import os

import streamlit as st

import rag

st.set_page_config(page_title="AI Financial Research Assistant", page_icon="📊")

# On Streamlit Community Cloud the API key comes from app Secrets; locally
# rag.py already loaded it from .env. Bridge Secrets -> env var if needed.
if not os.environ.get("OPENAI_API_KEY"):
    try:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass

st.title("📊 AI Financial Research Assistant")
st.caption(
    "Ask questions about company annual reports in natural language. "
    "Answers cite the PDF page they came from."
)

reports = rag.list_reports()
if not reports:
    st.error("No reports ingested yet. Run: python ingest.py data/reports/<file>.pdf")
    st.stop()

if not os.environ.get("OPENAI_API_KEY"):
    st.error(
        "OPENAI_API_KEY is not configured. Locally: put it in .env. "
        "On Streamlit Cloud: add it under App settings → Secrets."
    )
    st.stop()

report = st.selectbox("Annual report", reports)

with st.form("question_form"):
    question = st.text_input(
        "Your question",
        placeholder="e.g. How much did revenue grow, and what drove it?",
    )
    submitted = st.form_submit_button("Ask")

if submitted and question.strip():
    with st.spinner("Retrieving and answering..."):
        result = rag.answer(report, question.strip())

    st.markdown(result["answer"])

    st.subheader("Sources")
    st.caption(
        "Retrieved excerpts the answer is based on. Page numbers are "
        "physical PDF pages."
    )
    for doc in result["chunks"]:
        with st.expander(f"Page {doc.metadata['page']} — {doc.metadata['source']}"):
            st.text(doc.page_content)
elif submitted:
    st.warning("Type a question first.")
