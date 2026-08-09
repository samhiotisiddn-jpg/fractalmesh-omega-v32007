from __future__ import annotations

import argparse
import json
from pathlib import Path

from perf_tracker.io import load_tracker
from perf_tracker.prioritization import blocked_items_report, critical_path_candidates, quick_wins
from perf_tracker.reporting import generate_report, write_json, write_markdown
from perf_tracker.validation import summarize_statuses, validate_or_raise

DEFAULT_DATA = Path("tracker/deepseek_v4_perf_tracker.json")
DEFAULT_PRIORITY_JSON = Path("docs/status/priorities.json")
DEFAULT_PRIORITY_MD = Path("docs/status/priorities.md")
DEFAULT_REPORT_JSON = Path("docs/status/latest.json")
DEFAULT_REPORT_MD = Path("docs/status/latest.md")



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DeepSeek V4 perf tracker tooling")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="Path to tracker JSON data")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate tracker schema")
    validate_parser.set_defaults(command_handler=handle_validate)

    analyze_parser = subparsers.add_parser("analyze", help="Emit prioritization outputs")
    analyze_parser.add_argument("--json-out", default=str(DEFAULT_PRIORITY_JSON), help="Path for JSON prioritization output")
    analyze_parser.add_argument("--md-out", default=str(DEFAULT_PRIORITY_MD), help="Path for markdown prioritization output")
    analyze_parser.set_defaults(command_handler=handle_analyze)

    report_parser = subparsers.add_parser("report", help="Generate status report outputs")
    report_parser.add_argument("--json-out", default=str(DEFAULT_REPORT_JSON), help="Path for JSON report output")
    report_parser.add_argument("--md-out", default=str(DEFAULT_REPORT_MD), help="Path for markdown report output")
    report_parser.add_argument("--stale-days", default=7, type=int, help="Age in days for stale blocked/in-progress items")
    report_parser.add_argument("--fail-on-stale", action="store_true", help="Exit non-zero if stale blocked/in-progress items are found")
    report_parser.set_defaults(command_handler=handle_report)
    return parser



def _load_and_validate(data_path: str) -> list[dict[str, object]]:
    document = load_tracker(data_path)
    return validate_or_raise(document)



def handle_validate(args: argparse.Namespace) -> int:
    document = load_tracker(args.data)
    items = validate_or_raise(document)
    counts = summarize_statuses(document)
    print(f"Validated {len(items)} items from {args.data}")
    print(json.dumps(counts, indent=2))
    return 0



def handle_analyze(args: argparse.Namespace) -> int:
    items = _load_and_validate(args.data)
    payload = {
        "critical_path_candidates": critical_path_candidates(items),
        "quick_wins": quick_wins(items),
        "blocked_items": blocked_items_report(items),
    }
    write_json(args.json_out, payload)
    markdown_lines = [
        "# DeepSeek V4 Prioritization Outputs",
        "",
        "## Critical path candidates",
    ]
    for entry in payload["critical_path_candidates"]:
        markdown_lines.append(f"- `{entry['id']}` (score={entry['score']}, depth={entry['dependency_depth']}): {entry['title']}")
    markdown_lines.extend(["", "## Quick wins"])
    for entry in payload["quick_wins"]:
        markdown_lines.append(f"- `{entry['id']}` (score={entry['score']}, depth={entry['dependency_depth']}): {entry['title']}")
    markdown_lines.extend(["", "## Blocked items"])
    for entry in payload["blocked_items"]:
        blockers = ", ".join(entry["active_blockers"])
        markdown_lines.append(f"- `{entry['id']}` blocked by [{blockers}] — {entry['title']}")
    Path(args.md_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.md_out).write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    print(f"Wrote prioritization outputs to {args.json_out} and {args.md_out}")
    return 0



def handle_report(args: argparse.Namespace) -> int:
    items = _load_and_validate(args.data)
    report = generate_report(items, stale_days=args.stale_days)
    write_json(args.json_out, report)
    write_markdown(args.md_out, report)
    print(f"Wrote report outputs to {args.json_out} and {args.md_out}")
    if args.fail_on_stale and report["stale_items"]:
        print(f"Found {len(report['stale_items'])} stale items")
        return 1
    return 0



def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.command_handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
