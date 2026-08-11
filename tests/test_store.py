from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from perf_tracker.store import get_document, init_db, list_documents, prune_old_documents, upsert_document


class StoreTests(unittest.TestCase):
    def test_init_and_upsert_and_get(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "tracker.db"
            init_db(db_path)
            upsert_document(
                db_path,
                doc_id="doc-1",
                source_issue="#1",
                source_title="Issue",
                data={"sections": []},
            )

            loaded = get_document(db_path, "doc-1")
            assert loaded is not None
            self.assertEqual(loaded["id"], "doc-1")
            self.assertEqual(loaded["data"], {"sections": []})

    def test_list_documents_and_prune(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "tracker.db"
            init_db(db_path)
            upsert_document(db_path, doc_id="new", source_issue="#2", source_title="New", data={"v": 2})
            upsert_document(db_path, doc_id="old", source_issue="#1", source_title="Old", data={"v": 1})

            with sqlite3.connect(db_path) as conn:
                conn.execute("UPDATE tracker_documents SET updated_at = ? WHERE id = ?", ("1900-01-01 00:00:00", "old"))
                conn.commit()

            listed = list_documents(db_path)
            self.assertEqual({row["id"] for row in listed}, {"new", "old"})

            deleted = prune_old_documents(db_path, days=30)
            self.assertEqual(deleted, 1)
            remaining = list_documents(db_path)
            self.assertEqual([row["id"] for row in remaining], ["new"])


if __name__ == "__main__":
    unittest.main()
