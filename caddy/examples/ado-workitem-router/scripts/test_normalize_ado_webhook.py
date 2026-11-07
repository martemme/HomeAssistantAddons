import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT = SCRIPT_DIR / "normalize_ado_webhook.py"


def run_script(payload):
    with tempfile.TemporaryDirectory() as home:
        env = {**os.environ, "HERMES_HOME": home}
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )


class NormalizeAdoWebhookTests(unittest.TestCase):
    def test_normalizes_work_item_update_to_minimal_envelope(self):
        payload = {
            "publisherId": "tfs",
            "eventType": "workitem.updated",
            "resourceVersion": "1.0",
            "resource": {"id": 42, "fields": {"System.Title": "untrusted title"}},
            "resourceContainers": {"project": {"id": "project-guid"}},
        }

        result = run_script(payload)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "ado_event_type": "workitem.updated",
            "work_item_id": 42,
            "project_id": "project-guid",
        })
        self.assertNotIn("untrusted title", result.stdout)

    def test_normalizes_when_project_id_is_missing_for_authoritative_validation(self):
        payload = {
            "publisherId": "tfs",
            "eventType": "workitem.updated",
            "resourceVersion": "1.0",
            "resource": {"workItemId": 42},
        }

        result = run_script(payload)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "ado_event_type": "workitem.updated",
            "work_item_id": 42,
        })

    def test_prefers_work_item_id_over_update_revision_id(self):
        payload = {
            "publisherId": "tfs",
            "eventType": "workitem.updated",
            "resourceVersion": "1.0",
            "resource": {"id": 4, "workItemId": 42},
            "resourceContainers": {"project": {"id": "project-guid"}},
        }

        result = run_script(payload)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["work_item_id"], 42)

    def test_normalizes_comment_event_without_forwarding_comment_text(self):
        payload = {
            "publisherId": "tfs",
            "eventType": "workitem.commented",
            "resourceVersion": "1.0",
            "resource": {
                "id": 7,
                "workItemId": 42,
                "comment": {"id": 8, "text": "@hermes do something"},
            },
            "resourceContainers": {"project": {"id": "project-guid"}},
        }

        result = run_script(payload)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "ado_event_type": "workitem.commented",
            "work_item_id": 42,
            "project_id": "project-guid",
            "comment_id": 8,
        })
        self.assertNotIn("do something", result.stdout)

    def test_silences_comment_without_an_unambiguous_work_item_id(self):
        payload = {
            "publisherId": "tfs",
            "eventType": "workitem.commented",
            "resourceVersion": "1.0",
            "resource": {"id": 7, "comment": {"id": 8, "text": "@hermes"}},
            "resourceContainers": {"project": {"id": "project-guid"}},
        }

        result = run_script(payload)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[SILENT]")

    def test_silences_unknown_or_invalid_events(self):
        base = {
            "publisherId": "tfs",
            "eventType": "workitem.updated",
            "resourceVersion": "1.0",
            "resource": {"id": 42},
            "resourceContainers": {"project": {"id": "project-guid"}},
        }
        variants = [
            {**base, "eventType": "workitem.deleted"},
            {**base, "publisherId": "other"},
            {**base, "resourceVersion": "2.0"},
            {**base, "resource": {"id": 0}},
        ]

        for payload in variants:
            with self.subTest(payload=payload):
                result = run_script(payload)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "[SILENT]")


if __name__ == "__main__":
    unittest.main()
