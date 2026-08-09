#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from perf_tracker.cli import build_parser, handle_analyze, handle_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate DeepSeek V4 tracker outputs")
    parser.add_argument("--data", default="tracker/deepseek_v4_perf_tracker.json", help="Path to tracker JSON data")
    parser.add_argument("--stale-days", type=int, default=7, help="Age in days for stale blocked/in-progress items")
    parser.add_argument("--fail-on-stale", action="store_true", help="Exit non-zero if stale blocked/in-progress items are found")
    args = parser.parse_args()

    analyze_parser = build_parser()
    analyze_args = analyze_parser.parse_args(["--data", args.data, "analyze"])
    report_args = analyze_parser.parse_args(
        [
            "--data",
            args.data,
            "report",
            "--stale-days",
            str(args.stale_days),
            *( ["--fail-on-stale"] if args.fail_on_stale else [] ),
        ]
    )
    analyze_code = handle_analyze(analyze_args)
    report_code = handle_report(report_args)
    return analyze_code or report_code


if __name__ == "__main__":
    raise SystemExit(main())
