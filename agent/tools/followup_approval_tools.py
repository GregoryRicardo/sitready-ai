from datetime import datetime, timezone
import hashlib
import json

from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client
from agent.tools.followup_action_tools import create_followup_action
from agent.tools.human_attention_tools import create_human_attention, resolve_human_attention
from agent.tools.readiness_tools import assess_contractor_readiness


DEFAULT_DOCUMENT_DUE_DATE = "2026-08-30"
DEFAULT_SITE_DUE_DATE = "2026-08-26"

APPROVAL_STATUS_PENDING = "pending"
APPROVAL_STATUS_APPROVED = "approved"
APPROVAL_STATUS_CANCELLED = "cancelled"

VALID_APPROVAL_STATUSES = {
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_CANCELLED,
}


def _build_proposed_action(issue: dict) -> dict:
    """Convert a readiness issue into a deterministic proposed follow-up action."""
    issue_type = issue["issue_type"]

    if issue_type in {"expired_document", "missing_document", "missing_training"}:
        owner = "H&S Practitioner"
        due_date = DEFAULT_DOCUMENT_DUE_DATE
    elif issue_type in {"failed_inspection", "overdue_corrective_action"}:
        owner = "Site Manager"
        due_date = DEFAULT_SITE_DUE_DATE
    else:
        owner = "H&S Practitioner"
        due_date = DEFAULT_DOCUMENT_DUE_DATE

    return {
        "issue_type": issue_type,
        "issue_reference": issue["issue_reference"],
        "description": issue["description"],
        "priority": "high",
        "owner": owner,
        "due_date": due_date,
    }


def _normalize_proposed_actions(proposed_actions: list[dict]) -> list[dict]:
    """Normalize proposed actions so identical proposals have identical fingerprints."""
    normalized = []

    for action in proposed_actions:
        normalized.append(
            {
                "issue_type": str(action["issue_type"]).strip().lower(),
                "issue_reference": str(action["issue_reference"]).strip(),
                "description": str(action["description"]).strip(),
                "priority": str(action["priority"]).strip().lower(),
                "owner": str(action["owner"]).strip(),
                "due_date": str(action["due_date"]).strip(),
            }
        )

    normalized.sort(key=lambda action: (action["issue_type"], action["issue_reference"]))
    return normalized


def _build_approval_fingerprint(contractor_id: str, proposed_actions: list[dict]) -> str:
    """Create a deterministic SHA-256 fingerprint for a proposed action set."""
    payload = {
        "contractor_id": contractor_id,
        "proposed_actions": _normalize_proposed_actions(proposed_actions),
    }

    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _find_existing_pending_approval(contractor_id: str, approval_fingerprint: str) -> dict | None:
    """Find an existing pending approval for the same contractor and action set."""
    db = get_firestore_client()

    query = (
        db.collection("followup_approvals")
        .where(filter=FieldFilter("contractor_id", "==", contractor_id))
        .stream()
    )

    for document in query:
        existing = document.to_dict()
        if (
            existing.get("status") == APPROVAL_STATUS_PENDING
            and existing.get("approval_fingerprint") == approval_fingerprint
        ):
            return {"approval_id": document.id, **existing}

    return None


