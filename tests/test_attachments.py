import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.attachments import save_ai_attachment


class AttachmentTests(unittest.TestCase):
    def test_failed_replacement_preserves_existing_guidance(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch("utils.attachments.db_dir", temporary),
        ):
            destination = Path(save_ai_attachment(1, "../Essay?", "original"))
            self.assertEqual(destination.parent, Path(temporary) / "attachments")
            with patch("utils.attachments.os.replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    save_ai_attachment(1, "../Essay?", "replacement")
            self.assertEqual(destination.read_text(), "original")
            self.assertEqual(list(destination.parent.iterdir()), [destination])


if __name__ == "__main__":
    unittest.main()
