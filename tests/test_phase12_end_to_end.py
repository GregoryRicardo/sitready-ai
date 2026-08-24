import os

from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client
from agent.tools.audited_readiness_tools import (
    assess_contractor_readiness_with_audit,
)
from agent.tools.change_detection_tools import (
    compare_contractor_assessments,
)
from agent.tools.explanation_tools import (
    explain_contractor_readiness,
)
from agent.tools.followup_approval_tools import (
    approve_followup_actions,
    propose_followup_actions,
)
from agent.tools.readiness_tools import assess_contractor_readiness


CONTRACTOR_ID = "C003"


def require_firestore_emulator() -> None:
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

    if emulator_host != "127.0.0.1:8080":
        raise RuntimeError(
            "Phase 12 must run against the local Firestore emulator "
            "at 127.0.0.1:8080."
        )


def clear_test_write_collections(db) -> None:
    """
    Clear collections that Phase 12 writes directly.
    """
    for document in db.collection("followup_approvals").stream():
        document.reference.delete()

    for document in db.collection("followup_actions").stream():
        document.reference.delete()


def clear_test_readiness_history(
    db,
    contractor_id: str,
) -> None:
    """
    Remove readiness assessment history for the test contractor
    so Phase 12 controls its own historical baseline.
    """
    documents = (
        db.collection("readiness_assessments")
        .where(
            filter=FieldFilter(
                "contractor_id",
                "==",
                contractor_id,
            )
        )
        .stream()
    )

    for document in documents:
        document.reference.delete()


