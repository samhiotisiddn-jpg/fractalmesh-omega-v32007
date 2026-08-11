#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from perf_tracker.cli import build_parser, handle_analyze, handle_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate DeepSeek V4 tracker outputs")
    parser.add_argument("--data", default="tracker/deepseek_v4_perf_tracker.json", help="Path to tracker JSON data")
    parser.add_argument("--stale-days", type=int, default=7, help="Age in days for stale blocked/in-progress items")
    parser.add_argument(
        "--fail-on-stale", action="store_true", help="Exit non-zero if stale blocked/in-progress items are found"
    )
    args = parser.parse_args()

    cli_parser = build_parser()
    analyze_defaults = cli_parser.parse_args(["analyze"])
    analyze_args = argparse.Namespace(
        **{
            **vars(analyze_defaults),
            "data": args.data,
        }
    )
    report_defaults = cli_parser.parse_args(["report"])
    report_args = argparse.Namespace(
        **{
            **vars(report_defaults),
            "data": args.data,
            "stale_days": args.stale_days,
            "fail_on_stale": args.fail_on_stale,
        }
    )
    analyze_code = handle_analyze(analyze_args)
    report_code = handle_report(report_args)
    return analyze_code or report_code


if __name__ == "__main__":
    raise SystemExit(main())
