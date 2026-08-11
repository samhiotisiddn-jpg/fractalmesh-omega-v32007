from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from perf_tracker.config import get_db_path, get_repo_root
from perf_tracker.errors import ValidationError
from perf_tracker.io import load_tracker, resolve_repo_path, safe_write_text
from perf_tracker.prioritization import blocked_items_report, critical_path_candidates, quick_wins
from perf_tracker.reporting import generate_report, write_json, write_markdown
from perf_tracker.store import init_db
from perf_tracker.validation import summarize_statuses, validate_document

DEFAULT_DATA = Path("tracker/deepseek_v4_perf_tracker.json")
DEFAULT_PRIORITY_JSON = Path("docs/status/priorities.json")
DEFAULT_PRIORITY_MD = Path("docs/status/priorities.md")
DEFAULT_REPORT_JSON = Path("docs/status/latest.json")
DEFAULT_REPORT_MD = Path("docs/status/latest.md")


def _add_data_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data", default=argparse.SUPPRESS, help="Path to tracker JSON data")


def _get_data_path(args: argparse.Namespace) -> Path:
    return resolve_repo_path(getattr(args, "data", str(DEFAULT_DATA)), get_repo_root())


def _get_output_path(path_value: str | Path) -> Path:
    return resolve_repo_path(path_value, get_repo_root())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DeepSeek V4 perf tracker tooling")
    _add_data_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate tracker schema")
    _add_data_argument(validate_parser)
    validate_parser.set_defaults(command_handler=handle_validate)

    analyze_parser = subparsers.add_parser("analyze", help="Emit prioritization outputs")
    _add_data_argument(analyze_parser)
    analyze_parser.add_argument(
        "--json-out", default=str(DEFAULT_PRIORITY_JSON), help="Path for JSON prioritization output"
    )
    analyze_parser.add_argument(
        "--md-out", default=str(DEFAULT_PRIORITY_MD), help="Path for markdown prioritization output"
    )
    analyze_parser.add_argument("--dry-run", action="store_true", help="Print output paths without writing files")
    analyze_parser.set_defaults(command_handler=handle_analyze)

    report_parser = subparsers.add_parser("report", help="Generate status report outputs")
    _add_data_argument(report_parser)
    report_parser.add_argument("--json-out", default=str(DEFAULT_REPORT_JSON), help="Path for JSON report output")
    report_parser.add_argument("--md-out", default=str(DEFAULT_REPORT_MD), help="Path for markdown report output")
    report_parser.add_argument(
        "--stale-days", default=7, type=int, help="Age in days for stale blocked/in-progress items"
    )
    report_parser.add_argument(
        "--fail-on-stale", action="store_true", help="Exit non-zero if stale blocked/in-progress items are found"
    )
    report_parser.add_argument("--dry-run", action="store_true", help="Print output paths without writing files")
    report_parser.set_defaults(command_handler=handle_report)

    migrate_parser = subparsers.add_parser("migrate", help="Initialize SQLite storage")
    migrate_parser.add_argument("--db-path", default=str(get_db_path()), help="SQLite database path")
    migrate_parser.set_defaults(command_handler=handle_migrate)

    return parser


def _load_and_validate(args: argparse.Namespace) -> list[dict[str, object]]:
    document = load_tracker(_get_data_path(args))
    return validate_document(document)


def handle_validate(args: argparse.Namespace) -> int:
    data_path = _get_data_path(args)
    document = load_tracker(data_path)
    items = validate_document(document)
    counts = summarize_statuses(document)
    print(f"Validated {len(items)} items from {data_path}")
    print(json.dumps(counts, indent=2))
    return 0


def handle_analyze(args: argparse.Namespace) -> int:
    items = _load_and_validate(args)
    json_out = _get_output_path(args.json_out)
    md_out = _get_output_path(args.md_out)
    payload = {
        "critical_path_candidates": critical_path_candidates(items),
        "quick_wins": quick_wins(items),
        "blocked_items": blocked_items_report(items),
    }

    markdown_lines = [
        "# DeepSeek V4 Prioritization Outputs",
        "",
        "## Critical path candidates",
    ]
    for entry in payload["critical_path_candidates"]:
        markdown_lines.append(
            f"- `{entry['id']}` (score={entry['score']}, depth={entry['dependency_depth']}): {entry['title']}"
        )
    markdown_lines.extend(["", "## Quick wins"])
    for entry in payload["quick_wins"]:
        markdown_lines.append(
            f"- `{entry['id']}` (score={entry['score']}, depth={entry['dependency_depth']}): {entry['title']}"
        )
    markdown_lines.extend(["", "## Blocked items"])
    for entry in payload["blocked_items"]:
        blockers = ", ".join(entry["active_blockers"])
        markdown_lines.append(f"- `{entry['id']}` blocked by [{blockers}] — {entry['title']}")

    if args.dry_run:
        print(f"Dry run: would write prioritization outputs to {json_out} and {md_out}")
        return 0

    write_json(json_out, payload)
    safe_write_text(md_out, "\n".join(markdown_lines) + "\n")
    print(f"Wrote prioritization outputs to {json_out} and {md_out}")
    return 0


def handle_report(args: argparse.Namespace) -> int:
    items = _load_and_validate(args)
    json_out = _get_output_path(args.json_out)
    md_out = _get_output_path(args.md_out)
    report = generate_report(items, stale_days=args.stale_days)

    if args.dry_run:
        print(f"Dry run: would write report outputs to {json_out} and {md_out}")
    else:
        write_json(json_out, report)
        write_markdown(md_out, report)
        print(f"Wrote report outputs to {json_out} and {md_out}")

    if args.fail_on_stale and report["stale_items"]:
        print(f"Found {len(report['stale_items'])} stale items")
        return 1
    return 0


def handle_migrate(args: argparse.Namespace) -> int:
    db_path = _get_output_path(args.db_path)
    init_db(db_path)
    print(f"Initialized SQLite database at {db_path}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.command_handler(args)
    except ValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
