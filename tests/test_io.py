from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from perf_tracker.errors import ValidationError
from perf_tracker.io import load_tracker, resolve_repo_path, safe_write_text


class IOTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_rejects_relative_path_traversal(self) -> None:
        with self.assertRaises(ValidationError):
            resolve_repo_path("../outside.json", self.repo_root)

    def test_rejects_oversized_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "large.json"
            path.write_text('{"x": "' + ("a" * 1024) + '"}', encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_tracker(path, max_bytes=16)

    def test_rejects_json_bomb_depth(self) -> None:
        payload: object = {"v": 0}
        for _ in range(70):
            payload = {"nested": payload}

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "deep.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_tracker(path, max_depth=32)

    def test_rejects_non_dict_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "list.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_tracker(path)

    def test_safe_write_text_is_atomic_and_replaces_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "out.md"
            safe_write_text(target, "one\n")
            safe_write_text(target, "two\n")
            self.assertEqual(target.read_text(encoding="utf-8"), "two\n")


if __name__ == "__main__":
    unittest.main()
