"""One-click Executive Brief generator.

Runs a fixed battery of questions through rag.answer() - the same grounded,
cited single-report pipeline used everywhere else in this app - then one
synthesis call compiles the individual answers into a one-page brief. This
is the artifact you'd actually hand a VP after a discovery call: headline
metrics up top, every claim still carrying its [p. N] citation, plain prose,
no chat transcript.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import rag

BRIEF_MODEL = "gpt-4.1-mini"

QUESTIONS = [
    ("Revenue & growth",
     "What was total revenue and how much did it grow, and why?"),
    ("Profitability",
     "What was operating margin and net income, and how did they trend?"),
    ("Cash & capital returns",
     "How much cash did the company generate, and how much was returned "
     "to shareholders via dividends or buybacks?"),
    ("Key risks",
     "What are the most significant risks called out?"),
    ("Strategic priorities",
     "What are the company's stated strategic priorities or growth drivers?"),
    ("Notable events",
     "What were the most notable events or transactions during the "
     "period, such as acquisitions?"),
]

SYNTHESIS_SYSTEM_PROMPT = """\
You are compiling a one-page executive brief for a VP who has not read the
underlying annual report. You are given section drafts, each already
grounded in the report with [p. N] citations. Combine them into a single,
polished brief:

- Open with 3-4 headline metrics (revenue, growth, margin, net income) as a
  short bulleted list - the numbers a VP wants in the first five seconds.
- Then one short paragraph per section, in the given order, keeping every
  [p. N] citation exactly as given - never invent a new one and never drop
  one.
- If a section says information is not disclosed, keep that statement -
  never paper over a gap with outside knowledge.
- Tight, plain prose. No preamble - start directly with the headline
  metrics."""

SYNTHESIS_USER_PROMPT = """\
Report: {report}

Section drafts:

{sections}

Compile the executive brief."""


def generate(report: str, on_progress=None) -> str:
    """Run the fixed question battery, then synthesize one brief.

    on_progress(step, total_steps, label), if given, is called before each
    step runs - lets a caller show a progress bar.
    """
    rag.require_api_key()
    total_steps = len(QUESTIONS) + 1
    sections = []
    for i, (label, question) in enumerate(QUESTIONS, start=1):
        if on_progress:
            on_progress(i, total_steps, label)
        result = rag.answer(report, question)
        sections.append(f"## {label}\n{result['answer']}")

    if on_progress:
        on_progress(total_steps, total_steps, "Synthesizing brief")

    prompt = ChatPromptTemplate.from_messages(
        [("system", SYNTHESIS_SYSTEM_PROMPT), ("human", SYNTHESIS_USER_PROMPT)]
    )
    llm = ChatOpenAI(model=BRIEF_MODEL, temperature=0)
    message = (prompt | llm).invoke(
        {"report": report, "sections": "\n\n".join(sections)}
    )
    return message.content
