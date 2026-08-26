from datetime import datetime, timedelta, timezone

from google.cloud.firestore_v1.base_query import FieldFilter

from agent.tools.notification_tools import (
    CHANNEL_EMAIL,
    CHANNEL_WHATSAPP,
    STATUS_SCHEDULED,
    STATUS_TRIGGERED,
    list_notification_events,
)
from agent.tools.taskmaster_tools import run_taskmaster_workflow


CONTRACTOR_ID = "C003"


def _notification_documents(db, approval_id: str) -> list[dict]:
    return [
        document.to_dict() or {}
        for document in db.collection("notification_events")
        .where(
            filter=FieldFilter(
                "approval_id",
                "==",
                approval_id,
            )
        )
        .stream()
    ]


def _run_approval_workflow(contractor_id: str, db):
    result = run_taskmaster_workflow(contractor_id)
    approval_id = result["approval"]["approval_id"]
    assert result["approval_required"] is True
    assert result["human_attention"]["approval_id"] == approval_id
    return result, approval_id


def test_human_notification_events_are_created_and_scheduled(clean_taskmaster_state):
    result, approval_id = _run_approval_workflow(CONTRACTOR_ID, clean_taskmaster_state)

    events = _notification_documents(clean_taskmaster_state, approval_id)

    by_channel = {event["channel"]: event for event in events}

    assert CHANNEL_EMAIL in by_channel
    assert CHANNEL_WHATSAPP in by_channel
    assert by_channel[CHANNEL_EMAIL]["status"] == "simulated"
    assert by_channel[CHANNEL_WHATSAPP]["status"] == STATUS_SCHEDULED
    assert by_channel[CHANNEL_WHATSAPP]["escalation_due_at"]
    assert by_channel[CHANNEL_WHATSAPP]["mode"] == "demo_simulation"
    assert result["escalation_schedule"]["approval_id"] == approval_id


def test_due_escalation_reconciles_without_manual_trigger(clean_taskmaster_state):
    _, approval_id = _run_approval_workflow(CONTRACTOR_ID, clean_taskmaster_state)
    db = clean_taskmaster_state

    whatsapp_ref = (
        db.collection("notification_events")
        .where(
            filter=FieldFilter("approval_id", "==", approval_id)
        )
        .where(
            filter=FieldFilter("channel", "==", CHANNEL_WHATSAPP)
        )
        .stream()
    )
    documents = list(whatsapp_ref)
    assert len(documents) == 1

    due_at = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()
    documents[0].reference.update({"escalation_due_at": due_at})

    events = list_notification_events(approval_id)
    whatsapp = [
        event
        for event in events
        if event["channel"] == CHANNEL_WHATSAPP
    ][0]

    assert whatsapp["status"] == STATUS_TRIGGERED
    assert whatsapp["triggered_at"]
    assert whatsapp["escalation_reason"] == "Human action threshold reached."
    assert "No external WhatsApp message was sent." in whatsapp["message"]


def test_resolved_attention_stops_escalation(clean_taskmaster_state):
    result, approval_id = _run_approval_workflow(CONTRACTOR_ID, clean_taskmaster_state)
    db = clean_taskmaster_state

    db.collection("human_attention").document(
        result["human_attention"]["attention_id"]
    ).update({
        "status": "resolved",
        "resolved_by": "test_practitioner",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    })

    events = list_notification_events(approval_id)
    whatsapp = [
        event
        for event in events
        if event["channel"] == CHANNEL_WHATSAPP
    ][0]

    assert whatsapp["status"] == STATUS_SCHEDULED
