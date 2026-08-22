from datetime import date, timedelta

from agent.evaluation import evaluate_readiness
from agent.tools.contractor_tools import get_contractor
from agent.tools.corrective_action_tools import get_corrective_actions
from agent.tools.document_tools import get_documents
from agent.tools.followup_action_tools import create_followup_action
from agent.tools.inspection_tools import get_inspections
from agent.tools.training_tools import get_training_records


# ---------------------------------------------------------------------
# PROTOTYPE WORKFLOW SETTINGS
# ---------------------------------------------------------------------
# Synthetic demo defaults only.
# These must be replaced with client-confirmed rules later.

DEFAULT_OWNER_BY_CATEGORY = {
    "document": "H&S Practitioner",
    "training": "Contractor Manager",
    "inspection": "Site Manager",
    "corrective_action": "H&S Practitioner",
}

DEFAULT_CRITICAL_DAYS = 1
DEFAULT_MEDIUM_DAYS = 7


def calculate_due_date(priority: str) -> str:
    """Calculate a prototype follow-up due date."""
    today = date.today()

    if priority == "high":
        due_date = today + timedelta(days=DEFAULT_CRITICAL_DAYS)
    else:
        due_date = today + timedelta(days=DEFAULT_MEDIUM_DAYS)

    return due_date.isoformat()


def determine_action_owner(category: str) -> str:
    """Return the prototype owner for an issue category."""
    return DEFAULT_OWNER_BY_CATEGORY.get(
        category,
        "H&S Practitioner",
    )


def run_contractor_readiness(contractor_id: str) -> dict:
    """
    Run the complete SiteReady AI contractor-readiness workflow.

    Workflow:
        1. Retrieve contractor
        2. Retrieve evidence
        3. Evaluate readiness
        4. Create follow-up actions
        5. Return complete result
    """

    contractor = get_contractor(contractor_id)

    documents = get_documents(contractor_id)
    training_records = get_training_records(contractor_id)
    inspections = get_inspections(contractor_id)
    corrective_actions = get_corrective_actions(contractor_id)

    readiness = evaluate_readiness(
        contractor=contractor,
        documents=documents,
        training_records=training_records,
        inspections=inspections,
        corrective_actions=corrective_actions,
    )

    actions_created = []
    existing_actions = []

    for issue in readiness["issues"]:
        priority = (
            "high"
            if issue.get("severity") == "critical"
            else "medium"
        )

        owner = determine_action_owner(
            issue.get("category", "general")
        )

        due_date = calculate_due_date(priority)

        action_result = create_followup_action(
            contractor_id=contractor_id,
            issue_type=issue["issue_type"],
            issue_reference=issue["issue_reference"],
            description=issue["description"],
            priority=priority,
            owner=owner,
            due_date=due_date,
        )

        if action_result["created"]:
            actions_created.append(action_result)
        else:
            existing_actions.append(action_result)

    return {
        "contractor": contractor,
        "readiness": readiness,
        "actions_created": actions_created,
        "existing_actions": existing_actions,
        "summary": {
            "readiness_status": readiness["readiness_status"],
            "risk_level": readiness["risk_level"],
            "issues_found": len(readiness["issues"]),
            "actions_created": len(actions_created),
            "existing_actions": len(existing_actions),
        },
    }


if __name__ == "__main__":
    result = run_contractor_readiness("C003")

    print("\n===================================")
    print("SITEREADY AI WORKFLOW")
    print("===================================")

    print(
        f"Contractor: "
        f"{result['contractor']['company_name']}"
    )

    print(
        f"Status: "
        f"{result['readiness']['readiness_status']}"
    )

    print(
        f"Risk: "
        f"{result['readiness']['risk_level']}"
    )

    print(
        f"Issues found: "
        f"{result['summary']['issues_found']}"
    )

    print(
        f"Actions created: "
        f"{result['summary']['actions_created']}"
    )

    print(
        f"Existing actions: "
        f"{result['summary']['existing_actions']}"
    )

    if result["actions_created"]:
        print("\nNEW ACTIONS:")

        for action in result["actions_created"]:
            print(
                f"- {action['followup_id']}: "
                f"{action['description']}"
            )

    if result["existing_actions"]:
        print("\nEXISTING ACTIONS:")

        for action in result["existing_actions"]:
            print(
                f"- {action['followup_id']}: "
                f"{action['description']}"
            )