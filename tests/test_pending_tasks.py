import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from screens.all_pending_tasks_view import AllPendingTasksView


class PendingTaskTests(unittest.TestCase):
    def test_all_pending_screen_does_not_silently_limit_tasks(self):
        tasks = [{"id": index} for index in range(201)]
        database = Mock()
        database.get_all_pending_tasks.side_effect = lambda user_id, limit=200: tasks if limit is None else tasks[:limit]
        view = SimpleNamespace(db=database, user_id=1, load_tasks=Mock())
        AllPendingTasksView._fetch_and_render(view)
        self.assertEqual(len(view._raw_tasks), 201)


if __name__ == "__main__":
    unittest.main()
