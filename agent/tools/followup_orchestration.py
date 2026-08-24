from datetime import date, timedelta

from agent.tools.followup_action_tools import create_followup_action
from agent.tools.readiness_tools import assess_contractor_readiness


# SiteReady workflow policy.
#
# These mappings determine how a readiness issue is translated
# into a follow-up action.
#
# IMPORTANT:
# These are product workflow rules, not legal or H&S requirements.
ISSUE_ACTION_RULES = {
    # Critical / high-severity document issue
    "expired_document": {
        "priority": "high",
        "owner": "H&S Practitioner",
        "due_days": 7,
    },

    # Medium-severity document issue
    "expiring_document": {
        "priority": "medium",
        "owner": "H&S Practitioner",
        "due_days": 14,
    },

    "missing_document": {
        "priority": "high",
        "owner": "H&S Practitioner",
        "due_days": 7,
    },

    "missing_training": {
        "priority": "high",
        "owner": "H&S Practitioner",
        "due_days": 7,
    },

    "failed_inspection": {
        "priority": "high",
        "owner": "Site Manager",
        "due_days": 3,
    },

    # Existing corrective action already identified as overdue
    "overdue_corrective_action": {
        "priority": "high",
        "owner": "Site Manager",
        "due_days": 3,
    },

    # Medium-severity open corrective action
    "open_corrective_action": {
        "priority": "medium",
        "owner": "Site Manager",
        "due_days": 7,
    },
}


def create_followup_actions_for_readiness(
    contractor_id: str,
) -> dict:
    """
    Assess contractor readiness and create deterministic
    follow-up actions for each identified readiness issue.

    Existing open actions are not duplicated.

    IMPORTANT:
    This function is a deterministic execution primitive.
    It should only be called by an authorized workflow such
    as the Taskmaster policy engine.

    It must not be exposed directly to the ADK agent.
    """

    if not contractor_id or not contractor_id.strip():
        raise ValueError("contractor_id is required.")

    contractor_id = contractor_id.strip().upper()

    assessment = assess_contractor_readiness(
        contractor_id
    )

    actions = []

    for issue in assessment["issues"]:
        issue_type = issue["issue_type"]

        action_rule = ISSUE_ACTION_RULES.get(
            issue_type
        )

        if not action_rule:
            raise ValueError(
                f"No follow-up action rule configured for "
                f"issue type '{issue_type}'."
            )

        due_date = (
            date.today()
            + timedelta(
                days=action_rule["due_days"]
            )
        ).isoformat()

        result = create_followup_action(
            contractor_id=assessment["contractor_id"],
            issue_type=issue_type,
            issue_reference=issue["issue_reference"],
            description=issue["description"],
            priority=action_rule["priority"],
            owner=action_rule["owner"],
            due_date=due_date,
            source="taskmaster_autonomous_workflow",
        )

        actions.append(result)

    return {
        "contractor_id": assessment["contractor_id"],
        "contractor_name": assessment["contractor_name"],
        "readiness_status": assessment["readiness_status"],
        "risk_level": assessment["risk_level"],
        "issues": assessment["issues"],
        "actions": actions,
    }