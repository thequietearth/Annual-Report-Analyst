"""Ask a question about an ingested annual report, from the terminal.

Usage:
    python query.py --list
    python query.py NFLX_AR2025 "How many paid memberships does Netflix have?"
    python query.py CRM_AR2026 "What was total revenue?" --k 8
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
    args = parser.parse_args()

    if args.list or not (args.report and args.question):
        print("Ingested reports:")
        for name in rag.list_reports():
            print(f"  {name}")
        if not args.list:
            print('\nUsage: python query.py <report> "<question>"')
        return

    if args.report not in rag.list_reports():
        sys.exit(f"Unknown report '{args.report}'. Run: python query.py --list")

    result = rag.answer(args.report, args.question, k=args.k)

    print(result["answer"])
    print("\nSources (retrieved chunks):")
    for doc in result["chunks"]:
        snippet = " ".join(doc.page_content.split())[:100]
        print(f"  p. {doc.metadata['page']:>4}  {snippet}")


if __name__ == "__main__":
    main()
