from datetime import datetime, timezone
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client


ATTENTION_STATUS_OPEN = "open"
ATTENTION_STATUS_ACKNOWLEDGED = "acknowledged"
ATTENTION_STATUS_RESOLVED = "resolved"



def _attention_document_id(approval_id: str) -> str:
    return f"HA-{approval_id}"



def create_human_attention(approval: dict[str, Any]) -> dict[str, Any]:
    """
    Create or reuse an in-app human-attention record for a pending approval.

    This is a notification/work-queue record. It does not approve or create
    follow-up actions and therefore does not bypass the Taskmaster boundary.
    """

    approval_id = str(approval.get("approval_id", "")).strip()

    if not approval_id:
        raise ValueError("approval_id is required to create human attention.")

    contractor_id = str(approval.get("contractor_id", "")).strip().upper()

    if not contractor_id:
        raise ValueError("contractor_id is required to create human attention.")

    db = get_firestore_client()
    reference = db.collection("human_attention").document(
        _attention_document_id(approval_id)
    )
    snapshot = reference.get()

    if snapshot.exists:
        existing = snapshot.to_dict() or {}
        return {
            "created": False,
            "duplicate": True,
            **existing,
        }

    proposed_actions = approval.get("proposed_actions", []) or []
    issues = approval.get("issues", []) or []

    recipient_roles = sorted(
        {
            str(action.get("owner", "H&S Practitioner")).strip()
            for action in proposed_actions
            if action.get("owner")
        }
    )

    if not recipient_roles:
        recipient_roles = ["H&S Practitioner"]

    now = datetime.now(timezone.utc).isoformat()

    record = {
        "attention_id": _attention_document_id(approval_id),
        "attention_type": "human_approval_required",
        "status": ATTENTION_STATUS_OPEN,
        "contractor_id": contractor_id,
        "contractor_name": approval.get("contractor_name"),
        "readiness_status": approval.get("readiness_status"),
        "risk_level": approval.get("risk_level"),
        "priority": "high",
        "recipient_roles": recipient_roles,
        "title": "Human attention required",
        "message": (
            "Consequential contractor-readiness actions are awaiting "
            "explicit human approval."
        ),
        "approval_id": approval_id,
        "issue_count": len(issues),
        "action_count": len(proposed_actions),
        "proposed_actions": proposed_actions,
        "created_at": now,
        "acknowledged_at": None,
        "resolved_at": None,
        "resolved_by": None,
    }

    reference.set(record)

    return {
        "created": True,
        "duplicate": False,
        **record,
    }



def list_open_human_attention(
    contractor_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return open/acknowledged human-attention records."""

    db = get_firestore_client()
    query = db.collection("human_attention")

    if contractor_id:
        query = query.where(
            filter=FieldFilter(
                "contractor_id",
                "==",
                contractor_id.strip().upper(),
            )
        )

    records: list[dict[str, Any]] = []

    for document in query.stream():
        record = document.to_dict() or {}
        if record.get("status") in {
            ATTENTION_STATUS_OPEN,
            ATTENTION_STATUS_ACKNOWLEDGED,
        }:
            records.append(record)

    records.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    return records



def resolve_human_attention(
    approval_id: str,
    resolved_by: str = "human_reviewer",
) -> dict[str, Any]:
    """Resolve all attention records associated with an approval ID."""

    approval_id = approval_id.strip()
    resolved_by = resolved_by.strip()

    if not approval_id:
        raise ValueError("approval_id is required.")

    db = get_firestore_client()

    query = db.collection("human_attention").where(
        filter=FieldFilter(
            "approval_id",
            "==",
            approval_id,
        )
    )

    resolved_count = 0
    resolved_at = datetime.now(timezone.utc).isoformat()

    for document in query.stream():
        document.reference.update(
            {
                "status": ATTENTION_STATUS_RESOLVED,
                "resolved_at": resolved_at,
                "resolved_by": resolved_by or "human_reviewer",
            }
        )
        resolved_count += 1

    return {
        "approval_id": approval_id,
        "resolved_count": resolved_count,
        "resolved_at": resolved_at,
        "status": ATTENTION_STATUS_RESOLVED,
    }
