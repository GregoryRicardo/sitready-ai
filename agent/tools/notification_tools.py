from datetime import datetime, timedelta, timezone
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client


CHANNEL_EMAIL = "email"
CHANNEL_WHATSAPP = "whatsapp"

STATUS_SIMULATED = "simulated"
STATUS_TRIGGERED = "triggered"
STATUS_SENT = "sent"
STATUS_SCHEDULED = "scheduled"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _notification_id(channel: str, approval_id: str) -> str:
    prefix = "EMAIL" if channel == CHANNEL_EMAIL else "WA"
    return f"NOT-{prefix}-{approval_id}"


def create_notification_event(
    *,
    channel: str,
    approval_id: str,
    contractor_id: str,
    recipient_roles: list[str],
    status: str,
    mode: str,
    subject: str,
    message: str,
    escalation_reason: str | None = None,
) -> dict[str, Any]:
    """Create an auditable notification event. External delivery is not claimed."""
    if channel not in {CHANNEL_EMAIL, CHANNEL_WHATSAPP}:
        raise ValueError("Unsupported notification channel.")

    notification_id = _notification_id(channel, approval_id)
    db = get_firestore_client()
    reference = db.collection("notification_events").document(notification_id)
    snapshot = reference.get()

    if snapshot.exists:
        existing = snapshot.to_dict() or {}
        return {"created": False, "duplicate": True, **existing}

    record = {
        "notification_id": notification_id,
        "channel": channel,
        "approval_id": approval_id,
        "contractor_id": contractor_id,
        "recipient_roles": recipient_roles,
        "status": status,
        "mode": mode,
        "subject": subject,
        "message": message,
        "escalation_reason": escalation_reason,
        "created_at": _now(),
    }

    reference.set(record)
    return {"created": True, "duplicate": False, **record}


def create_human_notification_events(attention: dict[str, Any]) -> list[dict[str, Any]]:
    """Record the initial email notification and scheduled demo escalation."""
    approval_id = str(attention.get("approval_id", "")).strip()
    contractor_id = str(attention.get("contractor_id", "")).strip().upper()
    roles = attention.get("recipient_roles", []) or ["H&S Practitioner"]

    email = create_notification_event(
        channel=CHANNEL_EMAIL,
        approval_id=approval_id,
        contractor_id=contractor_id,
        recipient_roles=roles,
        status=STATUS_SIMULATED,
        mode="demo_simulation",
        subject=f"Action required — {contractor_id} contractor readiness",
        message=(
            "SiteReady has identified consequential work requiring human review. "
            f"Approval {approval_id} is awaiting practitioner action."
        ),
    )

    escalation = create_notification_event(
        channel=CHANNEL_WHATSAPP,
        approval_id=approval_id,
        contractor_id=contractor_id,
        recipient_roles=roles,
        status=STATUS_SCHEDULED,
        mode="demo_simulation",
        subject=f"Escalation — {contractor_id}",
        message=(
            "The agent has scheduled a demo WhatsApp escalation if the human-action "
            "threshold is reached. No external WhatsApp message is sent."
        ),
        escalation_reason="No human action within the configured demo window.",
    )

    return [email, escalation]


