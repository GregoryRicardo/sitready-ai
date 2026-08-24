import os

from agent.firestore_client import get_firestore_client
from agent.tools.followup_approval_tools import (
    approve_followup_actions,
    propose_followup_actions,
)


CONTRACTOR_ID = "C003"


def require_firestore_emulator() -> None:
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

    if emulator_host != "127.0.0.1:8080":
        raise RuntimeError(
            "This test must run against the local Firestore emulator "
            "at 127.0.0.1:8080."
        )


def test_followup_approval_workflow() -> None:
    require_firestore_emulator()

    db = get_firestore_client()

    # ---------------------------------------------------------
    # START CLEAN
    # ---------------------------------------------------------

    for document in db.collection("followup_approvals").stream():
        document.reference.delete()

    for document in db.collection("followup_actions").stream():
        document.reference.delete()

    # ---------------------------------------------------------
    # FIRST PROPOSAL
    # ---------------------------------------------------------

    first = propose_followup_actions(CONTRACTOR_ID)

    assert first["created"] is True
    assert first["duplicate"] is False
    assert first["status"] == "pending"
    assert first["approval_id"]
    assert first["contractor_id"] == CONTRACTOR_ID
    assert first["readiness_status"] == "NOT_READY"
    assert first["risk_level"] == "HIGH"
    assert len(first["proposed_actions"]) == 5

    approval_id = first["approval_id"]

    # ---------------------------------------------------------
    # VERIFY NO ACTIONS WERE CREATED
    # ---------------------------------------------------------

    actions_after_proposal = list(
        db.collection("followup_actions").stream()
    )

    assert actions_after_proposal == []

    # ---------------------------------------------------------
    # VERIFY APPROVAL RECORD
    # ---------------------------------------------------------

    approval_document = (
        db.collection("followup_approvals")
        .document(approval_id)
        .get()
    )

    assert approval_document.exists

    approval_record = approval_document.to_dict()

    assert approval_record["status"] == "pending"
    assert approval_record["contractor_id"] == CONTRACTOR_ID
    assert approval_record["approval_id"] == approval_id
    assert approval_record["approval_fingerprint"]

    # ---------------------------------------------------------
    # SECOND IDENTICAL PROPOSAL
    # ---------------------------------------------------------

    second = propose_followup_actions(CONTRACTOR_ID)

    assert second["created"] is False
    assert second["duplicate"] is True
    assert second["status"] == "pending"
    assert second["approval_id"] == approval_id

    # Confirm only one approval exists.
    approvals = list(
        db.collection("followup_approvals").stream()
    )

    assert len(approvals) == 1

    # ---------------------------------------------------------
    # HUMAN APPROVAL
    # ---------------------------------------------------------

    approved = approve_followup_actions(
        approval_id=approval_id,
        approved_by="Gregory",
    )

    assert approved["approved"] is True
    assert approved["status"] == "approved"
    assert approved["approval_id"] == approval_id
    assert approved["approved_by"] == "Gregory"
    assert approved["approved_at"]
    assert len(approved["created_actions"]) == 5

    # Every action should have been newly created.
    for action in approved["created_actions"]:
        assert action["created"] is True
        assert action["duplicate"] is False
        assert action["status"] == "open"

    # ---------------------------------------------------------
    # VERIFY FIRESTORE ACTIONS
    # ---------------------------------------------------------

    actions = list(
        db.collection("followup_actions").stream()
    )

    assert len(actions) == 5

    for document in actions:
        action = document.to_dict()

        assert action["contractor_id"] == CONTRACTOR_ID
        assert action["status"] == "open"
        assert action["priority"] == "high"
        assert action["followup_id"]
        assert action["issue_reference"]

    # ---------------------------------------------------------
    # VERIFY APPROVAL UPDATED
    # ---------------------------------------------------------

    approved_document = (
        db.collection("followup_approvals")
        .document(approval_id)
        .get()
    )

    assert approved_document.exists

    approved_record = approved_document.to_dict()

    assert approved_record["status"] == "approved"
    assert approved_record["approved_by"] == "Gregory"
    assert approved_record["approved_at"]

    # ---------------------------------------------------------
    # SECOND APPROVAL ATTEMPT
    # ---------------------------------------------------------

    second_approval = approve_followup_actions(
        approval_id=approval_id,
        approved_by="Gregory",
    )

    assert second_approval["approved"] is False
    assert second_approval["approval_id"] == approval_id
    assert second_approval["status"] == "approved"

    # The action count must remain exactly five.
    actions_after_second_approval = list(
        db.collection("followup_actions").stream()
    )

    assert len(actions_after_second_approval) == 5


if __name__ == "__main__":
    test_followup_approval_workflow()

    print()
    print("===================================")
    print("FOLLOW-UP APPROVAL TEST PASSED")
    print("===================================")
    print("Contractor: C003")
    print("Proposal created: 1")
    print("Duplicate proposal blocked: 1")
    print("Actions created after approval: 5")
    print("Second approval blocked: 1")