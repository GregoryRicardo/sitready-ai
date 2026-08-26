import os

import pytest
from google.cloud import firestore

from agent.firestore_client import get_firestore_client
from scripts.seed_firestore import seed_collection


PROJECT_ID = "sitready-ai-506306"


@pytest.fixture(scope="session", autouse=True)
def prepare_firestore_test_data():
    """Prepare deterministic baseline data once for the pytest session."""
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

    if not emulator_host:
        raise RuntimeError(
            "FIRESTORE_EMULATOR_HOST is not set. Start the local Firestore emulator before running tests."
        )

    environment = os.getenv("SITEREADY_ENV", "local").strip().lower()
    if environment != "local":
        raise RuntimeError(f"SITEREADY_ENV must be 'local' for tests, got '{environment}'.")

    print()
    print("=== SiteReady pytest Firestore setup ===")
    print(f"Project: {PROJECT_ID}")
    print(f"Emulator: {emulator_host}")

    db = firestore.Client(project=PROJECT_ID, database="(default)")

    seed_collection(db, "contractors.json", "contractors", "contractor_id")
    seed_collection(db, "documents.json", "documents", "document_id")
    seed_collection(db, "training_records.json", "training_records", "training_id")
    seed_collection(db, "inspections.json", "inspections", "inspection_id")
    seed_collection(db, "corrective_actions.json", "corrective_actions", "action_id")
    seed_collection(db, "readiness_rules.json", "readiness_rules", "rule_id")

    c002 = db.collection("contractors").document("C002").get()
    c003 = db.collection("contractors").document("C003").get()

    if not c002.exists or not c003.exists:
        raise RuntimeError("Firestore test setup completed, but C002/C003 could not be read back from the emulator.")

    print("✓ C002 verified")
    print("✓ C003 verified")
    print("✓ Firestore test data ready")
    print("========================================")
    print()


def _clear_taskmaster_state(db, contractor_ids: set[str]) -> None:
    """Remove generated Taskmaster state for the supplied contractors."""
    for collection_name in (
        "followup_actions",
        "followup_approvals",
        "human_attention",
        "notification_events",
    ):
        documents = db.collection(collection_name).stream()

        for document in documents:
            data = document.to_dict() or {}
            if data.get("contractor_id") in contractor_ids:
                document.reference.delete()


@pytest.fixture
def db():
    """Provide a Firestore client connected to the local emulator."""
    return get_firestore_client()


@pytest.fixture
def clean_taskmaster_state(db):
    """Provide a clean Taskmaster state for C002/C003 tests."""
    contractor_ids = {"C002", "C003"}
    _clear_taskmaster_state(db, contractor_ids)
    return db
