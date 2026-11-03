from pathlib import Path
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "ci/scripts/ensure_github_remote.sh"
EXPECTED_URL = "git@github.com:martemme/HomeAssistantAddons.git"


class EnsureGithubRemoteTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(dir=REPO_ROOT)
        self.repo = Path(self.tempdir.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.repo)], check=True)

    def tearDown(self):
        self.tempdir.cleanup()

    def add_github_remote(self, url):
        subprocess.run(
            ["git", "remote", "add", "github", url],
            cwd=self.repo,
            check=True,
        )

    def run_helper(self):
        return subprocess.run(
            ["bash", str(HELPER)],
            cwd=self.repo,
            capture_output=True,
            text=True,
            timeout=5,
        )

    def remote_url(self):
        result = subprocess.run(
            ["git", "remote", "get-url", "github"],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def test_adds_missing_github_remote(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_url(), EXPECTED_URL)

    def test_reuses_existing_expected_github_remote(self):
        self.add_github_remote(EXPECTED_URL)
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_url(), EXPECTED_URL)

    def test_rejects_unexpected_existing_github_remote_without_changing_it(self):
        unexpected = "https://github.com/someone-else/other-repo.git"
        self.add_github_remote(unexpected)
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected", result.stderr.lower())
        self.assertEqual(self.remote_url(), unexpected)


if __name__ == "__main__":
    unittest.main()
