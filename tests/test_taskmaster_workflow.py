from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client
from agent.tools.taskmaster_tools import run_taskmaster_workflow


AUTONOMOUS_CONTRACTOR_ID = "C002"
APPROVAL_CONTRACTOR_ID = "C003"


def clear_contractors_test_actions(
    db,
    contractor_ids: set[str],
) -> None:
    """
    Remove follow-up actions for the contractors used by this test.
    """
    documents = (
        db.collection("followup_actions")
        .where(
            filter=FieldFilter(
                "contractor_id",
                "in",
                list(contractor_ids),
            )
        )
        .stream()
    )

    for document in documents:
        document.reference.delete()


def clear_test_approvals(
    db,
    contractor_ids: set[str],
) -> None:
    """
    Remove approval records for the contractors used by this test.
    """
    documents = (
        db.collection("followup_approvals")
        .where(
            filter=FieldFilter(
                "contractor_id",
                "in",
                list(contractor_ids),
            )
        )
        .stream()
    )

    for document in documents:
        document.reference.delete()


def get_contractor_actions(
    db,
    contractor_id: str,
) -> list[dict]:
    """
    Return all follow-up actions for a contractor.
    """
    return [
        document.to_dict()
        for document in db.collection("followup_actions")
        .where(
            filter=FieldFilter(
                "contractor_id",
                "==",
                contractor_id,
            )
        )
        .stream()
    ]


def get_contractor_approvals(
    db,
    contractor_id: str,
) -> list[dict]:
    """
    Return all approval records for a contractor.
    """
    return [
        document.to_dict()
        for document in db.collection("followup_approvals")
        .where(
            filter=FieldFilter(
                "contractor_id",
                "==",
                contractor_id,
            )
        )
        .stream()
    ]


def test_autonomous_execution_path(clean_taskmaster_state) -> None:
    """
    C002 is the controlled autonomous-execution scenario.

    Expected:
    - workflow completes
    - no approval is required
    - two actions are created
    - actions are verified
    - second execution creates no duplicates
    """
    db = clean_taskmaster_state

    first_run = run_taskmaster_workflow(
        AUTONOMOUS_CONTRACTOR_ID
    )

    assert first_run["workflow_status"] == "completed"
    assert first_run["execution_mode"] == "autonomous"
    assert first_run["approval_required"] is False

    execution = first_run["execution"]

    assert len(execution["actions"]) == 2

    created_actions = [
        action
        for action in execution["actions"]
        if action.get("created") is True
    ]

    duplicate_actions = [
        action
        for action in execution["actions"]
        if action.get("duplicate") is True
    ]

    assert len(created_actions) == 2
    assert len(duplicate_actions) == 0

    assert first_run["verification"]["verified"] is True
    assert len(
        first_run["verification"]["verified_action_ids"]
    ) == 2

    actions_after_first_run = get_contractor_actions(
        db,
        AUTONOMOUS_CONTRACTOR_ID,
    )

    assert len(actions_after_first_run) == 2

    action_references = {
        action["issue_reference"]
        for action in actions_after_first_run
    }

    assert action_references == {
        "DOC004",
        "CA001",
    }

    for action in actions_after_first_run:
        assert action["status"] == "open"
        assert (
            action["source"]
            == "taskmaster_autonomous_workflow"
        )

    second_run = run_taskmaster_workflow(
        AUTONOMOUS_CONTRACTOR_ID
    )

    assert second_run["workflow_status"] == "completed"
    assert second_run["execution_mode"] == "autonomous"
    assert second_run["approval_required"] is False

    second_execution = second_run["execution"]

    assert len(second_execution["actions"]) == 2

    second_created_actions = [
        action
        for action in second_execution["actions"]
        if action.get("created") is True
    ]

    second_duplicate_actions = [
        action
        for action in second_execution["actions"]
        if action.get("duplicate") is True
    ]

    assert len(second_created_actions) == 0
    assert len(second_duplicate_actions) == 2

    assert second_run["verification"]["verified"] is True

    actions_after_second_run = get_contractor_actions(
        db,
        AUTONOMOUS_CONTRACTOR_ID,
    )

    assert len(actions_after_second_run) == 2


