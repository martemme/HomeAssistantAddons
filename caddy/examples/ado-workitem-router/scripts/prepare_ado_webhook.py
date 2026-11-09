#!/usr/bin/env python3
"""Prepare ADO webhook events with read-only authoritative context."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any

try:
    from normalize_ado_webhook import normalize
except ImportError:  # Tests/importers may load this file outside its script directory.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from normalize_ado_webhook import normalize


_PROJECT = "Homelab"
_KB_PATHS = (
    "/Homelab",
    "/Homelab/Governance/Procedure Operative",
    "/Homelab/Governance/Storico",
    "/Homelab/Infrastructure/Continuous Deployment/Governance-Azure-DevOps",
    "/Homelab/Infrastructure/Continuous Deployment/Stack-DevOps-Node-LLM",
    "/Homelab/Infrastructure/Network/Ingress",
)
_ITEM_FIELDS = ",".join((
    "System.Id", "System.TeamProject", "System.WorkItemType", "System.Title",
    "System.Description", "Microsoft.VSTS.Common.AcceptanceCriteria", "System.State",
    "System.AssignedTo", "System.AreaPath", "System.IterationPath",
))
_SECRET_LINE = re.compile(r"(?im)^.*\b(?:password|passwd|secret|token|api[_ -]?key|authorization|credential)\b.*$")
_SENSITIVE_TOKEN_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----", re.S),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}={0,2}\b", re.I),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"glpat-[A-Za-z0-9_-]{12,}\b", re.I),
    re.compile(r"\b[A-Za-z0-9_-]{40,}\b"),
)
_RELEVANT_KB = re.compile(r"ado|azure devops|webhook|hermes|governance|dry.?run|caddy|assignment|service hook", re.I)


class ContextUnavailable(RuntimeError):
    """Required knowledge-base or ADO read could not be completed."""


def _clean_text(value: Any, limit: int = 6000) -> str:
    text = str(value or "")
    text = _SECRET_LINE.sub("[sensitive line omitted]", text)
    for pattern in _SENSITIVE_TOKEN_PATTERNS:
        text = pattern.sub("[sensitive token omitted]", text)
    text = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)
    if len(text) > limit:
        text = text[:limit] + "\n[truncated]"
    return text


def _knowledge_excerpt(content: Any, limit: int = 3000) -> str:
    text = _clean_text(content, 100_000)
    lines = text.splitlines()
    selected: list[str] = []
    for index, line in enumerate(lines):
        if _RELEVANT_KB.search(line):
            for neighbor in lines[max(0, index - 1):min(len(lines), index + 2)]:
                if neighbor not in selected:
                    selected.append(neighbor)
    if not selected:
        selected = lines[:30]
    excerpt = "\n".join(selected)
    if len(excerpt) > limit:
        excerpt = excerpt[:limit] + "\n[relevant excerpt truncated]"
    return excerpt


def _identity_keys(identity: Any) -> set[str]:
    if not isinstance(identity, dict):
        return set()
    return {
        str(identity[key]).strip().casefold()
        for key in ("id", "descriptor")
        if isinstance(identity.get(key), str) and identity[key].strip()
    }


def _same_identity(left: Any, right: Any) -> bool:
    return bool(_identity_keys(left) & _identity_keys(right))


def _relation_ids(item: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    relations = item.get("relations", [])
    if relations is None:
        relations = []
    if not isinstance(relations, list):
        raise ContextUnavailable("ADO work-item relations unavailable")
    matches: list[dict[str, Any]] = []
    for relation in relations:
        if not isinstance(relation, dict):
            raise ContextUnavailable("ADO work-item relation is malformed")
        relation_kind = relation.get("rel")
        if not isinstance(relation_kind, str):
            raise ContextUnavailable("ADO work-item relation is malformed")
        if not relation_kind.startswith(kind):
            continue
        relation_url = relation.get("url")
        if not isinstance(relation_url, str):
            raise ContextUnavailable("ADO work-item relation is malformed")
        path = urllib.parse.urlsplit(relation_url).path.rstrip("/")
        path_parts = path.split("/")
        raw_id = path_parts[-1] if path_parts else ""
        if len(path_parts) < 2 or path_parts[-2].casefold() != "workitems" or not raw_id.isdecimal() or int(raw_id) <= 0:
            raise ContextUnavailable("ADO work-item relation is malformed")
        attributes = relation.get("attributes") or {}
        if not isinstance(attributes, dict):
            raise ContextUnavailable("ADO work-item relation is malformed")
        matches.append({"id": int(raw_id), "relation": relation_kind, "name": attributes.get("name")})
    return matches


def _item_summary(item: dict[str, Any]) -> dict[str, Any]:
    fields = item.get("fields")
    if not isinstance(fields, dict):
        raise ContextUnavailable("ADO work-item fields unavailable")
    assigned = fields.get("System.AssignedTo") or {}
    return {
        "id": item.get("id"),
        "type": _clean_text(fields.get("System.WorkItemType"), 120),
        "title": _clean_text(fields.get("System.Title"), 500),
        "state": _clean_text(fields.get("System.State"), 120),
        "description": _clean_text(fields.get("System.Description"), 4000),
        "acceptance_criteria": _clean_text(fields.get("Microsoft.VSTS.Common.AcceptanceCriteria"), 3000),
        "assigned_to": _clean_text(assigned.get("displayName") if isinstance(assigned, dict) else assigned, 200),
        "area": _clean_text(fields.get("System.AreaPath"), 300),
        "iteration": _clean_text(fields.get("System.IterationPath"), 300),
    }


def _related_summaries(client: Any, item: dict[str, Any], kind: str, *, ancestors: bool = False) -> list[dict[str, Any]]:
    first = _relation_ids(item, kind)
    if len(first) > 20:
        raise ContextUnavailable("ADO relation count exceeds safe limit")
    results: list[dict[str, Any]] = []
    seen: set[int] = set()
    queue = [(entry["id"], 0) for entry in first]
    while queue and len(results) < 40:
        item_id, depth = queue.pop(0)
        if item_id in seen:
            continue
        seen.add(item_id)
        related = client.get_item(item_id)
        if not isinstance(related, dict) or related.get("id") != item_id:
            raise ContextUnavailable("related ADO work item unavailable")
        related_fields = related.get("fields")
        if (not isinstance(related_fields, dict)
                or str(related_fields.get("System.TeamProject", "")).casefold() != _PROJECT.casefold()):
            raise ContextUnavailable("related ADO work item is outside Homelab or missing project metadata")
        summary = _item_summary(related)
        summary["relation"] = kind
        results.append(summary)
        if ancestors:
            parent_links = _relation_ids(related, kind)
            if depth >= 4 and parent_links:
                raise ContextUnavailable("ADO ancestry exceeds supported depth")
            if len(parent_links) > 10:
                raise ContextUnavailable("ADO relation count exceeds safe limit")
            queue.extend((entry["id"], depth + 1) for entry in parent_links)
    if any(item_id not in seen for item_id, _ in queue):
        raise ContextUnavailable("ADO relation result limit exceeded")
    return results


def prepare(payload: Any, client: Any) -> dict[str, Any] | None:
    """Return verified dry-run context, or None for malformed/stale/non-actionable events.

    ``client`` exposes ``read_kb``, ``project_id``, ``get_identity``, ``get_item``,
    ``get_comment`` and ``is_allowed_human_author``; tests use a deterministic fake.
    """
    envelope = normalize(payload)
    if envelope is None:
        return None

    # Knowledge-base reads deliberately precede every work-item/identity read.
    knowledge_base = client.read_kb(_PROJECT)
    if not knowledge_base:
        raise ContextUnavailable("knowledge base unavailable")

    project_id = client.project_id(_PROJECT)
    payload_project_id = envelope.get("project_id")
    if not project_id or (payload_project_id and str(payload_project_id).casefold() != str(project_id).casefold()):
        return None

    identity = client.get_identity()
    if not _identity_keys(identity):
        raise ContextUnavailable("authenticated ADO identity unavailable")

    item = client.get_item(envelope["work_item_id"])
    if not isinstance(item, dict) or item.get("id") != envelope["work_item_id"]:
        return None
    fields = item.get("fields") or {}
    if str(fields.get("System.TeamProject", "")).casefold() != _PROJECT.casefold():
        return None
    if not _same_identity(identity, fields.get("System.AssignedTo")):
        return None

    event_type = envelope["ado_event_type"]
    state = str(fields.get("System.State", ""))
    if event_type == "workitem.updated" and state not in {"New", "Active"}:
        return None
    if event_type == "workitem.commented" and state != "Active":
        return None

    trigger_comment = None
    if event_type == "workitem.commented":
        comment_id = envelope.get("comment_id")
        if comment_id is None:
            return None
        comment = client.get_comment(envelope["work_item_id"], comment_id)
        if not isinstance(comment, dict) or comment.get("id") != comment_id:
            return None
        author = comment.get("createdBy") or {}
        author_id = _identity_keys(author)
        if not author_id or _same_identity(identity, author):
            return None
        if "@hermes" not in str(comment.get("text", "")):
            return None
        if not client.is_allowed_human_author(author):
            return None
        trigger_comment = {
            "id": comment_id,
            "author_id": str(author.get("id") or author.get("descriptor") or ""),
            "author": _clean_text(author.get("displayName"), 200),
            "text": _clean_text(comment.get("text"), 2000),
        }

    parents = _related_summaries(client, item, "System.LinkTypes.Hierarchy-Reverse", ancestors=True)
    children = _related_summaries(client, item, "System.LinkTypes.Hierarchy-Forward")
    dependencies = _related_summaries(client, item, "System.LinkTypes.Dependency-")
    parent_ids = [entry["id"] for entry in parents]
    initial_message = " ".join([f"AB#{envelope['work_item_id']}", *(f"AB#{item_id}" for item_id in parent_ids)])

    prepared = {
        "run_mode": "DRY_RUN",
        "ado_event_type": event_type,
        "project_id": project_id,
        "work_item_id": envelope["work_item_id"],
        "initial_message": initial_message,
        "current_work_item": _item_summary(item),
        "parents": parents,
        "children": children,
        "dependencies": dependencies,
        "trigger_comment": trigger_comment,
        "knowledge_base": [
            {"path": _clean_text(page.get("path"), 300),
             "excerpt": _knowledge_excerpt(page.get("content"))}
            for page in knowledge_base if isinstance(page, dict)
        ],
        "decision": "candidate_for_read_only_assessment",
        "side_effects_allowed": False,
    }
    context_fields = (
        "run_mode", "ado_event_type", "project_id", "work_item_id", "initial_message",
        "current_work_item", "parents", "children", "dependencies", "trigger_comment",
        "knowledge_base", "decision", "side_effects_allowed",
    )
    prepared["agent_context"] = json.dumps(
        {key: prepared[key] for key in context_fields}, ensure_ascii=False, indent=2,
    )
    return prepared


class HomelabAdoClient:
    """Narrow GET-only reader for the Homelab project and its ADO wiki."""

    def __init__(self) -> None:
        home = Path(os.environ.get("HERMES_HOME", Path(__file__).resolve().parents[1])).resolve()
        helper_path = home / "skills" / "homelab-ops" / "scripts" / "homelab.py"
        spec = importlib.util.spec_from_file_location("homelab_ops_readonly", helper_path)
        if spec is None or spec.loader is None:
            raise ContextUnavailable("Homelab helper unavailable")
        self.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.helper)
        self.creds = self.helper.load_credentials()
        self.root, self.headers = self.helper.ado_config(self.creds)
        self.home = home

    def read_kb(self, project: str) -> list[dict[str, str]]:
        wikis = self.helper.ado_wikis(self.creds, project)
        wiki = next((entry for entry in wikis if entry.get("name") == "Homelab.wiki"), None)
        if not wiki:
            raise ContextUnavailable("Homelab wiki unavailable")
        pages: list[dict[str, str]] = []
        for page_path in _KB_PATHS:
            try:
                page = self.helper.ado_wiki_page(self.creds, project, wiki["id"], page_path)
            except RuntimeError as exc:
                if str(exc) == "HTTP 404":
                    continue
                raise ContextUnavailable("knowledge-base read failed") from None
            content = page.get("content") if isinstance(page, dict) else ""
            if content:
                pages.append({"path": page_path, "content": content})
        if not pages:
            raise ContextUnavailable("knowledge base has no readable pages")
        return pages

    def project_id(self, project: str) -> str | None:
        entry = next((value for value in self.helper.ado_projects(self.creds)
                      if str(value.get("name", "")).casefold() == project.casefold()), None)
        return str(entry.get("id")) if entry and entry.get("id") else None

    def get_identity(self) -> dict[str, Any]:
        data = self.helper.read_json(self.helper.query_url(
            self.root, "_apis/connectionData", {"connectOptions": 1, "api-version": "7.1-preview.1"}), self.headers)
        return data.get("authenticatedUser") or {}

    def get_item(self, item_id: int) -> dict[str, Any] | None:
        data = self.helper.read_json(self.helper.query_url(
            self.root, f"_apis/wit/workitems/{int(item_id)}",
            {"$expand": "relations", "api-version": self.helper.API_VERSION}), self.headers)
        return data if isinstance(data, dict) else None

    def get_comment(self, work_item_id: int, comment_id: int) -> dict[str, Any] | None:
        path = f"{self.helper.ado_project_path(_PROJECT)}/_apis/wit/workItems/{int(work_item_id)}/comments/{int(comment_id)}"
        data = self.helper.read_json(self.helper.query_url(
            self.root, path, {"api-version": "7.1-preview.4"}), self.headers)
        return data if isinstance(data, dict) else None

    def is_allowed_human_author(self, author: dict[str, Any]) -> bool:
        config_path = self.home / "ado-workitem-router.json"
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        allowed = config.get("human_commenter_descriptors", []) if isinstance(config, dict) else None
        if not isinstance(allowed, list) or any(not isinstance(value, str) for value in allowed):
            return False
        descriptor = author.get("descriptor") if isinstance(author, dict) else None
        return isinstance(descriptor, str) and descriptor in allowed


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if normalize(payload) is None:
            sys.stdout.write("[SILENT]\n")
            return 0
        result = prepare(payload, HomelabAdoClient())
    except (json.JSONDecodeError, UnicodeDecodeError):
        result = None
    except Exception:
        sys.stderr.write("ADO webhook context unavailable\n")
        return 1
    if result is None:
        sys.stdout.write("[SILENT]\n")
    else:
        sys.stdout.write(json.dumps(result, separators=(",", ":"), ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
