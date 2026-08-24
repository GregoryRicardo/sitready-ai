import os

from agent.firestore_client import get_firestore_client
from agent.tools.audited_readiness_tools import (
    assess_contractor_readiness_with_audit,
)
from agent.tools.explanation_tools import explain_contractor_readiness
from agent.tools.readiness_tools import assess_contractor_readiness


CONTRACTOR_ID = "C003"
EXPECTED_ISSUE_COUNT = 5


def require_firestore_emulator() -> None:
    """
    Prevent this test from accidentally running against
    real Google Cloud Firestore.
    """
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

    if emulator_host != "127.0.0.1:8080":
        raise RuntimeError(
            "This test must run against the local Firestore emulator "
            "at 127.0.0.1:8080."
        )


def test_audit_record_and_explanation() -> None:
    require_firestore_emulator()

    db = get_firestore_client()

    # ---------------------------------------------------------
    # BASELINE ASSESSMENT
    # ---------------------------------------------------------

    assessment = assess_contractor_readiness(CONTRACTOR_ID)

    assert assessment["contractor_id"] == CONTRACTOR_ID
    assert assessment["contractor_name"] == "ABC Construction"
    assert assessment["readiness_status"] == "NOT_READY"
    assert assessment["risk_level"] == "HIGH"

    issues = assessment["issues"]

    assert len(issues) == EXPECTED_ISSUE_COUNT

    # ---------------------------------------------------------
    # AUDITED ASSESSMENT
    # ---------------------------------------------------------

    audited = assess_contractor_readiness_with_audit(
        CONTRACTOR_ID
    )

    assert audited["contractor_id"] == CONTRACTOR_ID
    assert audited["contractor_name"] == "ABC Construction"
    assert audited["readiness_status"] == "NOT_READY"
    assert audited["risk_level"] == "HIGH"

    assert "audit" in audited
    assert audited["audit"]["assessment_id"]
    assert audited["audit"]["assessed_at"]

    assessment_id = audited["audit"]["assessment_id"]

    # Verify the actual Firestore audit record exists.
    audit_document = (
        db.collection("readiness_assessments")
        .document(assessment_id)
        .get()
    )

    assert audit_document.exists

    audit_record = audit_document.to_dict()

    assert audit_record["assessment_id"] == assessment_id
    assert audit_record["contractor_id"] == CONTRACTOR_ID
    assert audit_record["contractor_name"] == "ABC Construction"
    assert audit_record["readiness_status"] == "NOT_READY"
    assert audit_record["risk_level"] == "HIGH"
    assert audit_record["issue_count"] == EXPECTED_ISSUE_COUNT
    assert audit_record["source"] == "site_readiness_agent"
    assert audit_record["assessed_at"]

    # Verify the audit trail contains the same issue references
    # as the deterministic assessment.
    assessment_issue_keys = {
        (
            issue["issue_type"],
            issue["issue_reference"],
            issue["rule_id"],
        )
        for issue in issues
    }

    audit_issue_keys = {
        (
            issue["issue_type"],
            issue["issue_reference"],
            issue["rule_id"],
        )
        for issue in audit_record["issues"]
    }

    assert audit_issue_keys == assessment_issue_keys

    # ---------------------------------------------------------
    # EXPLANATION
    # ---------------------------------------------------------

    explanation = explain_contractor_readiness(
        CONTRACTOR_ID
    )

    assert explanation["contractor_id"] == CONTRACTOR_ID
    assert explanation["contractor_name"] == "ABC Construction"
    assert explanation["readiness_status"] == "NOT_READY"
    assert explanation["risk_level"] == "HIGH"
    assert explanation["issue_count"] == EXPECTED_ISSUE_COUNT

    explanations = explanation["explanations"]

    assert len(explanations) == EXPECTED_ISSUE_COUNT

    explanation_keys = {
        (
            item["issue_type"],
            item["issue_reference"],
            item["rule_id"],
        )
        for item in explanations
    }

    assert explanation_keys == assessment_issue_keys

    for item in explanations:
        assert item["severity"] == "critical"
        assert item["description"]
        assert item["impact"]
        assert item["rule_id"]


if __name__ == "__main__":
    test_audit_record_and_explanation()

    print()
    print("===================================")
    print("AUDIT + EXPLANATION TEST PASSED")
    print("===================================")
    print("Contractor: C003")
    print("Status: NOT_READY")
    print("Risk: HIGH")
    print("Issues verified: 5")
    print("Audit record: verified in Firestore")
    print("Explanation evidence: verified")