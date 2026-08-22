from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client


def get_documents(contractor_id: str) -> list[dict]:
    """
    Retrieve all documents belonging to a contractor.

    Args:
        contractor_id: Firestore contractor ID, e.g. C001.

    Returns:
        A list of document records.
    """
    if not contractor_id or not contractor_id.strip():
        raise ValueError("contractor_id is required.")

    contractor_id = contractor_id.strip().upper()

    db = get_firestore_client()

    query = db.collection("documents").where(
        filter=FieldFilter("contractor_id", "==", contractor_id)
    )

    documents = []

    for document in query.stream():
        documents.append(
            {
                "document_id": document.id,
                **document.to_dict(),
            }
        )

    documents.sort(key=lambda item: item["document_id"])

    return documents


if __name__ == "__main__":
    results = get_documents("C001")

    for document in results:
        print(document)