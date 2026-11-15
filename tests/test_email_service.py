import unittest
from datetime import timedelta
from unittest.mock import patch

from utils import email_service


class RecoveryCodeTests(unittest.TestCase):
    def setUp(self):
        email_service._store.clear()
        email_service._resend_timestamps.clear()
        self.validation = patch.object(email_service, "_validate_email", return_value=None)
        self.validation.start()
        self.addCleanup(self.validation.stop)
        self.addCleanup(email_service._store.clear)
        self.addCleanup(email_service._resend_timestamps.clear)

    def test_resend_cooldown_prevents_replacing_valid_code(self):
        with patch.object(email_service, "_credentials", return_value=("test@example.test", "test-only")), patch.object(
            email_service.smtplib, "SMTP_SSL"
        ) as smtp:
            self.assertTrue(email_service.send_reset_otp("student@example.test")["ok"])
            first_code = email_service._store["student@example.test"]["code"]
            self.assertFalse(email_service.send_reset_otp("student@example.test")["ok"])
            self.assertEqual(email_service._store["student@example.test"]["code"], first_code)
            self.assertEqual(smtp.call_count, 1)

    def test_non_ascii_code_is_rejected_without_crashing(self):
        email_service._store["student@example.test"] = {
            "code": "123456", "attempts": 0, "verified": False,
            "expires_at": email_service._now() + timedelta(minutes=5),
        }
        self.assertFalse(email_service.verify("student@example.test", "\u00e912345")["ok"])


if __name__ == "__main__":
    unittest.main()
