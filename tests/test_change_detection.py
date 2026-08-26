from agent.firestore_client import get_firestore_client
from agent.tools.audited_readiness_tools import (
    assess_contractor_readiness_with_audit,
)
from agent.tools.change_detection_tools import (
    compare_contractor_assessments,
)


CONTRACTOR_ID = "C003"



def test_change_detection_with_resolved_issue() -> None:

    db = get_firestore_client()

    # ---------------------------------------------------------
    # BASELINE
    # ---------------------------------------------------------

    baseline = assess_contractor_readiness_with_audit(
        CONTRACTOR_ID
    )

    assert baseline["readiness_status"] == "NOT_READY"
    assert baseline["risk_level"] == "HIGH"

    baseline_issue_keys = {
        (
            issue["issue_type"],
            issue["issue_reference"],
            issue["rule_id"],
        )
        for issue in baseline["issues"]
    }

    assert (
        "expired_document",
        "DOC007",
        "RULE001",
    ) in baseline_issue_keys

    document_reference = (
        db.collection("documents")
        .document("DOC007")
    )

    try:
        # -----------------------------------------------------
        # CONTROLLED CHANGE
        # -----------------------------------------------------

        document_reference.update(
            {
                "status": "valid",
            }
        )

        # -----------------------------------------------------
        # NEW ASSESSMENT
        # -----------------------------------------------------

        current = assess_contractor_readiness_with_audit(
            CONTRACTOR_ID
        )

        assert current["readiness_status"] == "NOT_READY"
        assert current["risk_level"] == "HIGH"

        current_issue_keys = {
            (
                issue["issue_type"],
                issue["issue_reference"],
                issue["rule_id"],
            )
            for issue in current["issues"]
        }

        assert (
            "expired_document",
            "DOC007",
            "RULE001",
        ) not in current_issue_keys

        # -----------------------------------------------------
        # COMPARE
        # -----------------------------------------------------

        comparison = compare_contractor_assessments(
            CONTRACTOR_ID
        )

        assert comparison["comparison_available"] is True

        assert comparison["status_changed"] is False
        assert comparison["risk_changed"] is False

        assert comparison["new_issue_count"] == 0
        assert comparison["resolved_issue_count"] == 1
        assert comparison["persistent_issue_count"] == 4

        resolved_keys = {
            (
                issue["issue_type"],
                issue["issue_reference"],
                issue["rule_id"],
            )
            for issue in comparison["resolved_issues"]
        }

        assert resolved_keys == {
            (
                "expired_document",
                "DOC007",
                "RULE001",
            )
        }

    finally:
        # -----------------------------------------------------
        # RESTORE TEST DATA
        # -----------------------------------------------------

        document_reference.update(
            {
                "status": "expired",
            }
        )


if __name__ == "__main__":
    test_change_detection_with_resolved_issue()

    print()
    print("===================================")
    print("CHANGE DETECTION TEST PASSED")
    print("===================================")
    print("Contractor: C003")
    print("Resolved issues: 1")
    print("Persistent issues: 4")
    print("Status change: none")
    print("Risk change: none")