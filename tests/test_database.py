import sqlite3
import threading
import unittest
from pathlib import Path

from database.db_manager import DatabaseManager, configure_connection


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = object.__new__(DatabaseManager)
        self.db._db_lock = threading.RLock()
        self.db._conn = sqlite3.connect(":memory:")
        configure_connection(self.db._conn)
        self.db._conn.executescript(
            (Path(__file__).resolve().parents[1] / "database/schema.sql").read_text()
        )
        self.db._conn.execute(
            "INSERT INTO users (id, username, encrypted_password) VALUES (1, 'student', 'test')"
        )
        self.addCleanup(self.db._conn.close)

    def test_user_lookup_contract_and_bound_parameters(self):
        expected = self.db.get_user("student")
        self.assertEqual(self.db.get_user_by_username("student"), expected)
        self.assertIsNone(self.db.get_user("' OR 1=1 --"))

    def test_subject_task_lifecycle_and_metrics(self):
        self.db.add_subject(1, "Math", "M-101")
        subject = self.db.get_subjects(1)[0]
        task_id = self.db.add_task(subject["id"], "Essay", "Details", priority="High")
        self.assertEqual(self.db.get_dashboard_metrics(1)["high_priority_count"], 1)
        self.db.update_task_status(task_id, "completed")
        self.assertEqual(self.db.get_dashboard_metrics(1)["total_pending_tasks"], 0)
        self.assertIsNotNone(self.db.get_completed_tasks(1)[0]["completed_at"])
        self.db.update_task_status(task_id, "pending")
        self.assertEqual(self.db.get_completed_tasks(1), [])
        self.db.delete_subject(subject["id"])
        self.assertEqual(self.db.get_tasks(subject["id"]), [])


if __name__ == "__main__":
    unittest.main()
