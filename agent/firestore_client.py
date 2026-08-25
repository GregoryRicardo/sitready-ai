import os

from google.cloud import firestore


DEFAULT_PROJECT_ID = "sitready-ai-506306"


def get_firestore_client() -> firestore.Client:
    """
    Return the Firestore client for the current SiteReady environment.

    local:
        Requires FIRESTORE_EMULATOR_HOST so local development cannot
        accidentally connect to production Firestore.

    cloud:
        Uses real Google Cloud Firestore and explicitly rejects the
        emulator setting.

    Any unsupported environment fails fast.
    """

    project_id = os.getenv(
        "GOOGLE_CLOUD_PROJECT",
        DEFAULT_PROJECT_ID,
    )

    environment = os.getenv(
        "SITEREADY_ENV",
        "local",
    ).strip().lower()

    emulator_host = os.getenv(
        "FIRESTORE_EMULATOR_HOST"
    )

    if environment == "local":
        if not emulator_host:
            raise RuntimeError(
                "SITEREADY_ENV is set to 'local', but "
                "FIRESTORE_EMULATOR_HOST is not set. "
                "Start the local Firestore emulator first."
            )

        return firestore.Client(
            project=project_id,
        )

    if environment == "cloud":
        if emulator_host:
            raise RuntimeError(
                "SITEREADY_ENV is set to 'cloud', but "
                "FIRESTORE_EMULATOR_HOST is still set. "
                "Remove the emulator variable before using "
                "Cloud Firestore."
            )

        return firestore.Client(
            project=project_id,
        )

    raise RuntimeError(
        f"Unsupported SITEREADY_ENV '{environment}'. "
        "Expected 'local' or 'cloud'."
    )