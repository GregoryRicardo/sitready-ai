import os

from google.cloud import firestore


PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "sitready-ai-506306")


def get_firestore_client() -> firestore.Client:
    """
    Create a Firestore client for local SiteReady AI development.

    The local emulator must be running so development code cannot
    accidentally connect to production Firestore.
    """
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

    if not emulator_host:
        raise RuntimeError(
            "FIRESTORE_EMULATOR_HOST is not set. "
            "Start the local Firestore emulator first."
        )

    return firestore.Client(project=PROJECT_ID)