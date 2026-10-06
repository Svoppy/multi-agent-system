import argparse
import json
import sys

from .orchestrator import Orchestrator, write_jsonl


def main(argv=None):
    parser = argparse.ArgumentParser(description="Analyze a review using the Week 5 multi-agent prototype")
    parser.add_argument("--text", help="Review text to analyze")
    parser.add_argument("--domain", choices=["product", "electronics", "hotel", "movie", "restaurant", "mixed"])
    parser.add_argument("--json", action="store_true", help="Print result as JSON")
    parser.add_argument("--show-trace", action="store_true", help="Print inter-agent trace")
    parser.add_argument("--log-dir", help="Save call trace as JSONL in this folder")
    args = parser.parse_args(argv)
    review = args.text
    domain = args.domain
    if review is None:
        try:
            review = input("Review: ").strip()
            if domain is None:
                domain = input("Domain (product/electronics/hotel/movie/restaurant/mixed): ").strip() or "mixed"
        except (EOFError, KeyboardInterrupt):
            print("Input cancelled.", file=sys.stderr)
            return 2
    try:
        result, state = Orchestrator().run(review, domain or "mixed")
    except (ValueError, RuntimeError) as exc:
        print(f"Could not analyze review: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Review analysis ({domain or 'mixed'})")
        print(f"Sentiment: {result['sentiment']['label']} (score {result['sentiment']['score']}, confidence {result['sentiment']['confidence']})")
        print(f"Provenance cues: {result['provenance']['label']} (confidence {result['provenance']['confidence']})")
        print(f"Evidence check: {'passed' if result['evidence_review']['grounded'] else 'warning'}")
        workload = result["workload"]
        print(f"Workload: {workload['total_llm_tool_calls']} LLM/tool calls; max share {workload['max_share_percent']}% (limit 40%: {'pass' if workload['under_40_percent'] else 'review'})")
        print("Caveats: " + " ".join(result["caveats"]))
    if args.show_trace:
        for event in state.events:
            print(json.dumps(event, ensure_ascii=False))
    if args.log_dir:
        print(f"Trace saved to {write_jsonl(state, args.log_dir)}", file=sys.stderr)
    return 0
