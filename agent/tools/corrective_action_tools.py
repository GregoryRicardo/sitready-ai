from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client


def get_corrective_actions(contractor_id: str) -> list[dict]:
    """
    Retrieve corrective actions associated with a contractor.

    Args:
        contractor_id: Firestore contractor ID, e.g. C003.

    Returns:
        A list of corrective action records.
    """
    if not contractor_id or not contractor_id.strip():
        raise ValueError("contractor_id is required.")

    contractor_id = contractor_id.strip().upper()

    db = get_firestore_client()

    query = db.collection("corrective_actions").where(
        filter=FieldFilter("contractor_id", "==", contractor_id)
    )

    actions = []

    for document in query.stream():
        actions.append(
            {
                "action_id": document.id,
                **document.to_dict(),
            }
        )

    actions.sort(key=lambda item: item["action_id"])

    return actions


if __name__ == "__main__":
    results = get_corrective_actions("C001")

    for action in results:
        print(action)