"""Ask a question about ingested annual reports, from the terminal.

Usage:
    python query.py --list
    python query.py NFLX_AR2025 "How many paid memberships does Netflix have?"
    python query.py CRM_AR2026 "What was total revenue?" --k 8
    python query.py NFLX_AR2025,CRM_AR2026 "Compare revenue growth"
    python query.py --deep "Is Micron's capex sustainable vs its cash flow, and how is the market pricing it?"
"""

import argparse
import sys

import rag


def main() -> None:
    parser = argparse.ArgumentParser(description="Query an ingested annual report.")
    parser.add_argument("report", nargs="?", help="Report name (see --list)")
    parser.add_argument("question", nargs="?", help="Your question, in quotes")
    parser.add_argument("--k", type=int, default=rag.DEFAULT_K,
                        help=f"Number of chunks to retrieve (default {rag.DEFAULT_K})")
    parser.add_argument("--list", action="store_true", help="List ingested reports")
    parser.add_argument("--deep", action="store_true",
                        help="Deep-analysis agent: decides its own searches across "
                             "reports and live quotes. Pass just the question, no report.")
    args = parser.parse_args()

    if args.deep:
        question = args.report  # single positional in --deep mode
        if not question:
            sys.exit('Usage: python query.py --deep "<question>"')
        import agent
        result = agent.deep_answer(question)
        print(result["answer"])
        print("\nTool calls:")
        for t in result["trace"]:
            print(f"  {t['tool']}({t['args']})")
        return

    if args.list or not (args.report and args.question):
        print("Ingested reports:")
        for name in rag.list_reports():
            print(f"  {name}")
        if not args.list:
            print('\nUsage: python query.py <report> "<question>"')
        return

    selected = [r.strip() for r in args.report.split(",") if r.strip()]
    known = rag.list_reports()
    for report in selected:
        if report not in known:
            sys.exit(f"Unknown report '{report}'. Run: python query.py --list")

    if len(selected) == 1:
        result = rag.answer(selected[0], args.question, k=args.k)
    else:
        result = rag.answer_multi(selected, args.question)

    print(result["answer"])
    print("\nSources (retrieved chunks):")
    for doc in result["chunks"]:
        snippet = " ".join(doc.page_content.split())[:90]
        source = doc.metadata["source"].removesuffix(".pdf")
        print(f"  {source} p. {doc.metadata['page']:>4}  {snippet}")


if __name__ == "__main__":
    main()
