import os

from fastapi.testclient import TestClient

from agent.firestore_client import get_firestore_client
from web.main import app


AUTONOMOUS_CONTRACTOR_ID = "C002"
APPROVAL_CONTRACTOR_ID = "C003"


client = TestClient(app)


def require_firestore_emulator() -> None:
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

    if emulator_host != "127.0.0.1:8080":
        raise RuntimeError(
            "This test must run against the local Firestore emulator "
            "at 127.0.0.1:8080."
        )


def test_c002_taskmaster_api() -> None:
    response = client.post(
        f"/api/taskmaster/{AUTONOMOUS_CONTRACTOR_ID}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["workflow_status"] == "completed"
    assert data["execution_mode"] == "autonomous"
    assert data["contractor_id"] == "C002"
    assert data["contractor_name"] == "SafeBuild Services"
    assert data["readiness_status"] == "ATTENTION_REQUIRED"
    assert data["risk_level"] == "MEDIUM"
    assert data["approval_required"] is False

    assert data["verification"]["verified"] is True

    assert data["workflow_steps"]


def test_c003_taskmaster_api() -> None:
    response = client.post(
        f"/api/taskmaster/{APPROVAL_CONTRACTOR_ID}"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["workflow_status"]
        == "awaiting_human_approval"
    )

    assert (
        data["execution_mode"]
        == "human_approval"
    )

    assert data["contractor_id"] == "C003"
    assert data["contractor_name"] == "ABC Construction"
    assert data["readiness_status"] == "NOT_READY"
    assert data["risk_level"] == "HIGH"
    assert data["approval_required"] is True

    assert data["approval_reasons"]

    assert data["approval"]["approval_id"]
    assert data["approval"]["status"] == "pending"

    # The approval boundary must remain intact.
    # The Taskmaster proposal must not create actions.
    db = get_firestore_client()

    actions = [
        document.to_dict()
        for document in db.collection(
            "followup_actions"
        ).stream()
        if document.to_dict().get("contractor_id")
        == APPROVAL_CONTRACTOR_ID
    ]

    assert len(actions) == 0


def test_taskmaster_api_health_contract() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "siteready-ai"


if __name__ == "__main__":
    require_firestore_emulator()

    test_c002_taskmaster_api()
    test_c003_taskmaster_api()
    test_taskmaster_api_health_contract()

    print()
    print("==========================================")
    print("TASKMASTER API REGRESSION TEST PASSED")
    print("==========================================")
    print("C002 API workflow: autonomous ✅")
    print("C003 API workflow: approval required ✅")
    print("C003 actions before approval: 0 ✅")
    print("Health endpoint: verified ✅")
    print("==========================================")