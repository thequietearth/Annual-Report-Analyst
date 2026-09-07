"""AI Financial Research Assistant — Streamlit UI.

Single page: pick one or more pre-ingested annual reports, ask a question,
get an answer with citations. One report cites [p. N]; several reports cite
[REPORT p. N] and compare. All RAG logic lives in rag.py (shared with the
query.py CLI); this file is presentation only.
"""

import os

import streamlit as st

import agent
import market
import rag

st.set_page_config(
    page_title="AI Financial Research Assistant",
    page_icon="📊",
    layout="wide",
)

# On Streamlit Community Cloud the API key comes from app Secrets; locally
# rag.py already loaded it from .env. Bridge Secrets -> env var if needed.
if not os.environ.get("OPENAI_API_KEY"):
    try:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass

EXAMPLE_QUESTIONS = [
    "How much did revenue grow, and what drove it?",
    "How much was returned to shareholders?",
    "What are the biggest risks called out?",
    "Compare revenue growth across the selected reports",
]

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

main_col, side_col = st.columns([7, 3], gap="large")

with main_col:
    selected = st.multiselect(
        "Annual report(s) — pick one, or several to compare",
        reports,
        default=reports[:1],
    )

    with st.form("question_form"):
        question = st.text_input(
            "Your question",
            placeholder="Type your own question…",
        )
        example = st.pills(
            "…or try one of these",
            EXAMPLE_QUESTIONS,
            selection_mode="single",
        )
        deep = st.checkbox(
            "🔎 Deep analysis — let an agent decide its own searches across "
            "reports and live quotes, instead of a single retrieval pass",
        )
        submitted = st.form_submit_button("Ask", type="primary")

    asked = (question.strip() or example or "").strip()

    if submitted and asked and not selected and not deep:
        st.warning("Pick at least one report.")
    elif submitted and asked and deep:
        with st.spinner("Agent is deciding what to look up..."):
            result = agent.deep_answer(asked)

        with st.container(border=True):
            st.markdown(f"**{asked}**")
            st.markdown(result["answer"])

        st.subheader(f"Agent trace — {len(result['trace'])} tool call(s)")
        st.caption("What the agent looked up, in order, to reach this answer.")
        for i, t in enumerate(result["trace"], 1):
            with st.expander(f"{i}. {t['tool']}({t['args']})"):
                st.text(t["result"])
    elif submitted and asked:
        with st.spinner("Retrieving and answering..."):
            if len(selected) == 1:
                result = rag.answer(selected[0], asked)
            else:
                result = rag.answer_multi(selected, asked)

        with st.container(border=True):
            st.markdown(f"**{asked}**")
            st.markdown(result["answer"])

        st.subheader("Sources")
        st.caption(
            "Retrieved excerpts the answer is based on. Page numbers are "
            "physical PDF pages."
        )
        for doc in result["chunks"]:
            source = doc.metadata["source"].removesuffix(".pdf")
            with st.expander(f"p. {doc.metadata['page']} · {source}"):
                st.text(doc.page_content)
    elif submitted:
        st.warning("Type a question or pick an example first.")

with side_col:
    st.subheader("Market snapshot")
    st.caption("Live data via Yahoo Finance — independent of the reports.")
    quotes = market.quotes([market.ticker_for(r) for r in selected])
    if not quotes:
        st.caption("No market data available.")
    for q in quotes:
        with st.container(border=True):
            delta = (
                f"{q['change_pct']:+.1f}% today"
                if q["change_pct"] is not None
                else None
            )
            st.metric(q["ticker"], f"${q['price']:,.2f}", delta)
            if q["low_52w"] and q["high_52w"]:
                st.caption(
                    f"52-week range: ${q['low_52w']:,.2f} – ${q['high_52w']:,.2f}"
                )

    st.subheader("In the library")
    for name in reports:
        st.caption(f"📄 {name.replace('_', ' ')}")
