import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/release.sh"


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "commit", "--allow-empty", "-qm", "Fixture")
        self.git("tag", "v1.2.3")
        (self.repo / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [Unreleased]\n\nFuture changes\n\n"
            "## [1.2.3] - 2026-11-18\n\n### Fixed\n\n- Login works again.\n\n"
            "## [1.2.2]\n\n- Older change.\n\n[1.2.3]: https://example.com/compare\n")
        bin_dir = self.repo / "bin"
        bin_dir.mkdir()
        shutil.copy(ROOT / "tests/fake-gh", bin_dir / "gh")
        (bin_dir / "gh").chmod(0o755)
        self.state = self.repo / "remote.json"
        self.state.write_text("{}")
        self.output = self.repo / "output"
        self.output.touch()
        self.env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"],
                        GITHUB_WORKSPACE=str(self.repo), GITHUB_REPOSITORY="example/project",
                        GITHUB_REF="refs/tags/v1.2.3", GH_TOKEN="fixture-not-a-secret",
                        GITHUB_OUTPUT=str(self.output), FAKE_GH_STATE=str(self.state),
                        RELEASE_BODY_SOURCE="changelog", RELEASE_CHANGELOG_PATH="CHANGELOG.md",
                        RELEASE_TITLE="", RELEASE_ASSETS="")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True,
                              capture_output=True, text=True).stdout

    def run_action(self, **env):
        return subprocess.run(["bash", str(SCRIPT)], cwd=self.repo,
                              env=dict(self.env, **env), capture_output=True, text=True)

    def release(self):
        return json.loads(self.state.read_text()).get("release")

    def assert_failed(self, result, message):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(message, result.stdout + result.stderr)
        self.assertIsNone(self.release())

    def test_default_changelog_creates_release(self):
        result = self.run_action()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release()["name"], "Release v1.2.3")
        self.assertEqual(self.release()["body"].strip(), "### Fixed\n\n- Login works again.")
        self.assertIn("release-created=true", self.output.read_text())
        self.assertIn("release-url=https://github.com/", self.output.read_text())

    def test_custom_path_title_and_literal_assets(self):
        (self.repo / "docs").mkdir()
        (self.repo / "CHANGELOG.md").rename(self.repo / "docs/history.md")
        (self.repo / "my app.zip").write_text("binary fixture")
        (self.repo / "-checksum.txt").write_text("checksum fixture")
        title = 'Release $(touch INJECTED); "quoted"'
        result = self.run_action(RELEASE_CHANGELOG_PATH="docs/history.md", RELEASE_TITLE=title,
                                 RELEASE_ASSETS="my app.zip\r\n\n-checksum.txt\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release()["name"], title)
        self.assertEqual(self.release()["assets"], {"my app.zip": "binary fixture",
                                                     "-checksum.txt": "checksum fixture"})
        self.assertFalse((self.repo / "INJECTED").exists())

    def test_changelog_filename_is_a_literal_path(self):
        (self.repo / "CHANGELOG.md").rename(self.repo / "history=release.md")
        result = self.run_action(RELEASE_CHANGELOG_PATH="history=release.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release()["body"].strip(), "### Fixed\n\n- Login works again.")

    def test_annotated_tag_body_is_used_verbatim(self):
        message = "Release 1.2.3\n\nLogin works again. $(touch INJECTED)"
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "tag", "-fa", "v1.2.3", "-m", message)
        result = self.run_action(RELEASE_BODY_SOURCE="tag")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release()["body"].strip(), message)
        self.assertFalse((self.repo / "INJECTED").exists())

    def test_label_only_annotation_is_preserved(self):
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "tag", "-fa", "v1.2.3", "-m", "Release 1.2.3")
        result = self.run_action(RELEASE_BODY_SOURCE="tag")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release()["body"].strip(), "Release 1.2.3")

    def test_signed_tag_excludes_signature(self):
        commit = self.git("rev-parse", "HEAD").strip()
        for kind in ["PGP", "SSH"]:
            with self.subTest(kind=kind):
                self.state.write_text("{}")
                tag_object = (f"object {commit}\ntype commit\ntag v1.2.3\n"
                              "tagger Test <test@example.com> 1700000000 +0000\n\n"
                              f"Signed release body.\n-----BEGIN {kind} SIGNATURE-----\n"
                              f"signature fixture\n-----END {kind} SIGNATURE-----\n")
                oid = subprocess.run(["git", "hash-object", "-t", "tag", "-w", "--stdin"],
                                     input=tag_object, text=True, cwd=self.repo,
                                     check=True, capture_output=True).stdout.strip()
                self.git("update-ref", "refs/tags/v1.2.3", oid)
                result = self.run_action(RELEASE_BODY_SOURCE="tag")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.release()["body"].strip(), "Signed release body.")

    def test_tag_without_v_prefix(self):
        self.git("tag", "1.2.3")
        result = self.run_action(GITHUB_REF="refs/tags/1.2.3")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release()["name"], "Release 1.2.3")

    def test_rerun_does_not_upload_new_assets(self):
        first = self.run_action()
        self.assertEqual(first.returncode, 0, first.stderr)
        original = self.release()
        second = self.run_action(RELEASE_ASSETS="missing-on-rerun.zip")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.release(), original)

    def test_tag_with_slash_and_shell_characters_is_literal(self):
        tag = "package/v1.2.3;echo-injected"
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "tag", "-a", tag, "-m", "Package release")
        result = self.run_action(GITHUB_REF="refs/tags/" + tag, RELEASE_BODY_SOURCE="tag")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release()["tag_name"], tag)

    def test_lightweight_tag_does_not_use_commit_or_changelog(self):
        self.assert_failed(self.run_action(RELEASE_BODY_SOURCE="tag"), "annotated tag")

    def test_empty_annotation_fails(self):
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "tag", "-fa", "v1.2.3", "-m", "")
        self.assert_failed(self.run_action(RELEASE_BODY_SOURCE="tag"), "empty")

    def test_missing_changelog_fails_without_fallback(self):
        (self.repo / "CHANGELOG.md").unlink()
        self.assert_failed(self.run_action(), "changelog")

    def test_missing_version_and_empty_section_fail(self):
        for content in ["## [1.2.30]\nWrong version\n", "## [1.2.3]\n \t\n## [1.2.2]\nOld\n"]:
            with self.subTest(content=content):
                (self.repo / "CHANGELOG.md").write_text(content)
                self.assert_failed(self.run_action(), "empty")

    def test_final_section_excludes_reference_links(self):
        (self.repo / "CHANGELOG.md").write_text(
            "## [1.2.3]\n\nFirst release.\n\n[1.2.3]: https://example.com\n")
        result = self.run_action()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release()["body"].strip(), "First release.")

    def test_crlf_and_unbracketed_heading(self):
        (self.repo / "CHANGELOG.md").write_bytes(b"## 1.2.3 - 2026-11-18\r\n\r\nFixed.\r\n")
        result = self.run_action()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release()["body"].strip(), "Fixed.")

    def test_heading_in_fenced_code_does_not_end_section(self):
        body = "Example:\n\n```md\n## Sample heading\n```\n\nStill part of release."
        (self.repo / "CHANGELOG.md").write_text("## [1.2.3]\n\n" + body + "\n\n## [1.2.2]\nOld\n")
        result = self.run_action()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release()["body"].strip(), body)

    def test_existing_release_is_unchanged_even_without_notes(self):
        original = {"name": "Original", "body": "Keep this", "html_url": "https://example.com/release"}
        self.state.write_text(json.dumps({"release": original}))
        (self.repo / "CHANGELOG.md").unlink()
        result = self.run_action()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.release(), original)
        self.assertIn("release-created=false", self.output.read_text())

    def test_api_failures_do_not_attempt_creation(self):
        for status in [401, 403, 429, 500]:
            with self.subTest(status=status):
                self.state.write_text(json.dumps({"status": status}))
                self.assert_failed(self.run_action(), "check")

    def test_creation_failure_is_reported(self):
        self.state.write_text(json.dumps({"create_failure": True}))
        self.assert_failed(self.run_action(), "creation failed")

    def test_invalid_source_missing_asset_and_branch_ref_fail(self):
        for env, message in [({"RELEASE_BODY_SOURCE": "generated"}, "release-body-source"),
                             ({"RELEASE_ASSETS": "missing.zip"}, "asset"),
                             ({"RELEASE_ASSETS": "*.zip"}, "asset"),
                             ({"GITHUB_REF": "refs/heads/main"}, "tag"),
                             ({"GH_TOKEN": ""}, "GH_TOKEN")]:
            with self.subTest(env=env):
                self.assert_failed(self.run_action(**env), message)

    def test_missing_local_tag_and_wrong_checkout_fail(self):
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "commit", "--allow-empty", "-qm", "Another commit")
        self.assert_failed(self.run_action(), "checkout")
        self.assert_failed(self.run_action(GITHUB_REF="refs/tags/v9.9.9"), "tag")


if __name__ == "__main__":
    unittest.main()
