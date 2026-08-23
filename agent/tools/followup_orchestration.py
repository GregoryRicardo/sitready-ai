from datetime import date, timedelta

from agent.tools.followup_action_tools import create_followup_action
from agent.tools.readiness_tools import assess_contractor_readiness


ISSUE_ACTION_RULES = {
    "expired_document": {
        "priority": "high",
        "owner": "H&S Practitioner",
        "due_days": 7,
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
    "overdue_corrective_action": {
        "priority": "high",
        "owner": "Site Manager",
        "due_days": 3,
    },
}


def create_followup_actions_for_readiness(
    contractor_id: str,
) -> dict:
    """
    Assess contractor readiness and create deterministic follow-up
    actions for each identified readiness issue.

    Existing open actions are not duplicated.
    """

    assessment = assess_contractor_readiness(contractor_id)

    actions = []

    for issue in assessment["issues"]:
        issue_type = issue["issue_type"]

        action_rule = ISSUE_ACTION_RULES.get(issue_type)

        if not action_rule:
            raise ValueError(
                f"No follow-up action rule configured for "
                f"issue type '{issue_type}'."
            )

        due_date = (
            date.today()
            + timedelta(days=action_rule["due_days"])
        ).isoformat()

        result = create_followup_action(
            contractor_id=assessment["contractor_id"],
            issue_type=issue_type,
            issue_reference=issue["issue_reference"],
            description=issue["description"],
            priority=action_rule["priority"],
            owner=action_rule["owner"],
            due_date=due_date,
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