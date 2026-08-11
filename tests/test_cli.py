from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from perf_tracker.cli import build_parser, handle_analyze, main
from perf_tracker.errors import ValidationError


class CLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.data = self.repo_root / "tracker" / "deepseek_v4_perf_tracker.json"

    def test_parse_data_after_subcommand(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["validate", "--data", str(self.data)])
        self.assertEqual(Path(args.data), self.data)

    def test_analyze_dry_run_does_not_write_outputs(self) -> None:
        parser = build_parser()
        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "priorities.json"
            md_out = Path(tmpdir) / "priorities.md"
            args = parser.parse_args(
                [
                    "analyze",
                    "--data",
                    str(self.data),
                    "--json-out",
                    str(json_out),
                    "--md-out",
                    str(md_out),
                    "--dry-run",
                ]
            )
            with redirect_stdout(io.StringIO()) as captured:
                code = handle_analyze(args)
            self.assertEqual(code, 0)
            self.assertIn("Dry run", captured.getvalue())
            self.assertFalse(json_out.exists())
            self.assertFalse(md_out.exists())

    def test_invalid_relative_output_path_is_rejected(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "analyze",
                "--data",
                str(self.data),
                "--json-out",
                "../outside.json",
                "--md-out",
                "docs/status/test.md",
            ]
        )
        with self.assertRaises(ValidationError):
            handle_analyze(args)

    def test_main_returns_error_on_invalid_path(self) -> None:
        with patch(
            "sys.argv",
            [
                "perf-tracker",
                "analyze",
                "--data",
                str(self.data),
                "--json-out",
                "../outside.json",
            ],
        ):
            with redirect_stderr(io.StringIO()) as captured:
                code = main()
        self.assertEqual(code, 2)
        self.assertIn("Path traversal", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
