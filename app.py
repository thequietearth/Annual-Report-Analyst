"""AI Financial Research Assistant — Streamlit UI.

Single page: pick one or more pre-ingested annual reports, ask a question,
get an answer with citations. One report cites [p. N]; several reports cite
[REPORT p. N] and compare. All RAG logic lives in rag.py (shared with the
query.py CLI); this file is presentation only.
"""

import os

import streamlit as st

import market
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
    "Answers cite the PDF page they came from. Select several reports to compare."
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

selected = st.multiselect(
    "Annual report(s) — pick one, or several to compare",
    reports,
    default=reports[:1],
)

with st.sidebar:
    st.subheader("Market snapshot")
    st.caption("Live data via Yahoo Finance — independent of the reports.")
    quotes = market.quotes([market.ticker_for(r) for r in selected])
    if not quotes:
        st.caption("No market data available.")
    for q in quotes:
        delta = f"{q['change_pct']:+.1f}% today" if q["change_pct"] is not None else None
        st.metric(q["ticker"], f"${q['price']:,.2f}", delta)
        if q["low_52w"] and q["high_52w"]:
            st.caption(f"52-week range: ${q['low_52w']:,.2f} – ${q['high_52w']:,.2f}")

with st.form("question_form"):
    question = st.text_input(
        "Your question",
        placeholder="e.g. How much did revenue grow, and what drove it?",
    )
    submitted = st.form_submit_button("Ask")

if submitted and question.strip() and not selected:
    st.warning("Pick at least one report.")
elif submitted and question.strip():
    with st.spinner("Retrieving and answering..."):
        if len(selected) == 1:
            result = rag.answer(selected[0], question.strip())
        else:
            result = rag.answer_multi(selected, question.strip())

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
