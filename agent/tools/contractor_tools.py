from agent.firestore_client import get_firestore_client


def get_contractor(contractor_id: str) -> dict:
    """
    Retrieve one contractor from Firestore.

    Args:
        contractor_id: Firestore contractor document ID, e.g. C001.

    Returns:
        Contractor data as a dictionary.

    Raises:
        ValueError: If contractor_id is empty.
        LookupError: If the contractor does not exist.
    """
    if not contractor_id or not contractor_id.strip():
        raise ValueError("contractor_id is required.")

    contractor_id = contractor_id.strip().upper()

    db = get_firestore_client()

    document = (
        db.collection("contractors")
        .document(contractor_id)
        .get()
    )

    if not document.exists:
        raise LookupError(
            f"Contractor '{contractor_id}' was not found."
        )

    return {
        "contractor_id": document.id,
        **document.to_dict(),
    }


if __name__ == "__main__":
    print(get_contractor("C001"))