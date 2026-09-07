"""Deep-analysis agent: a plain function-calling loop over the same
retrieval and market data already used by the single-shot RAG path.

Deliberately built with ChatOpenAI.bind_tools() and a manual loop instead of
an agent framework (no LangGraph, no AgentExecutor) - the entire decision
loop is ~30 lines and fully visible, which is the point: this is what "an
AI worker that makes decisions and takes action" looks like at first
principles, not behind a framework's abstraction.

Use this for questions a single retrieval pass can't answer well - ones that
need several targeted lookups (possibly across reports) plus live market
context, e.g. "Is Micron's capex sustainable relative to its operating cash
flow, and how is the market pricing it?"
"""

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

import market
import rag

AGENT_MODEL = "gpt-4.1"  # stronger than the single-shot answerer (gpt-4.1-mini) -
# multi-step tool orchestration needs better self-correction than one-shot
# retrieval answering does. Tested: gpt-4.1-mini repeated a wrong report-name
# guess with a rephrased query instead of pivoting; gpt-4.1 corrected in one
# step. Deep analysis is opt-in and capped at MAX_STEPS, so the added cost
# per call (still low cents) doesn't touch the default single-shot path.
MAX_STEPS = 6

AGENT_SYSTEM_PROMPT = """\
You are a financial research analyst with tools to search annual reports and
check live stock quotes. Break the question into the specific lookups you
need, call tools to gather grounded facts, then synthesize a final answer.

Reports currently available to search (use these EXACT names - do not guess
a different year or format): {report_names}

Rules:
- Use search_report for every factual claim about a company's report - never
  answer about report contents from memory.
- Cite every report-derived claim inline, like [NFLX_AR2025 p. 12]. Never
  invent a citation for a claim that isn't a report page - a live quote from
  get_quote is stated plainly, with no bracketed citation, and clearly
  labeled as current market data (not from the report).
- get_quote is for live market data only (current price, day change, 52-week
  range) - never use it for anything a report would disclose.
- If a tool returns nothing useful, say so in the final answer rather than
  guessing.
- You have a limited number of tool calls: don't repeat an identical call,
  don't call get_quote for the same ticker twice, and stop calling tools
  once you have enough to answer well."""


@tool
def search_report(report: str, query: str) -> str:
    """Search one annual report for chunks relevant to a query. `report`
    must be an exact report name from list_available_reports (e.g.
    'NFLX_AR2025'). Returns the retrieved excerpts with page numbers."""
    known = rag.list_reports()
    if report not in known:
        # Hand back the valid list directly in the error - a model that
        # guessed wrong (e.g. a plausible-looking year) self-corrects on the
        # next call instead of repeating the same wrong guess with a
        # different query, which is what happened before this check existed.
        return f"'{report}' is not a valid report. Valid reports: {', '.join(known)}"
    try:
        chunks = rag.retrieve(report, query, k=4)
    except Exception as exc:
        return f"error searching {report}: {exc}"
    if not chunks:
        return f"no results in {report} for: {query}"
    return "\n\n".join(
        f"[{report} p. {c.metadata['page']}]\n{c.page_content}" for c in chunks
    )


@tool
def get_quote(ticker: str) -> str:
    """Get the current live stock price, today's percent change, and
    52-week range for a ticker (e.g. 'NFLX'). Independent of any annual
    report - use this only for current market data."""
    results = market.quotes([ticker])
    if not results:
        return f"no live quote available for {ticker}"
    q = results[0]
    parts = [f"{q['ticker']}: ${q['price']:,.2f}"]
    if q["change_pct"] is not None:
        parts.append(f"{q['change_pct']:+.1f}% today")
    if q["low_52w"] and q["high_52w"]:
        parts.append(f"52w range ${q['low_52w']:,.2f}-${q['high_52w']:,.2f}")
    return ", ".join(parts)


@tool
def list_available_reports() -> str:
    """List every annual report available to search."""
    return ", ".join(rag.list_reports())


TOOLS = [search_report, get_quote, list_available_reports]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}


def deep_answer(question: str) -> dict:
    """Run the tool-calling loop until the model stops calling tools (or
    MAX_STEPS is hit), then return the final answer plus a trace of every
    tool call made, in order - the UI renders the trace so you can watch
    the agent decide what to look up.

    Returns {"answer": str, "trace": list[dict]} where each trace entry is
    {"tool": name, "args": dict, "result": str}.
    """
    rag.require_api_key()
    system_prompt = AGENT_SYSTEM_PROMPT.format(report_names=", ".join(rag.list_reports()))
    llm = ChatOpenAI(model=AGENT_MODEL, temperature=0).bind_tools(TOOLS)
    messages = [SystemMessage(system_prompt), HumanMessage(question)]
    trace = []
    seen_calls: dict[tuple, str] = {}  # (tool, sorted args) -> result, to skip repeats

    for _ in range(MAX_STEPS):
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return {"answer": response.content, "trace": trace}

        for call in response.tool_calls:
            cache_key = (call["name"], tuple(sorted(call["args"].items())))
            if cache_key in seen_calls:
                result = seen_calls[cache_key]
            else:
                result = TOOLS_BY_NAME[call["name"]].invoke(call["args"])
                seen_calls[cache_key] = result
                trace.append({"tool": call["name"], "args": call["args"], "result": result})
            messages.append(ToolMessage(content=result, tool_call_id=call["id"]))

    # Ran out of steps: force a final answer from what's already gathered,
    # using a tool-free model call so it can't ask for yet another lookup.
    messages.append(HumanMessage(
        "You've reached the tool-call limit. Answer now using only what "
        "you've already found, and say clearly what you could not verify."
    ))
    final = ChatOpenAI(model=AGENT_MODEL, temperature=0).invoke(messages)
    return {"answer": final.content, "trace": trace}
