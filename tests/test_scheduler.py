import threading
import unittest
from unittest.mock import patch

from utils.notification_scheduler import NotificationScheduler


class SchedulerTests(unittest.TestCase):
    def test_restart_joins_previous_worker_before_changing_user(self):
        scheduler = NotificationScheduler()
        scheduler.stop()
        previous_finished = threading.Event()
        observed_users = []

        def run():
            user = scheduler._user_id
            while scheduler._running:
                previous_finished.wait(0.001)
            observed_users.append((user, scheduler._user_id))
            previous_finished.set()

        with patch.object(scheduler, "_run_loop", side_effect=run):
            scheduler.start(1, "first")
            previous = scheduler._thread
            scheduler.stop()
            self.assertFalse(previous.is_alive())
            self.assertTrue(previous_finished.is_set())
            scheduler.start(2, "second")
            scheduler.stop()
        self.assertEqual(observed_users, [(1, 1), (2, 2)])


if __name__ == "__main__":
    unittest.main()
