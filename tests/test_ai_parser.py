import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from utils.ai_parser import fallback_parse, parse_voice_command, to_title_case


class ParserTests(unittest.TestCase):
    def test_title_case_and_offline_priority_characterization(self):
        self.assertEqual(to_title_case("INTRODUCTION TO THE ARTS"), "Introduction to the Arts")
        parsed = fallback_parse("essay about climate change high priority", "task")
        self.assertEqual(parsed["name"], "Essay")
        self.assertEqual(parsed["priority"], "High")

    def test_malformed_model_fields_use_offline_parser(self):
        text = "essay about climate change"
        expected = fallback_parse(text, "task")
        for response in (
            {"name": None, "description": "text", "priority": "Medium"},
            {"name": "Essay", "description": [], "priority": "Medium"},
            {"name": "Essay", "description": "text", "priority": "urgent"},
            {
                "name": "Essay",
                "description": "text",
                "priority": "Medium",
                "deadline": "2026-02-30",
            },
            {"name": "Essay", "description": "text", "priority": "Medium", "time": "13:75 PM"},
        ):
            fake = SimpleNamespace(ChatCompletion=Mock(), models=SimpleNamespace(default="test"))
            fake.ChatCompletion.create.return_value = json.dumps(response)
            with self.subTest(response=response), patch.dict(sys.modules, {"g4f": fake}):
                with patch("socket.create_connection", return_value=MagicMock()):
                    self.assertEqual(parse_voice_command(text, "task"), expected)


if __name__ == "__main__":
    unittest.main()
