import json
import os
from pathlib import Path

from google.cloud import firestore


# Project and folder locations
DEFAULT_PROJECT_ID = "siteready-ai-506306"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# JSON files → Firestore collections
DATASETS = {
    "contractors.json": "contractors",
    "documents.json": "documents",
    "training_records.json": "training_records",
    "inspections.json": "inspections",
    "corrective_actions.json": "corrective_actions",
    "readiness_rules.json": "readiness_rules",
}


def load_json(filename: str) -> list[dict]:
    """Load a JSON dataset from the data folder."""
    file_path = DATA_DIR / filename

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"{filename} must contain a JSON array.")

    return data


def seed_collection(
    db: firestore.Client,
    filename: str,
    collection_name: str,
    id_field: str,
) -> int:
    """Load one JSON dataset into one Firestore collection."""
    records = load_json(filename)
    collection_ref = db.collection(collection_name)

    written = 0

    for record in records:
        document_id = record.get(id_field)

        if not document_id:
            raise ValueError(
                f"{filename}: missing required ID field '{id_field}'."
            )

        collection_ref.document(str(document_id)).set(record)
        written += 1

    print(f"✓ {collection_name}: {written} records written")
    return written


def main() -> None:
    """Seed all synthetic datasets into Firestore."""
    project_id = (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCLOUD_PROJECT")
        or DEFAULT_PROJECT_ID
    )

    print("Starting SiteReady AI Firestore seed...")
    print(f"Project: {project_id}")
    print()

    db = firestore.Client(project=project_id)

    seed_collection(
        db,
        "contractors.json",
        "contractors",
        "contractor_id",
    )

    seed_collection(
        db,
        "documents.json",
        "documents",
        "document_id",
    )

    seed_collection(
        db,
        "training_records.json",
        "training_records",
        "training_id",
    )

    seed_collection(
        db,
        "inspections.json",
        "inspections",
        "inspection_id",
    )

    seed_collection(
        db,
        "corrective_actions.json",
        "corrective_actions",
        "action_id",
    )

    seed_collection(
        db,
        "readiness_rules.json",
        "readiness_rules",
        "rule_id",
    )

    print()
    print("✓ SiteReady AI Firestore seed completed successfully.")


if __name__ == "__main__":
    main()
