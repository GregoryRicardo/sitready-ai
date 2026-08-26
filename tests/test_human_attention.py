from google.cloud.firestore_v1.base_query import FieldFilter

from agent.tools.followup_approval_tools import approve_followup_actions
from agent.tools.taskmaster_tools import run_taskmaster_workflow


CONTRACTOR_ID = "C003"


def _attention_for_contractor(db):
    return [
        document.to_dict()
        for document in db.collection("human_attention")
        .where(
            filter=FieldFilter(
                "contractor_id",
                "==",
                CONTRACTOR_ID,
            )
        )
        .stream()
    ]


def test_human_attention_created_and_resolved(clean_taskmaster_state):
    """
    C003 must produce a visible practitioner attention record before
    any consequential follow-up action is created.
    """
    db = clean_taskmaster_state

    result = run_taskmaster_workflow(CONTRACTOR_ID)

    assert result["workflow_status"] == "awaiting_human_approval"
    assert result["approval_required"] is True
    assert result["approval"]["status"] == "pending"

    attention = result["approval"]["human_attention"]

    assert attention["status"] == "open"
    assert attention["approval_id"] == result["approval"]["approval_id"]
    assert attention["contractor_id"] == CONTRACTOR_ID
    assert attention["action_count"] == len(result["approval"]["proposed_actions"])
    assert attention["recipient_roles"]

    stored_attention = _attention_for_contractor(db)
    assert len(stored_attention) == 1
    assert stored_attention[0]["status"] == "open"

    approval_id = result["approval"]["approval_id"]

    approval_result = approve_followup_actions(
        approval_id=approval_id,
        approved_by="test_practitioner",
    )

    assert approval_result["approved"] is True
    assert approval_result["status"] == "approved"
    assert approval_result["human_attention"]["status"] == "resolved"

    stored_attention = _attention_for_contractor(db)
    assert len(stored_attention) == 1
    assert stored_attention[0]["status"] == "resolved"
    assert stored_attention[0]["resolved_by"] == "test_practitioner"
