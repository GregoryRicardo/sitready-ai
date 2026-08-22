from datetime import datetime, timezone

from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client


VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"open", "completed", "cancelled"}


def create_followup_action(
    contractor_id: str,
    issue_type: str,
    issue_reference: str,
    description: str,
    priority: str,
    owner: str,
    due_date: str,
    source: str = "contractor_readiness_assessment",
) -> dict:
    """
    Create a follow-up action for a contractor issue.

    Prevents duplicate open actions for the same contractor,
    issue type and issue reference.
    """

    if not contractor_id or not contractor_id.strip():
        raise ValueError("contractor_id is required.")

    if not issue_type or not issue_type.strip():
        raise ValueError("issue_type is required.")

    if not issue_reference or not issue_reference.strip():
        raise ValueError("issue_reference is required.")

    if not description or not description.strip():
        raise ValueError("description is required.")

    if priority not in VALID_PRIORITIES:
        raise ValueError(
            f"Invalid priority '{priority}'. "
            f"Expected one of: {sorted(VALID_PRIORITIES)}"
        )

    if not owner or not owner.strip():
        raise ValueError("owner is required.")

    if not due_date or not due_date.strip():
        raise ValueError("due_date is required.")

    contractor_id = contractor_id.strip().upper()
    issue_type = issue_type.strip().lower()
    issue_reference = issue_reference.strip()
    description = description.strip()
    owner = owner.strip()
    source = source.strip()

    db = get_firestore_client()

    # ---------------------------------------------------------
    # DUPLICATE CHECK
    # ---------------------------------------------------------

    existing_query = (
        db.collection("followup_actions")
        .where(
            filter=FieldFilter(
                "contractor_id",
                "==",
                contractor_id,
            )
        )
        .stream()
    )

    for existing_document in existing_query:
        existing = existing_document.to_dict()

        if (
            existing.get("issue_type") == issue_type
            and existing.get("issue_reference") == issue_reference
            and existing.get("status") == "open"
        ):
            return {
                "created": False,
                "duplicate": True,
                "followup_id": existing_document.id,
                **existing,
            }

    # ---------------------------------------------------------
    # CREATE ACTION
    # ---------------------------------------------------------

    followup_id = (
        f"FA-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    )

    now = datetime.now(timezone.utc).isoformat()

    action = {
        "followup_id": followup_id,
        "contractor_id": contractor_id,
        "issue_type": issue_type,
        "issue_reference": issue_reference,
        "description": description,
        "priority": priority,
        "owner": owner,
        "due_date": due_date,
        "status": "open",
        "source": source,
        "created_at": now,
        "completed_at": None,
    }

    (
        db.collection("followup_actions")
        .document(followup_id)
        .set(action)
    )

    return {
        "created": True,
        "duplicate": False,
        **action,
    }