def test_phase12_end_to_end() -> None:
    require_firestore_emulator()

    db = get_firestore_client()

    clear_test_write_collections(db)
    clear_test_readiness_history(db, CONTRACTOR_ID)

    # ---------------------------------------------------------
    # 1. READINESS ASSESSMENT
    # ---------------------------------------------------------

    assessment = assess_contractor_readiness(
        CONTRACTOR_ID
    )

    assert assessment["contractor_id"] == CONTRACTOR_ID
    assert assessment["contractor_name"] == "ABC Construction"
    assert assessment["readiness_status"] == "NOT_READY"
    assert assessment["risk_level"] == "HIGH"
    assert len(assessment["issues"]) == 5

    issue_references = {
        issue["issue_reference"]
        for issue in assessment["issues"]
    }

    assert issue_references == {
        "DOC007",
        "DOC008",
        "TR009",
        "INS003",
        "CA002",
    }

    # ---------------------------------------------------------
    # 2. EXPLANATION
    # ---------------------------------------------------------

    explanation = explain_contractor_readiness(
        CONTRACTOR_ID
    )

    assert explanation["contractor_id"] == CONTRACTOR_ID
    assert explanation["contractor_name"] == "ABC Construction"
    assert explanation["readiness_status"] == "NOT_READY"
    assert explanation["risk_level"] == "HIGH"
    assert explanation["issue_count"] == 5

    explanation_references = {
        item["issue_reference"]
        for item in explanation["explanations"]
    }

    assert explanation_references == issue_references

    for item in explanation["explanations"]:
        assert item["rule_id"]
        assert item["severity"] == "critical"
        assert item["description"]
        assert item["impact"]

    # ---------------------------------------------------------
    # 3. AUDIT
    # ---------------------------------------------------------

    audited = assess_contractor_readiness_with_audit(
        CONTRACTOR_ID
    )

    assert audited["contractor_id"] == CONTRACTOR_ID
    assert audited["readiness_status"] == "NOT_READY"
    assert audited["risk_level"] == "HIGH"
    assert audited["audit"]["assessment_id"]
    assert audited["audit"]["assessed_at"]

    first_assessment_id = audited["audit"]["assessment_id"]

    first_audit_document = (
        db.collection("readiness_assessments")
        .document(first_assessment_id)
        .get()
    )

    assert first_audit_document.exists

    first_audit_record = first_audit_document.to_dict()

    assert first_audit_record["contractor_id"] == CONTRACTOR_ID
    assert first_audit_record["readiness_status"] == "NOT_READY"
    assert first_audit_record["risk_level"] == "HIGH"
    assert first_audit_record["issue_count"] == 5
    assert first_audit_record["issues"]

    # Create a second known historical assessment.
    second_audited = assess_contractor_readiness_with_audit(
        CONTRACTOR_ID
    )

    assert second_audited["contractor_id"] == CONTRACTOR_ID
    assert second_audited["readiness_status"] == "NOT_READY"
    assert second_audited["risk_level"] == "HIGH"
    assert second_audited["audit"]["assessment_id"]
    assert second_audited["audit"]["assessed_at"]

    second_assessment_id = (
        second_audited["audit"]["assessment_id"]
    )

    assert second_assessment_id != first_assessment_id

    second_audit_document = (
        db.collection("readiness_assessments")
        .document(second_assessment_id)
        .get()
    )

    assert second_audit_document.exists

    second_audit_record = second_audit_document.to_dict()

    assert second_audit_record["contractor_id"] == CONTRACTOR_ID
    assert second_audit_record["readiness_status"] == "NOT_READY"
    assert second_audit_record["risk_level"] == "HIGH"
    assert second_audit_record["issue_count"] == 5
    assert second_audit_record["issues"]

    # ---------------------------------------------------------
    # 4. HISTORICAL COMPARISON
    # ---------------------------------------------------------

    comparison = compare_contractor_assessments(
        CONTRACTOR_ID
    )

    assert comparison["comparison_available"] is True
    assert comparison["latest_assessment"]["assessment_id"]
    assert comparison["previous_assessment"]["assessment_id"]

    assert comparison["status_changed"] is False
    assert comparison["risk_changed"] is False

    # Phase 12 deliberately created two known assessments
    # from the same seeded readiness state.
    assert comparison["new_issue_count"] == 0
    assert comparison["resolved_issue_count"] == 0
    assert comparison["persistent_issue_count"] == 5

    # ---------------------------------------------------------
    # 5. FOLLOW-UP PROPOSAL
    # ---------------------------------------------------------

    proposal = propose_followup_actions(
        CONTRACTOR_ID
    )

    assert proposal["created"] is True
    assert proposal["duplicate"] is False
    assert proposal["status"] == "pending"
    assert proposal["approval_id"]
    assert len(proposal["proposed_actions"]) == 5

    approval_id = proposal["approval_id"]

    # Proposal must NOT create actions.
    actions_after_proposal = list(
        db.collection("followup_actions").stream()
    )

    assert len(actions_after_proposal) == 0

    # ---------------------------------------------------------
    # 6. DUPLICATE PROPOSAL PROTECTION
    # ---------------------------------------------------------

    duplicate_proposal = propose_followup_actions(
        CONTRACTOR_ID
    )

    assert duplicate_proposal["created"] is False
    assert duplicate_proposal["duplicate"] is True
    assert duplicate_proposal["status"] == "pending"
    assert duplicate_proposal["approval_id"] == approval_id

    approvals = list(
        db.collection("followup_approvals").stream()
    )

    assert len(approvals) == 1

    # ---------------------------------------------------------
    # 7. HUMAN APPROVAL
    # ---------------------------------------------------------

    approval_result = approve_followup_actions(
        approval_id=approval_id,
        approved_by="phase12_test",
    )

    assert approval_result["approved"] is True
    assert approval_result["approval_id"] == approval_id
    assert approval_result["status"] == "approved"
    assert approval_result["approved_by"] == "phase12_test"
    assert approval_result["approved_at"]
    assert len(approval_result["created_actions"]) == 5

    # ---------------------------------------------------------
    # 8. VERIFY ACTIONS
    # ---------------------------------------------------------

    actions = list(
        db.collection("followup_actions").stream()
    )

    assert len(actions) == 5

    action_references = set()

    for document in actions:
        action = document.to_dict()

        assert action["contractor_id"] == CONTRACTOR_ID
        assert action["status"] == "open"
        assert action["priority"] == "high"
        assert action["followup_id"]
        assert action["issue_reference"]

        action_references.add(
            action["issue_reference"]
        )

    assert action_references == issue_references

    # ---------------------------------------------------------
    # 9. SECOND APPROVAL ATTEMPT
    # ---------------------------------------------------------

    second_approval = approve_followup_actions(
        approval_id=approval_id,
        approved_by="phase12_test",
    )

    assert second_approval["approved"] is False
    assert second_approval["approval_id"] == approval_id
    assert second_approval["status"] == "approved"

    actions_after_second_approval = list(
        db.collection("followup_actions").stream()
    )

    assert len(actions_after_second_approval) == 5

    # ---------------------------------------------------------
    # 10. FINAL APPROVAL RECORD
    # ---------------------------------------------------------

    final_approval_document = (
        db.collection("followup_approvals")
        .document(approval_id)
        .get()
    )

    assert final_approval_document.exists

    final_approval = final_approval_document.to_dict()

    assert final_approval["status"] == "approved"
    assert final_approval["approved_by"] == "phase12_test"
    assert final_approval["approved_at"]


if __name__ == "__main__":
    test_phase12_end_to_end()

    print()
    print("======================================")
    print("PHASE 12 END-TO-END TEST PASSED")
    print("======================================")
    print("Contractor: C003")
    print("Readiness: NOT_READY / HIGH")
    print("Issues verified: 5")
    print("Explanation evidence: verified")
    print("Audit record: verified")
    print("Historical comparison: verified")
    print("Follow-up proposal: verified")
    print("Duplicate proposal protection: verified")
    print("Human approval: verified")
    print("Actions created: 5")
    print("Repeat approval blocked: verified")
    print("======================================")