import os

from google.cloud import firestore


PROJECT_ID = os.getenv(
    "GOOGLE_CLOUD_PROJECT",
    "sitready-ai-506306",
)

ENVIRONMENT = os.getenv(
    "SITEREADY_ENV",
    "local",
).lower()


def get_firestore_client() -> firestore.Client:
    """
    Return the Firestore client for the current SiteReady environment.

    local:
        Requires FIRESTORE_EMULATOR_HOST so local development cannot
        accidentally connect to production Firestore.

    cloud:
        Uses the real Google Cloud Firestore service.
    """

    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

    if ENVIRONMENT == "local":
        if not emulator_host:
            raise RuntimeError(
                "SITEREADY_ENV is set to 'local', but "
                "FIRESTORE_EMULATOR_HOST is not set. "
                "Start the local Firestore emulator first."
            )

        return firestore.Client(
            project=PROJECT_ID,
        )

    if ENVIRONMENT == "cloud":
        if emulator_host:
            raise RuntimeError(
                "SITEREADY_ENV is set to 'cloud', but "
                "FIRESTORE_EMULATOR_HOST is still set. "
                "Remove the emulator variable before using cloud Firestore."
            )

        return firestore.Client(
            project=PROJECT_ID,
        )

    raise RuntimeError(
        f"Unsupported SITEREADY_ENV '{ENVIRONMENT}'. "
        "Expected 'local' or 'cloud'."
    )