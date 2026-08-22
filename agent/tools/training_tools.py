from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client


def get_training_records(contractor_id: str) -> list[dict]:
    """
    Retrieve all training records belonging to a contractor.

    Args:
        contractor_id: Firestore contractor ID, e.g. C003.

    Returns:
        A list of training records.
    """
    if not contractor_id or not contractor_id.strip():
        raise ValueError("contractor_id is required.")

    contractor_id = contractor_id.strip().upper()

    db = get_firestore_client()

    query = db.collection("training_records").where(
        filter=FieldFilter("contractor_id", "==", contractor_id)
    )

    records = []

    for document in query.stream():
        records.append(
            {
                "training_id": document.id,
                **document.to_dict(),
            }
        )

    records.sort(key=lambda item: item["training_id"])

    return records


if __name__ == "__main__":
    results = get_training_records("C001")

    for record in results:
        print(record)