def propose_followup_actions(contractor_id: str) -> dict:
    """Assess readiness and prepare follow-up actions for human approval."""
    if not contractor_id or not contractor_id.strip():
        raise ValueError("contractor_id is required.")

    contractor_id = contractor_id.strip().upper()
    assessment = assess_contractor_readiness(contractor_id)

    proposed_actions = [_build_proposed_action(issue) for issue in assessment["issues"]]
    normalized_actions = _normalize_proposed_actions(proposed_actions)
    approval_fingerprint = _build_approval_fingerprint(contractor_id, normalized_actions)

    existing_pending = _find_existing_pending_approval(contractor_id, approval_fingerprint)

    if existing_pending:
        approval = {
            "created": False,
            "duplicate": True,
            "approval_id": existing_pending["approval_id"],
            "status": existing_pending["status"],
            "contractor_id": existing_pending["contractor_id"],
            "contractor_name": existing_pending["contractor_name"],
            "readiness_status": existing_pending["readiness_status"],
            "risk_level": existing_pending["risk_level"],
            "issues": existing_pending.get("issues", []),
            "proposed_actions": existing_pending["proposed_actions"],
            "created_at": existing_pending.get("created_at"),
            "message": (
                "An identical pending approval already exists. "
                "No duplicate approval was created."
            ),
        }
        if approval["status"] == APPROVAL_STATUS_PENDING:
            attention = create_human_attention(approval)
            approval["human_attention"] = attention
        return approval

    db = get_firestore_client()
    now = datetime.now(timezone.utc)
    created_at = now.isoformat()
    approval_id = f"APR-{now.strftime('%Y%m%d%H%M%S%f')}"

    approval_record = {
        "approval_id": approval_id,
        "contractor_id": assessment["contractor_id"],
        "contractor_name": assessment["contractor_name"],
        "readiness_status": assessment["readiness_status"],
        "risk_level": assessment["risk_level"],
        "issues": assessment["issues"],
        "proposed_actions": normalized_actions,
        "approval_fingerprint": approval_fingerprint,
        "status": APPROVAL_STATUS_PENDING,
        "created_at": created_at,
        "approved_at": None,
        "approved_by": None,
    }

    db.collection("followup_approvals").document(approval_id).set(approval_record)

    approval = {
        "created": True,
        "duplicate": False,
        "approval_id": approval_id,
        "status": APPROVAL_STATUS_PENDING,
        "contractor_id": assessment["contractor_id"],
        "contractor_name": assessment["contractor_name"],
        "readiness_status": assessment["readiness_status"],
        "risk_level": assessment["risk_level"],
        "issues": assessment["issues"],
        "proposed_actions": normalized_actions,
        "created_at": created_at,
        "message": (
            "Follow-up actions have been prepared for human approval. "
            "No follow-up actions were created."
        ),
    }

    attention = create_human_attention(approval)
    approval["human_attention"] = attention
    return approval


def approve_followup_actions(approval_id: str, approved_by: str = "human_reviewer") -> dict:
    """Approve a pending request and create the proposed actions."""
    if not approval_id or not approval_id.strip():
        raise ValueError("approval_id is required.")
    if not approved_by or not approved_by.strip():
        raise ValueError("approved_by is required.")

    approval_id = approval_id.strip()
    approved_by = approved_by.strip()
    db = get_firestore_client()
    approval_reference = db.collection("followup_approvals").document(approval_id)
    approval_snapshot = approval_reference.get()

    if not approval_snapshot.exists:
        raise LookupError(f"Approval '{approval_id}' was not found.")

    approval = approval_snapshot.to_dict()
    status = approval.get("status")

    if status not in VALID_APPROVAL_STATUSES:
        raise ValueError(f"Invalid approval status '{status}'.")

    if status != APPROVAL_STATUS_PENDING:
        return {
            "approved": False,
            "approval_id": approval_id,
            "status": status,
            "message": (
                "This approval request is no longer pending and cannot be executed again."
            ),
        }

    created_actions = []
    for proposed_action in approval.get("proposed_actions", []):
        action = create_followup_action(
            contractor_id=approval["contractor_id"],
            issue_type=proposed_action["issue_type"],
            issue_reference=proposed_action["issue_reference"],
            description=proposed_action["description"],
            priority=proposed_action["priority"],
            owner=proposed_action["owner"],
            due_date=proposed_action["due_date"],
        )
        created_actions.append(action)

    approved_at = datetime.now(timezone.utc).isoformat()
    approval_reference.update({
        "status": APPROVAL_STATUS_APPROVED,
        "approved_at": approved_at,
        "approved_by": approved_by,
    })

    attention = resolve_human_attention(approval_id, approved_by)

    return {
        "approved": True,
        "approval_id": approval_id,
        "status": APPROVAL_STATUS_APPROVED,
        "approved_at": approved_at,
        "approved_by": approved_by,
        "created_actions": created_actions,
        "human_attention": attention,
    }
