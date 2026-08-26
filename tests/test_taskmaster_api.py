from fastapi.testclient import TestClient

from web.main import app


AUTONOMOUS_CONTRACTOR_ID = "C002"
APPROVAL_CONTRACTOR_ID = "C003"


client = TestClient(app)


def test_c002_taskmaster_api(clean_taskmaster_state) -> None:
    """
    C002 must execute autonomously.

    Expected:
    - HTTP 200
    - workflow completes
    - execution mode is autonomous
    - approval is not required
    - verification succeeds
    """
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


def test_c003_taskmaster_api(clean_taskmaster_state) -> None:
    """
    C003 must stop at the human-approval boundary.

    Expected:
    - HTTP 200
    - workflow awaits human approval
    - approval is required
    - approval record is pending
    - no follow-up actions exist before approval
    """
    db = clean_taskmaster_state

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

    # Approval boundary:
    # Taskmaster must propose actions but must not create them
    # before human approval.
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
    """
    Verify the public health contract.
    """
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "siteready-ai"