from agent.firestore_client import get_firestore_client
from agent.tools.followup_orchestration import (
    create_followup_actions_for_readiness,
)


CONTRACTOR_ID = "C003"
EXPECTED_ISSUE_COUNT = 5
EXPECTED_ACTION_COUNT = 5



def clear_followup_actions() -> None:
    """
    Remove follow-up actions from the local emulator so the test
    always starts from a known state.
    """
    db = get_firestore_client()

    documents = list(
        db.collection("followup_actions").stream()
    )

    for document in documents:
        document.reference.delete()


def test_end_to_end_readiness_and_followup_workflow() -> None:

    clear_followup_actions()

    # ---------------------------------------------------------
    # FIRST RUN
    # ---------------------------------------------------------

    first_result = create_followup_actions_for_readiness(
        CONTRACTOR_ID
    )

    assert first_result["contractor_id"] == CONTRACTOR_ID
    assert first_result["contractor_name"] == "ABC Construction"
    assert first_result["readiness_status"] == "NOT_READY"
    assert first_result["risk_level"] == "HIGH"

    issues = first_result["issues"]
    actions = first_result["actions"]

    assert len(issues) == EXPECTED_ISSUE_COUNT
    assert len(actions) == EXPECTED_ACTION_COUNT

    created_actions = [
        action
        for action in actions
        if action["created"] is True
        and action["duplicate"] is False
    ]

    duplicate_actions = [
        action
        for action in actions
        if action["duplicate"] is True
    ]

    assert len(created_actions) == EXPECTED_ACTION_COUNT
    assert len(duplicate_actions) == 0

    # Verify every readiness issue has an action.
    issue_keys = {
        (
            issue["issue_type"],
            issue["issue_reference"],
        )
        for issue in issues
    }

    action_keys = {
        (
            action["issue_type"],
            action["issue_reference"],
        )
        for action in created_actions
    }

    assert action_keys == issue_keys

    # ---------------------------------------------------------
    # SECOND RUN
    # ---------------------------------------------------------

    second_result = create_followup_actions_for_readiness(
        CONTRACTOR_ID
    )

    assert second_result["readiness_status"] == "NOT_READY"
    assert second_result["risk_level"] == "HIGH"

    second_actions = second_result["actions"]

    assert len(second_actions) == EXPECTED_ACTION_COUNT

    second_created = [
        action
        for action in second_actions
        if action["created"] is True
    ]

    second_duplicates = [
        action
        for action in second_actions
        if action["duplicate"] is True
    ]

    # Idempotency requirement:
    # the second execution must create nothing new.
    assert len(second_created) == 0
    assert len(second_duplicates) == EXPECTED_ACTION_COUNT

    # Verify that the same follow-up IDs were reused.
    first_ids = {
        action["followup_id"]
        for action in created_actions
    }

    second_ids = {
        action["followup_id"]
        for action in second_duplicates
    }

    assert second_ids == first_ids


if __name__ == "__main__":
    test_end_to_end_readiness_and_followup_workflow()

    print()
    print("===================================")
    print("END-TO-END READINESS TEST PASSED")
    print("===================================")
    print("Contractor: C003")
    print("Status: NOT_READY")
    print("Risk: HIGH")
    print("Issues verified: 5")
    print("First run actions created: 5")
    print("Second run new actions: 0")
    print("Second run duplicates: 5")