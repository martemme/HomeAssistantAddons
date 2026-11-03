from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE = REPO_ROOT / "azure-pipelines.yml"


class MirrorPipelineContractTests(unittest.TestCase):
    def setUp(self):
        self.pipeline = PIPELINE.read_text(encoding="utf-8")

    def test_mirror_targets_the_homelab_self_hosted_pool(self):
        self.assertIn("pool:\n  name: Homelab\n", self.pipeline)
        self.assertNotIn("vmImage:", self.pipeline)

    def test_pipeline_uses_checked_github_remote_helper(self):
        self.assertIn("./ci/scripts/ensure_github_remote.sh", self.pipeline)
        self.assertNotIn("git remote add github", self.pipeline)

    def test_pipeline_runs_contract_check_before_mirroring(self):
        contract_step = self.pipeline.find("python3 -m unittest discover -s ci/tests -v")
        mirror_step = self.pipeline.find("displayName: Mirror ADO branches and tags")
        self.assertGreaterEqual(contract_step, 0, "missing mirror contract test step")
        self.assertGreaterEqual(mirror_step, 0, "missing mirror step")
        self.assertLess(contract_step, mirror_step)


if __name__ == "__main__":
    unittest.main()
