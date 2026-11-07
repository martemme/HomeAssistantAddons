import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT = SCRIPT_DIR / "prepare_ado_webhook.py"
spec = importlib.util.spec_from_file_location("prepare_ado_webhook", SCRIPT)
prepare_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prepare_module
spec.loader.exec_module(prepare_module)


class FakeAdoClient:
    def __init__(self):
        self.calls = []
        self.project_id_value = "project-guid"
        self.identity = {"id": "hermes-id", "descriptor": "hermes-descriptor"}
        self.item = {
            "id": 42,
            "fields": {
                "System.TeamProject": "Homelab",
                "System.WorkItemType": "Task",
                "System.Title": "Live title",
                "System.Description": "Live description",
                "Microsoft.VSTS.Common.AcceptanceCriteria": "Live criteria",
                "System.State": "Active",
                "System.AssignedTo": {
                    "id": "hermes-id",
                    "descriptor": "hermes-descriptor",
                    "displayName": "Hermes Martin",
                },
            },
            "relations": [{
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": "https://dev.azure.com/org/Homelab/_apis/wit/workItems/17",
                "attributes": {"name": "Parent"},
            }],
        }
        self.parent = {
            "id": 17,
            "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "User Story", "System.Title": "Parent story"},
            "relations": [],
        }
        self.comment = {
            "id": 8,
            "workItemId": 42,
            "text": "@hermes please assess this task",
            "createdBy": {"id": "human-id", "descriptor": "human-descriptor", "displayName": "Martin"},
        }

    def read_kb(self, project):
        self.calls.append(("read_kb", project))
        return [{"path": "/Homelab/Governance/Procedure Operative", "content": "Dry-run governance"}]

    def project_id(self, project):
        self.calls.append(("project_id", project))
        return self.project_id_value

    def get_identity(self):
        self.calls.append(("get_identity",))
        return self.identity

    def get_item(self, item_id):
        self.calls.append(("get_item", item_id))
        return self.item if item_id == 42 else self.parent if item_id == 17 else None

    def get_comment(self, work_item_id, comment_id):
        self.calls.append(("get_comment", work_item_id, comment_id))
        return self.comment if (work_item_id, comment_id) == (42, 8) else None

    def is_allowed_human_author(self, author):
        return bool(author and author.get("id") == "human-id")


def ado_payload(event_type="workitem.updated", *, work_item_id=42, project_id="project-guid", comment_id=None):
    resource = {"workItemId": work_item_id}
    if event_type == "workitem.commented":
        resource["comment"] = {"id": comment_id if comment_id is not None else 8}
    return {
        "publisherId": "tfs",
        "eventType": event_type,
        "resourceVersion": "1.0",
        "resource": resource,
        "resourceContainers": {"project": {"id": project_id}},
    }


