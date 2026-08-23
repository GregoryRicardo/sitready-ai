from agent.evaluation import evaluate_readiness
from agent.tools.contractor_tools import get_contractor
from agent.tools.document_tools import get_documents
from agent.tools.training_tools import get_training_records
from agent.tools.inspection_tools import get_inspections
from agent.tools.corrective_action_tools import get_corrective_actions


def assess_contractor_readiness(contractor_id: str) -> dict:
    """
    Assess a contractor's readiness using all available evidence.

    The readiness decision is made by the deterministic evaluation engine.
    """

    contractor = get_contractor(contractor_id)

    documents = get_documents(contractor_id)

    training_records = get_training_records(contractor_id)

    inspections = get_inspections(contractor_id)

    corrective_actions = get_corrective_actions(contractor_id)

    result = evaluate_readiness(
        contractor=contractor,
        documents=documents,
        training_records=training_records,
        inspections=inspections,
        corrective_actions=corrective_actions,
    )

    return result