def trigger_demo_whatsapp_escalation(approval_id: str) -> dict[str, Any]:
    """Transition the scheduled demo escalation to triggered; no external message is sent."""
    approval_id = approval_id.strip()
    if not approval_id:
        raise ValueError("approval_id is required.")

    db = get_firestore_client()
    attention_query = db.collection("human_attention").where(
        filter=FieldFilter("approval_id", "==", approval_id)
    )
    attention_documents = list(attention_query.stream())

    if not attention_documents:
        raise LookupError(f"No human-attention record found for '{approval_id}'.")

    attention = attention_documents[0].to_dict() or {}

    if attention.get("status") == "resolved":
        return {
            "triggered": False,
            "status": "resolved",
            "approval_id": approval_id,
            "message": "Escalation stopped because human approval is complete.",
        }

    notification_id = _notification_id(CHANNEL_WHATSAPP, approval_id)
    reference = db.collection("notification_events").document(notification_id)
    snapshot = reference.get()
    triggered_at = _now()

    if snapshot.exists:
        existing = snapshot.to_dict() or {}
        if existing.get("status") == STATUS_TRIGGERED:
            return {"triggered": False, "duplicate": True, **existing}

        updated = {
            **existing,
            "status": STATUS_TRIGGERED,
            "message": (
                "Demo escalation triggered by the agent because the human-action "
                "threshold was reached. No external WhatsApp message was sent."
            ),
            "escalation_reason": "Human action threshold reached.",
            "triggered_at": triggered_at,
        }
        reference.set(updated)
        return {"triggered": True, "duplicate": False, **updated}

    record = create_notification_event(
        channel=CHANNEL_WHATSAPP,
        approval_id=approval_id,
        contractor_id=str(attention.get("contractor_id", "")),
        recipient_roles=attention.get("recipient_roles", []) or ["H&S Practitioner"],
        status=STATUS_TRIGGERED,
        mode="demo_simulation",
        subject=f"Escalation required — {attention.get('contractor_id', '')}",
        message=(
            "Demo escalation triggered by the agent because the human-action "
            "threshold was reached. No external WhatsApp message was sent."
        ),
        escalation_reason="Human action threshold reached.",
    )
    return {"triggered": True, **record}


def _auto_trigger_due_escalation(approval_id: str, event: dict[str, Any]) -> dict[str, Any]:
    """Transition a due scheduled escalation on the server side."""
    if event.get("status") != STATUS_SCHEDULED:
        return event

    due_at = event.get("escalation_due_at")
    if not due_at:
        return event

    try:
        due_time = datetime.fromisoformat(due_at)
    except (TypeError, ValueError):
        return event

    if due_time > datetime.now(timezone.utc):
        return event

    result = trigger_demo_whatsapp_escalation(approval_id)
    if result.get("triggered"):
        return result
    return {**event, "status": result.get("status", event.get("status"))}


def list_notification_events(approval_id: str | None = None) -> list[dict[str, Any]]:
    """Return notification events and server-side trigger any due demo escalation."""
    db = get_firestore_client()
    query = db.collection("notification_events")

    if approval_id:
        query = query.where(
            filter=FieldFilter("approval_id", "==", approval_id.strip())
        )

    events = [document.to_dict() or {} for document in query.stream()]

    if approval_id:
        events = [
            _auto_trigger_due_escalation(approval_id.strip(), event)
            if event.get("channel") == CHANNEL_WHATSAPP
            else event
            for event in events
        ]

    events.sort(key=lambda item: item.get("created_at", ""))
    return events


def schedule_demo_whatsapp_escalation(
    approval_id: str,
    delay_seconds: int = 30,
) -> dict[str, Any]:
    """Persist the agent-driven escalation due time for deterministic monitoring."""
    approval_id = approval_id.strip()
    if not approval_id:
        raise ValueError("approval_id is required.")

    safe_delay = max(1, int(delay_seconds))
    db = get_firestore_client()
    notification_id = _notification_id(CHANNEL_WHATSAPP, approval_id)
    reference = db.collection("notification_events").document(notification_id)
    snapshot = reference.get()

    if not snapshot.exists:
        raise LookupError(
            f"Notification event '{notification_id}' does not exist; create the human notification first."
        )

    existing = snapshot.to_dict() or {}

    if existing.get("status") == STATUS_TRIGGERED:
        return {
            "scheduled": False,
            "already_triggered": True,
            "approval_id": approval_id,
            "delay_seconds": 0,
            "mode": "demo_simulation",
            "escalation_due_at": existing.get("escalation_due_at"),
        }

    now = datetime.now(timezone.utc)
    due_at = (now + timedelta(seconds=safe_delay)).isoformat()

    updated = {
        **existing,
        "status": STATUS_SCHEDULED,
        "scheduled_at": now.isoformat(),
        "escalation_due_at": due_at,
    }
    reference.set(updated)

    return {
        "scheduled": True,
        "already_scheduled": False,
        "approval_id": approval_id,
        "delay_seconds": safe_delay,
        "mode": "demo_simulation",
        "scheduled_at": now.isoformat(),
        "escalation_due_at": due_at,
    }
