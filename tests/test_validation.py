from __future__ import annotations

import copy
import unittest
from pathlib import Path

from perf_tracker.io import load_tracker
from perf_tracker.validation import ValidationError, validate_document

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = REPO_ROOT / "tracker" / "deepseek_v4_perf_tracker.json"


class ValidationTests(unittest.TestCase):
    def test_repository_tracker_validates(self) -> None:
        document = load_tracker(DATA_FILE)
        items = validate_document(document)
        self.assertGreater(len(items), 0)

    def test_validation_rejects_unknown_blockers(self) -> None:
        document = load_tracker(DATA_FILE)
        broken = copy.deepcopy(document)
        broken["sections"][0]["items"][0]["blocked_by"] = ["missing-item"]
        with self.assertRaises(ValidationError):
            validate_document(broken)

    def test_validation_rejects_dependency_cycles(self) -> None:
        document = load_tracker(DATA_FILE)
        broken = copy.deepcopy(document)
        first = broken["sections"][0]["items"][0]
        second = broken["sections"][0]["items"][1]
        first["blocked_by"] = [second["id"]]
        second["blocked_by"] = [first["id"]]
        with self.assertRaises(ValidationError):
            validate_document(broken)


if __name__ == "__main__":
    unittest.main()
