from __future__ import annotations

import unittest

from perf_tracker.prioritization import blocked_items_report, critical_path_candidates, quick_wins
from perf_tracker.reporting import generate_report


class PrioritizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.items = [
            {
                "id": "base-kernel",
                "title": "Base kernel",
                "upstream_ref": "#1",
                "section": "Attention",
                "status": "todo",
                "priority": "p0",
                "impact": "high",
                "risk": "medium",
                "blocked_by": [],
                "updated_at": "2026-08-01T00:00:00Z",
            },
            {
                "id": "dependent-optimization",
                "title": "Dependent optimization",
                "upstream_ref": "#2",
                "section": "Attention",
                "status": "todo",
                "priority": "p0",
                "impact": "high",
                "risk": "low",
                "blocked_by": ["base-kernel"],
                "updated_at": "2026-08-01T00:00:00Z",
            },
            {
                "id": "quick-win",
                "title": "Quick win",
                "upstream_ref": "#3",
                "section": "Indexer",
                "status": "in_progress",
                "priority": "p1",
                "impact": "high",
                "risk": "low",
                "blocked_by": [],
                "updated_at": "2026-07-01T00:00:00Z",
            },
        ]

    def test_critical_path_prefers_longer_active_chain(self) -> None:
        ranked = critical_path_candidates(self.items)
        self.assertEqual(ranked[0]["id"], "dependent-optimization")
        self.assertEqual(ranked[0]["blocked_chain"], ["dependent-optimization", "base-kernel"])

    def test_quick_wins_filters_to_high_impact_low_risk_low_depth(self) -> None:
        wins = quick_wins(self.items)
        self.assertEqual([entry["id"] for entry in wins], ["dependent-optimization", "quick-win"])

    def test_blocked_report_lists_items_with_active_blockers(self) -> None:
        blocked = blocked_items_report(self.items)
        self.assertEqual(blocked[0]["id"], "dependent-optimization")
        self.assertEqual(blocked[0]["active_blockers"], ["base-kernel"])

    def test_report_includes_stale_in_progress_items(self) -> None:
        report = generate_report(self.items, stale_days=7)
        self.assertEqual(report["stale_items"][0]["id"], "quick-win")


if __name__ == "__main__":
    unittest.main()
