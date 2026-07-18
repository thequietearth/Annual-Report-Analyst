"""Run the eval suite over evals/questions.json.

For every filled-in question:
  (a) retrieval hit-rate  - is at least one gold page among the top-k chunks?
  (b) answer grade        - LLM-as-judge compares the answer to the gold answer
                            under a strict rubric (CORRECT / PARTIAL / INCORRECT).

Writes evals/scorecard.md and prints a summary.

Usage:
    python evals/run_evals.py
"""

import json
import sys
from datetime import date
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

import rag  # noqa: E402  (needs sys.path set up first)
from langchain_openai import ChatOpenAI  # noqa: E402

QUESTIONS_FILE = PROJECT_DIR / "evals" / "questions.json"
SCORECARD_FILE = PROJECT_DIR / "evals" / "scorecard.md"
JUDGE_MODEL = "gpt-4.1"

JUDGE_PROMPT = """\
You are grading an AI assistant's answer about a company's annual report
against a gold answer written by a human analyst. Apply this rubric strictly:

- CORRECT: every material fact in the gold answer appears accurately in the
  assistant's answer. Numbers must match (rounding to the same precision as
  the gold answer is acceptable; wrong units, periods, or magnitudes are not).
  Extra detail is fine if it does not contradict the gold answer.
- PARTIAL: the assistant states some but not all material facts of the gold
  answer, and states nothing factually wrong.
- INCORRECT: any material fact is wrong or contradicts the gold answer, or the
  assistant provides an answer where the gold answer says the information is
  not disclosed, or the assistant declines to answer despite the gold answer
  containing the information.

Gold answer:
{gold}

Assistant's answer:
{answer}

Respond with ONLY this JSON, nothing else:
{{"grade": "CORRECT" | "PARTIAL" | "INCORRECT", "reason": "<one short sentence>"}}"""


def judge(gold: str, answer: str) -> dict:
    llm = ChatOpenAI(model=JUDGE_MODEL, temperature=0)
    raw = llm.invoke(JUDGE_PROMPT.format(gold=gold, answer=answer)).content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    try:
        verdict = json.loads(raw)
        assert verdict["grade"] in ("CORRECT", "PARTIAL", "INCORRECT")
        return verdict
    except (json.JSONDecodeError, KeyError, AssertionError):
        return {"grade": "JUDGE_ERROR", "reason": f"unparseable judge output: {raw[:80]}"}


def main() -> None:
    rag.require_api_key()
    data = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    filled = [q for q in data["questions"] if q["question"].strip()]
    if not filled:
        sys.exit("No questions filled in yet - edit evals/questions.json first.")

    known = set(rag.list_reports())
    rows = []
    for q in filled:
        if q["report"] not in known:
            sys.exit(f"Question {q['id']}: unknown report '{q['report']}' (see python query.py --list)")
        print(f"[{q['id']:>2}] {q['report']}: {q['question'][:60]}...")
        result = rag.answer(q["report"], q["question"])
        retrieved_pages = [doc.metadata["page"] for doc in result["chunks"]]
        hit = any(p in q["gold_pages"] for p in retrieved_pages)
        verdict = judge(q["gold_answer"], result["answer"])
        print(f"     hit@{rag.DEFAULT_K}: {'yes' if hit else 'NO'} | grade: {verdict['grade']}")
        rows.append({
            "id": q["id"],
            "report": q["report"],
            "question": q["question"],
            "hit": hit,
            "gold_pages": q["gold_pages"],
            "retrieved_pages": retrieved_pages,
            "grade": verdict["grade"],
            "reason": verdict["reason"],
        })

    n = len(rows)
    hits = sum(r["hit"] for r in rows)
    counts = {g: sum(r["grade"] == g for r in rows)
              for g in ("CORRECT", "PARTIAL", "INCORRECT", "JUDGE_ERROR")}

    lines = [
        "# Eval Scorecard",
        "",
        f"Generated: {date.today().isoformat()} | Answer model: `{rag.CHAT_MODEL}` | "
        f"Judge: `{JUDGE_MODEL}` | k = {rag.DEFAULT_K}",
        "",
        "## Summary",
        "",
        f"- Questions run: **{n}** of {len(data['questions'])}",
        f"- Retrieval hit-rate: **{hits}/{n}** ({hits / n:.0%})",
        f"- Answer grades: **{counts['CORRECT']} correct**, {counts['PARTIAL']} partial, "
        f"{counts['INCORRECT']} incorrect"
        + (f", {counts['JUDGE_ERROR']} judge errors" if counts["JUDGE_ERROR"] else ""),
        "",
        "## Per-question results",
        "",
        "| # | Report | Question | Hit | Gold p. | Retrieved p. | Grade | Judge note |",
        "|---|--------|----------|-----|---------|--------------|-------|------------|",
    ]
    for r in rows:
        pages = ", ".join(map(str, r["gold_pages"]))
        got = ", ".join(map(str, dict.fromkeys(r["retrieved_pages"])))
        q_text = r["question"].replace("|", "\\|")
        note = r["reason"].replace("|", "\\|")
        lines.append(
            f"| {r['id']} | {r['report']} | {q_text} | {'✅' if r['hit'] else '❌'} "
            f"| {pages} | {got} | {r['grade']} | {note} |"
        )
    SCORECARD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nScorecard written to {SCORECARD_FILE}")
    print(f"Hit-rate {hits}/{n} | correct {counts['CORRECT']} | "
          f"partial {counts['PARTIAL']} | incorrect {counts['INCORRECT']}")


if __name__ == "__main__":
    main()
