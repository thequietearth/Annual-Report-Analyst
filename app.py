"""AI Financial Research Assistant — Streamlit UI.

Milestone 1: hello-world skeleton. RAG wiring arrives in later milestones.
"""

import streamlit as st

st.set_page_config(page_title="AI Financial Research Assistant", page_icon="📊")

st.title("📊 AI Financial Research Assistant")
st.caption("Ask questions about company annual reports in natural language.")

st.info(
    "Hello, world! This is the milestone-1 skeleton. "
    "Ingestion, retrieval, and answers arrive in the next milestones."
)
