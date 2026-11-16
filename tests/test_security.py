import unittest
from unittest.mock import patch

from utils.security import decrypt_data, encrypt_data


class EncryptionTests(unittest.TestCase):
    def test_round_trip_and_randomized_ciphertext(self):
        with patch.dict("os.environ", {"ENCRYPTION_MASTER_SECRET": "test-only-master-secret"}):
            first = encrypt_data("student@example.test")
            second = encrypt_data("student@example.test")
            self.assertNotEqual(first, second)
            self.assertEqual(decrypt_data(first), "student@example.test")

    def test_encryption_failure_cannot_be_saved_as_empty_email(self):
        with patch("utils.security.get_aes_gcm", side_effect=ValueError("test failure")):
            with self.assertRaises(ValueError):
                encrypt_data("student@example.test")


if __name__ == "__main__":
    unittest.main()
