import os

from google.cloud import firestore


PROJECT_ID = "sitready-ai-506306"


def get_firestore_client() -> firestore.Client:
    """
    Create a Firestore client for the local emulator.

    The emulator environment variable is required during local development
    so we don't accidentally connect to production Firestore.
    """
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

    if not emulator_host:
        raise RuntimeError(
            "FIRESTORE_EMULATOR_HOST is not set. "
            "The local Firestore emulator must be running."
        )

    return firestore.Client(project=PROJECT_ID)


def get_contractor(contractor_id: str) -> dict:
    """
    Retrieve one contractor from Firestore.

    Args:
        contractor_id: Firestore contractor document ID, e.g. C001.

    Returns:
        A dictionary containing the contractor data.

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

    contractor = document.to_dict()

    return {
        "contractor_id": document.id,
        **contractor,
    }


if __name__ == "__main__":
    contractor = get_contractor("C001")
    print(contractor)