class PrepareAdoWebhookTests(unittest.TestCase):
    def test_reads_knowledge_base_before_any_authoritative_ado_data(self):
        client = FakeAdoClient()

        prepared = prepare_module.prepare(ado_payload(), client)

        self.assertIsNotNone(prepared)
        self.assertEqual(client.calls[0], ("read_kb", "Homelab"))
        self.assertLess(
            next(i for i, call in enumerate(client.calls) if call[0] == "read_kb"),
            next(i for i, call in enumerate(client.calls) if call[0] == "get_identity"),
        )

    def test_uses_live_ado_fields_and_hierarchy_not_payload_claims(self):
        client = FakeAdoClient()
        payload = ado_payload()
        payload["resource"].update({"fields": {"System.Title": "Forged title"}, "parentId": 999})

        prepared = prepare_module.prepare(payload, client)

        self.assertEqual(prepared["current_work_item"]["title"], "Live title")
        self.assertEqual(prepared["current_work_item"]["description"], "Live description")
        self.assertEqual(prepared["parents"][0]["id"], 17)
        self.assertTrue(prepared["initial_message"].startswith("AB#42 AB#17"))
        self.assertEqual(prepared["run_mode"], "DRY_RUN")

    def test_malformed_hierarchy_relation_fails_closed(self):
        client = FakeAdoClient()
        client.item["relations"][0]["url"] = "https://dev.azure.com/org/project/_apis/wit/workItems/not-an-id"

        with self.assertRaises(prepare_module.ContextUnavailable):
            prepare_module.prepare(ado_payload(), client)

    def test_unreadable_related_parent_fails_closed(self):
        client = FakeAdoClient()
        get_item = client.get_item
        client.get_item = lambda item_id: None if item_id == 17 else get_item(item_id)

        with self.assertRaises(prepare_module.ContextUnavailable):
            prepare_module.prepare(ado_payload(), client)

    def test_exactly_twenty_direct_relations_are_complete(self):
        client = FakeAdoClient()
        parent_ids = range(100, 120)
        client.item["relations"] = [{
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{item_id}",
            "attributes": {"name": "Parent"},
        } for item_id in parent_ids]
        items = {
            item_id: {"id": item_id, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "User Story", "System.Title": "Parent"}, "relations": []}
            for item_id in parent_ids
        }
        client.get_item = lambda item_id: client.item if item_id == 42 else items.get(item_id)

        prepared = prepare_module.prepare(ado_payload(), client)

        self.assertEqual(len(prepared["parents"]), 20)
        self.assertEqual({entry["id"] for entry in prepared["parents"]}, set(parent_ids))

    def test_too_many_direct_relations_fail_closed_before_partial_context(self):
        client = FakeAdoClient()
        client.item["relations"] = [
            {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{item_id}",
                "attributes": {"name": "Parent"},
            }
            for item_id in range(17, 38)
        ]

        with self.assertRaisesRegex(prepare_module.ContextUnavailable, "relation count exceeds"):
            prepare_module.prepare(ado_payload(), client)

    def test_exactly_ten_nested_ancestor_links_are_complete(self):
        client = FakeAdoClient()
        ancestor_links = [{
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{item_id}",
            "attributes": {"name": "Parent"},
        } for item_id in range(18, 28)]
        parent = {
            "id": 17,
            "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "User Story", "System.Title": "Parent story"},
            "relations": ancestor_links,
        }
        items = {
            item_id: {"id": item_id, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "Feature", "System.Title": "Ancestor"}, "relations": []}
            for item_id in range(18, 28)
        }
        items[17] = parent
        client.get_item = lambda item_id: client.item if item_id == 42 else items.get(item_id)

        prepared = prepare_module.prepare(ado_payload(), client)

        self.assertEqual(len(prepared["parents"]), 11)
        self.assertEqual({entry["id"] for entry in prepared["parents"]}, {17, *range(18, 28)})

    def test_too_many_nested_ancestor_links_fail_closed(self):
        client = FakeAdoClient()
        ancestor_links = [{
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{item_id}",
            "attributes": {"name": "Parent"},
        } for item_id in range(18, 29)]
        parent = {
            "id": 17,
            "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "User Story", "System.Title": "Parent story"},
            "relations": ancestor_links,
        }
        client.get_item = lambda item_id: client.item if item_id == 42 else parent if item_id == 17 else None

        with self.assertRaisesRegex(prepare_module.ContextUnavailable, "relation count exceeds"):
            prepare_module.prepare(ado_payload(), client)

    def test_immediate_parent_plus_four_ancestor_hops_are_complete(self):
        client = FakeAdoClient()
        client.item["relations"] = [{
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": "https://dev.azure.com/org/project/_apis/wit/workItems/17",
            "attributes": {"name": "Parent"},
        }]
        items = {
            item_id: {"id": item_id, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "Feature", "System.Title": "Ancestor"}, "relations": []}
            for item_id in range(17, 22)
        }
        items[17]["fields"]["System.WorkItemType"] = "User Story"
        for item_id in range(17, 21):
            items[item_id]["relations"] = [{
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{item_id + 1}",
                "attributes": {"name": "Parent"},
            }]
        client.get_item = lambda item_id: client.item if item_id == 42 else items.get(item_id)

        prepared = prepare_module.prepare(ado_payload(), client)

        self.assertEqual(len(prepared["parents"]), 5)
        self.assertEqual({entry["id"] for entry in prepared["parents"]}, set(range(17, 22)))

    def test_five_ancestor_hops_beyond_immediate_parent_fail_closed(self):
        client = FakeAdoClient()
        client.item["relations"] = [{
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": "https://dev.azure.com/org/project/_apis/wit/workItems/17",
            "attributes": {"name": "Parent"},
        }]
        items = {
            17: client.parent,
            18: {"id": 18, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "Feature", "System.Title": "Ancestor"}, "relations": []},
            19: {"id": 19, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "Epic", "System.Title": "Ancestor"}, "relations": []},
            20: {"id": 20, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "Epic", "System.Title": "Ancestor"}, "relations": []},
            21: {"id": 21, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "Epic", "System.Title": "Ancestor"}, "relations": []},
            22: {"id": 22, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "Epic", "System.Title": "Too deep"}, "relations": []},
        }
        for item_id, parent_id in ((17, 18), (18, 19), (19, 20), (20, 21), (21, 22)):
            items[item_id]["relations"] = [{
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{parent_id}",
                "attributes": {"name": "Parent"},
            }]
        client.get_item = lambda item_id: items.get(item_id) if item_id != 42 else client.item

        with self.assertRaisesRegex(prepare_module.ContextUnavailable, "ancestry exceeds"):
            prepare_module.prepare(ado_payload(), client)

    def test_exactly_forty_results_in_one_relation_group_are_complete(self):
        client = FakeAdoClient()
        parent_ids = range(100, 120)
        client.item["relations"] = [{
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{parent_id}",
            "attributes": {"name": "Parent"},
        } for parent_id in parent_ids]
        items = {}
        for parent_id in parent_ids:
            ancestor_id = parent_id + 100
            items[parent_id] = {
                "id": parent_id,
                "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "User Story", "System.Title": "Parent"},
                "relations": [{
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{ancestor_id}",
                    "attributes": {"name": "Parent"},
                }],
            }
            items[ancestor_id] = {"id": ancestor_id, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "Feature", "System.Title": "Ancestor"}, "relations": []}
        client.get_item = lambda item_id: client.item if item_id == 42 else items.get(item_id)

        prepared = prepare_module.prepare(ado_payload(), client)

        self.assertEqual(len(prepared["parents"]), 40)
        self.assertEqual({entry["id"] for entry in prepared["parents"]}, set(parent_ids) | set(range(200, 220)))

    def test_duplicate_queued_at_result_limit_is_not_an_overflow(self):
        client = FakeAdoClient()
        parent_ids = range(100, 120)
        client.item["relations"] = [{
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{parent_id}",
            "attributes": {"name": "Parent"},
        } for parent_id in parent_ids]
        items = {}
        for parent_id in parent_ids:
            ancestor_id = parent_id + 100
            ancestor_links = [ancestor_id]
            if parent_id == 119:
                ancestor_links.append(100)
            items[parent_id] = {
                "id": parent_id,
                "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "User Story", "System.Title": "Parent"},
                "relations": [{
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{item_id}",
                    "attributes": {"name": "Parent"},
                } for item_id in ancestor_links],
            }
            items[ancestor_id] = {
                "id": ancestor_id,
                "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "Feature", "System.Title": "Ancestor"},
                "relations": [],
            }
        client.get_item = lambda item_id: client.item if item_id == 42 else items.get(item_id)

        prepared = prepare_module.prepare(ado_payload(), client)

        self.assertEqual(len(prepared["parents"]), 40)

    def test_result_limit_is_per_relation_group_not_aggregate(self):
        client = FakeAdoClient()
        groups = {
            "System.LinkTypes.Hierarchy-Reverse": range(100, 120),
            "System.LinkTypes.Hierarchy-Forward": range(200, 220),
            "System.LinkTypes.Dependency-Forward": range(300, 320),
        }
        client.item["relations"] = [
            {
                "rel": relation_type,
                "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{item_id}",
                "attributes": {"name": relation_type.rsplit("-", 1)[-1]},
            }
            for relation_type, item_ids in groups.items()
            for item_id in item_ids
        ]
        items = {
            item_id: {"id": item_id, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "User Story", "System.Title": "Related"}, "relations": []}
            for item_ids in groups.values()
            for item_id in item_ids
        }
        client.get_item = lambda item_id: client.item if item_id == 42 else items.get(item_id)

        prepared = prepare_module.prepare(ado_payload(), client)

        self.assertEqual(len(prepared["parents"]), 20)
        self.assertEqual(len(prepared["children"]), 20)
        self.assertEqual(len(prepared["dependencies"]), 20)
        self.assertEqual(sum(map(len, (prepared["parents"], prepared["children"], prepared["dependencies"]))), 60)

    def test_more_than_result_limit_fails_closed(self):
        client = FakeAdoClient()
        parent_ids = range(100, 120)
        client.item["relations"] = [{
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{parent_id}",
            "attributes": {"name": "Parent"},
        } for parent_id in parent_ids]
        items = {}
        for parent_id in parent_ids:
            items[parent_id] = {
                "id": parent_id,
                "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "User Story", "System.Title": "Parent"},
                "relations": [{
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": f"https://dev.azure.com/org/project/_apis/wit/workItems/{ancestor_id}",
                    "attributes": {"name": "Parent"},
                } for ancestor_id in (
                    [200 + (parent_id - 100)] + ([220] if parent_id == 100 else [])
                )],
            }
        for ancestor_id in range(200, 221):
            items[ancestor_id] = {"id": ancestor_id, "fields": {"System.TeamProject": "Homelab", "System.WorkItemType": "Feature", "System.Title": "Ancestor"}, "relations": []}
        client.get_item = lambda item_id: items.get(item_id) if item_id != 42 else client.item

        with self.assertRaisesRegex(prepare_module.ContextUnavailable, "result limit"):
            prepare_module.prepare(ado_payload(), client)

    def test_assignment_event_is_ignored_when_live_assignee_is_not_caller(self):
        client = FakeAdoClient()
        client.item["fields"]["System.AssignedTo"] = {"id": "someone-else", "displayName": "Hermes Martin"}

        self.assertIsNone(prepare_module.prepare(ado_payload(), client))

    def test_terminal_assignment_event_is_ignored(self):
        client = FakeAdoClient()
        client.item["fields"]["System.State"] = "Closed"

        self.assertIsNone(prepare_module.prepare(ado_payload(), client))

    def test_comment_event_requires_live_human_marker_and_active_assignment(self):
        client = FakeAdoClient()

        prepared = prepare_module.prepare(ado_payload("workitem.commented"), client)

        self.assertIsNotNone(prepared)
        self.assertEqual(prepared["trigger_comment"]["id"], 8)
        self.assertEqual(prepared["trigger_comment"]["text"], "@hermes please assess this task")
        self.assertEqual(prepared["trigger_comment"]["author_id"], "human-id")

    def test_self_authored_comment_is_ignored(self):
        client = FakeAdoClient()
        client.comment["createdBy"] = client.identity

        self.assertIsNone(prepare_module.prepare(ado_payload("workitem.commented"), client))

    def test_comment_without_marker_or_approved_human_author_is_ignored(self):
        client = FakeAdoClient()
        client.comment["text"] = "ordinary comment"

        self.assertIsNone(prepare_module.prepare(ado_payload("workitem.commented"), client))

        client = FakeAdoClient()
        client.comment["createdBy"]["id"] = "unknown-automation"
        self.assertIsNone(prepare_module.prepare(ado_payload("workitem.commented"), client))

    def test_commenter_allowlist_requires_a_list_and_exact_membership(self):
        client = prepare_module.HomelabAdoClient.__new__(prepare_module.HomelabAdoClient)
        author = {"descriptor": "human-descriptor"}
        with tempfile.TemporaryDirectory() as home:
            client.home = Path(home)
            config_path = Path(home) / "ado-workitem-router.json"
            config_path.write_text(json.dumps({
                "human_commenter_descriptors": "prefix-human-descriptor-suffix",
            }), encoding="utf-8")
            self.assertFalse(client.is_allowed_human_author(author))

            for partial_descriptor in (
                "prefix-human-descriptor",
                "human-descriptor-suffix",
                "prefix-human-descriptor-suffix",
            ):
                config_path.write_text(json.dumps({
                    "human_commenter_descriptors": [partial_descriptor],
                }), encoding="utf-8")
                self.assertFalse(client.is_allowed_human_author(author))

            config_path.write_text(json.dumps({
                "human_commenter_descriptors": ["human-descriptor"],
            }), encoding="utf-8")
            self.assertTrue(client.is_allowed_human_author(author))

    def test_missing_payload_project_id_is_checked_against_live_item(self):
        client = FakeAdoClient()
        payload = ado_payload()
        payload["resourceContainers"]["project"].pop("id")

        prepared = prepare_module.prepare(payload, client)

        self.assertIsNotNone(prepared)
        client.item["fields"]["System.TeamProject"] = "Other"
        self.assertIsNone(prepare_module.prepare(payload, client))

    def test_related_items_must_belong_to_homelab(self):
        client = FakeAdoClient()
        allowed = prepare_module.prepare(ado_payload(), client)
        self.assertEqual(allowed["parents"][0]["title"], "Parent story")

        client = FakeAdoClient()
        client.parent["fields"]["System.TeamProject"] = "Other"
        client.parent["fields"]["System.Title"] = "Cross-project private title"
        with self.assertRaises(prepare_module.ContextUnavailable):
            prepare_module.prepare(ado_payload(), client)

        client = FakeAdoClient()
        client.parent["fields"].pop("System.TeamProject")
        with self.assertRaises(prepare_module.ContextUnavailable):
            prepare_module.prepare(ado_payload(), client)

    def test_project_mismatch_is_ignored(self):
        client = FakeAdoClient()

        self.assertIsNone(prepare_module.prepare(ado_payload(project_id="other-project"), client))

    def test_missing_knowledge_base_fails_closed_before_ado_reads(self):
        client = FakeAdoClient()
        client.read_kb = lambda project: []

        with self.assertRaises(prepare_module.ContextUnavailable):
            prepare_module.prepare(ado_payload(), client)
        self.assertFalse(any(call[0] == "get_item" for call in client.calls))

    def test_clean_text_redacts_short_unlabelled_gitlab_pat_tokens(self):
        token = "glpat-" + "d" * 24
        embedded_mixed_case = "contextGLPAT-" + "e" * 24 + ".suffix"

        cleaned = prepare_module._clean_text("untrusted note " + token + " " + embedded_mixed_case)

        self.assertNotIn(token, cleaned)
        self.assertNotIn("GLPAT-" + "e" * 24, cleaned)
        self.assertIn("[sensitive token omitted]", cleaned)

    def test_clean_text_redacts_unlabelled_tokens_and_private_key_blocks(self):
        unlabelled = "A" * 48 + "9" * 8
        bearer = "Bearer " + "b" * 48
        github_token = "ghp_" + "c" * 28
        private_key = (
            "-----BEGIN OPENSSH PRIVATE KEY-----\n"
            "ZmFrZS1ub3QtYS1yZWFsLWtleQ==\n"
            "-----END OPENSSH PRIVATE KEY-----"
        )
        self.assertIn("-----BEGIN OPENSSH PRIVATE KEY-----", private_key)
        self.assertIn("ZmFrZS1ub3QtYS1yZWFsLWtleQ==", private_key)
        self.assertIn("-----END OPENSSH PRIVATE KEY-----", private_key)
        text = "AB#42 note\n" + unlabelled + "\n" + bearer + "\n" + github_token + "\n" + private_key

        cleaned = prepare_module._clean_text(text)

        for token in (unlabelled, "b" * 48, github_token, "ZmFrZS1ub3QtYS1yZWFsLWtleQ=="):
            self.assertNotIn(token, cleaned)
        self.assertNotIn("-----BEGIN OPENSSH PRIVATE KEY-----", cleaned)
        self.assertNotIn("-----END OPENSSH PRIVATE KEY-----", cleaned)
        self.assertIn("AB#42 note", cleaned)
        self.assertIn("[sensitive token omitted]", cleaned)

    def test_main_silences_unknown_event_without_loading_profile_credentials(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HERMES_HOME": home}
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=json.dumps(ado_payload("workitem.deleted")),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[SILENT]")

    def test_unknown_event_is_silent_without_any_reads(self):
        client = FakeAdoClient()

        self.assertIsNone(prepare_module.prepare(ado_payload("workitem.deleted"), client))
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()
