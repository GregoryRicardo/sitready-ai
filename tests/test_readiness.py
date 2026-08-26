from agent.evaluation import evaluate_readiness
from agent.tools.contractor_tools import get_contractor
from agent.tools.corrective_action_tools import get_corrective_actions
from agent.tools.document_tools import get_documents
from agent.tools.inspection_tools import get_inspections
from agent.tools.training_tools import get_training_records


def assess(contractor_id: str) -> None:
    contractor = get_contractor(contractor_id)
    documents = get_documents(contractor_id)
    training = get_training_records(contractor_id)
    inspections = get_inspections(contractor_id)
    actions = get_corrective_actions(contractor_id)

    result = evaluate_readiness(
        contractor=contractor,
        documents=documents,
        training_records=training,
        inspections=inspections,
        corrective_actions=actions,
    )

    print("\n==============================")
    print(contractor["company_name"])
    print("==============================")
    print(f"Status: {result['readiness_status']}")
    print(f"Risk:   {result['risk_level']}")

    if result["issues"]:
        print("\nIssues:")
        for issue in result["issues"]:
            print(f"- {issue['description']}")
    else:
        print("\nNo issues found.")


if __name__ == "__main__":
    import os

    os.environ["FIRESTORE_EMULATOR_HOST"] = "[::1]:8983"

    assess("C001")
    assess("C002")
    assess("C003")
