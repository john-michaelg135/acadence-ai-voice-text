import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from screens.tasks_view import EditTaskPopup


class TaskEditTests(unittest.TestCase):
    def test_regeneration_preserves_existing_attachment_until_replacement_is_ready(self):
        with tempfile.TemporaryDirectory() as temporary:
            attachment = Path(temporary) / "existing.txt"
            attachment.write_text("existing guidance", encoding="utf-8")
            screen = SimpleNamespace(
                name_entry=Mock(), deadline_entry=Mock(), hour_var=Mock(), min_var=Mock(),
                ampm_var=Mock(), desc_textbox=Mock(), priority_var=Mock(), submitted=False,
                db=Mock(), on_success=Mock(), withdraw=Mock(), update_idletasks=Mock(),
                grab_release=Mock(), master=Mock(), destroy=Mock(),
                task_data={"id": 1, "attachment_path": str(attachment)},
            )
            screen.name_entry.get.return_value = "Essay"
            screen.deadline_entry.get_date.return_value = date(2099, 1, 1)
            screen.hour_var.get.return_value = "12"
            screen.min_var.get.return_value = "00"
            screen.ampm_var.get.return_value = "PM"
            screen.desc_textbox.get.return_value = "Write an essay"
            screen.priority_var.get.return_value = "Medium"
            screen.master.winfo_exists.return_value = False
            with patch("utils.ai_parser._check_online", return_value=True), patch(
                "screens.tasks_view.messagebox.askyesno", return_value=True
            ):
                EditTaskPopup.submit(screen)
            self.assertTrue(attachment.exists())
            self.assertEqual(attachment.read_text(), "existing guidance")
            screen.db.update_task_attachment.assert_not_called()
            screen.on_success.assert_called_once()


if __name__ == "__main__":
    unittest.main()