def test_human_approval_path(clean_taskmaster_state) -> None:
    """
    C003 is the consequential-action scenario.

    Expected:
    - workflow pauses for human approval
    - approval is pending
    - no follow-up actions are created
    """
    db = clean_taskmaster_state

    result = run_taskmaster_workflow(
        APPROVAL_CONTRACTOR_ID
    )

    assert (
        result["workflow_status"]
        == "awaiting_human_approval"
    )

    assert (
        result["execution_mode"]
        == "human_approval"
    )

    assert result["approval_required"] is True

    assert result["approval_reasons"]

    assert result["approval"]["approval_id"]
    assert result["approval"]["status"] == "pending"

    actions = get_contractor_actions(
        db,
        APPROVAL_CONTRACTOR_ID,
    )

    assert len(actions) == 0

    approvals = get_contractor_approvals(
        db,
        APPROVAL_CONTRACTOR_ID,
    )

    assert len(approvals) == 1
    assert approvals[0]["status"] == "pending"


def test_phase13_3_taskmaster_workflow(
    clean_taskmaster_state,
) -> None:
    """
    End-to-end Taskmaster regression test.

    This test intentionally runs both controlled paths in one
    isolated local-emulator state.
    """
    db = clean_taskmaster_state

    contractor_ids = {
        AUTONOMOUS_CONTRACTOR_ID,
        APPROVAL_CONTRACTOR_ID,
    }

    clear_contractors_test_actions(
        db,
        contractor_ids,
    )

    clear_test_approvals(
        db,
        contractor_ids,
    )

    # Autonomous path
    first_run = run_taskmaster_workflow(
        AUTONOMOUS_CONTRACTOR_ID
    )

    assert first_run["workflow_status"] == "completed"
    assert first_run["execution_mode"] == "autonomous"
    assert first_run["approval_required"] is False

    assert len(first_run["execution"]["actions"]) == 2

    created_actions = [
        action
        for action in first_run["execution"]["actions"]
        if action.get("created") is True
    ]

    assert len(created_actions) == 2

    assert first_run["verification"]["verified"] is True

    # Human-approval path
    clear_test_approvals(
        db,
        {APPROVAL_CONTRACTOR_ID},
    )

    clear_contractors_test_actions(
        db,
        {APPROVAL_CONTRACTOR_ID},
    )

    approval_run = run_taskmaster_workflow(
        APPROVAL_CONTRACTOR_ID
    )

    assert (
        approval_run["workflow_status"]
        == "awaiting_human_approval"
    )

    assert (
        approval_run["execution_mode"]
        == "human_approval"
    )

    assert approval_run["approval_required"] is True

    assert approval_run["approval"]["approval_id"]
    assert approval_run["approval"]["status"] == "pending"

    c003_actions = get_contractor_actions(
        db,
        APPROVAL_CONTRACTOR_ID,
    )

    assert len(c003_actions) == 0


if __name__ == "__main__":
    db = get_firestore_client()

    test_contractor_ids = {
        AUTONOMOUS_CONTRACTOR_ID,
        APPROVAL_CONTRACTOR_ID,
    }

    clear_contractors_test_actions(
        db,
        test_contractor_ids,
    )

    clear_test_approvals(
        db,
        test_contractor_ids,
    )

    test_phase13_3_taskmaster_workflow(
        db
    )

    print()
    print("==========================================")
    print("PHASE 13.3.1 TASKMASTER TEST PASSED")
    print("==========================================")
    print("Autonomous contractor: C002")
    print("Autonomous execution: verified")
    print("Approval contractor: C003")
    print("Human approval required: verified")
    print("Actions created before approval: 0")
    print("==========================================")