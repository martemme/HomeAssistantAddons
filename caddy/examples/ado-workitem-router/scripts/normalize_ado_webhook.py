#!/usr/bin/env python3
"""Normalize Azure DevOps work-item Service Hook envelopes for Hermes routes."""

import json
import sys
from typing import Any


_ALLOWED_EVENTS = {"workitem.updated", "workitem.commented"}
_EXPECTED_PUBLISHER = "tfs"
_EXPECTED_RESOURCE_VERSION = "1.0"


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.isdecimal() and int(value) > 0:
        return int(value)
    return None


def normalize(payload: Any) -> dict[str, Any] | None:
    """Return a minimal, non-authoritative envelope or None for ignored input."""
    if not isinstance(payload, dict):
        return None
    event_type = payload.get("eventType")
    if (payload.get("publisherId") != _EXPECTED_PUBLISHER
            or event_type not in _ALLOWED_EVENTS
            or payload.get("resourceVersion") != _EXPECTED_RESOURCE_VERSION):
        return None

    resource = payload.get("resource")
    if not isinstance(resource, dict):
        return None

    if event_type == "workitem.commented":
        work_item = resource.get("workItem")
        candidates = [
            resource.get("workItemId"),
            work_item.get("id") if isinstance(work_item, dict) else None,
        ]
    else:
        candidates = [resource.get("workItemId"), resource.get("id")]
    work_item_id = next((value for item in candidates
                         if (value := _positive_int(item)) is not None), None)
    if work_item_id is None:
        return None

    containers = payload.get("resourceContainers")
    project = containers.get("project") if isinstance(containers, dict) else None
    project_id = project.get("id") if isinstance(project, dict) else None
    if project_id is not None and (not isinstance(project_id, str) or not project_id.strip()):
        return None

    envelope: dict[str, Any] = {
        "ado_event_type": event_type,
        "work_item_id": work_item_id,
    }
    if isinstance(project_id, str) and project_id.strip():
        envelope["project_id"] = project_id
    if event_type == "workitem.commented":
        comment = resource.get("comment")
        comment_id = _positive_int(comment.get("id")) if isinstance(comment, dict) else None
        if comment_id is not None:
            envelope["comment_id"] = comment_id
    return envelope


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        envelope = normalize(payload)
    except (json.JSONDecodeError, UnicodeDecodeError):
        envelope = None
    if envelope is None:
        sys.stdout.write("[SILENT]\n")
    else:
        sys.stdout.write(json.dumps(envelope, separators=(",", ":"), ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
