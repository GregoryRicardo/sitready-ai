from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client


def get_inspections(contractor_id: str) -> list[dict]:
    """
    Retrieve inspection records belonging to a contractor.

    Args:
        contractor_id: Firestore contractor ID, e.g. C003.

    Returns:
        A list of inspection records.
    """
    if not contractor_id or not contractor_id.strip():
        raise ValueError("contractor_id is required.")

    contractor_id = contractor_id.strip().upper()

    db = get_firestore_client()

    query = db.collection("inspections").where(
        filter=FieldFilter("contractor_id", "==", contractor_id)
    )

    inspections = []

    for document in query.stream():
        inspections.append(
            {
                "inspection_id": document.id,
                **document.to_dict(),
            }
        )

    inspections.sort(key=lambda item: item["inspection_id"])

    return inspections


if __name__ == "__main__":
    results = get_inspections("C001")

    for inspection in results:
        print(inspection)