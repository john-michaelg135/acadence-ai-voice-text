import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import prepare_release, release


class ReleaseGuardTests(unittest.TestCase):
    def test_prerelease_feed_never_uses_stable_channel(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            version = "0.1.0-rc.1"
            for target, extension in release.TARGETS.items():
                (root / f"Acadence-{version}-{target}.{extension}").write_bytes(b"test")
            with patch.object(release, "__version__", version):
                feed = release.write_feed(root, "owner/repo")
            data = json.loads(feed.read_text())
            self.assertEqual(feed.name, "updates-beta.json")
            self.assertEqual(data["channel"], "beta")
            self.assertTrue(all(f"/v{version}/" in asset["url"] for asset in data["assets"]))
            self.assertFalse((root / "updates-stable.json").exists())

    def test_mismatched_tag_is_rejected_before_git_or_publish(self):
        with patch.object(release, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "exactly match"):
                release.validate_tag("v999.0.0")
            run.assert_not_called()

    def test_missing_assets_never_create_release(self):
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.object(release, "ROOT", Path(directory)),
                patch.object(release, "validate_tag", return_value="commit"),
                patch.object(release.subprocess, "run") as publish,
            ):
                with self.assertRaises(FileNotFoundError):
                    release.publish("v" + release.__version__)
                publish.assert_not_called()

    def test_missing_changelog_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "CHANGELOG.md").write_text("## [Unreleased]\n")
            with patch.object(release, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "changelog"):
                    release.notes()

    def test_feature_requires_minor_version(self):
        with patch.object(prepare_release, "run", side_effect=["v1.2.3", "feat(ui): add view", ""]):
            version, _, _ = prepare_release.plan()
            self.assertEqual(version, "1.3.0")

    def test_breaking_change_below_one_uses_minor(self):
        with patch.object(
            prepare_release, "run", side_effect=["v0.2.3", "fix(api)!: remove field", ""]
        ):
            version, _, _ = prepare_release.plan()
            self.assertEqual(version, "0.3.0")
