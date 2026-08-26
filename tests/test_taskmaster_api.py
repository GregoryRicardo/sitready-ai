from fastapi.testclient import TestClient

from web import main as web_main
from web.main import app


AUTONOMOUS_CONTRACTOR_ID = "C002"
APPROVAL_CONTRACTOR_ID = "C003"


client = TestClient(app)


def test_c002_taskmaster_api(clean_taskmaster_state, monkeypatch) -> None:
    """
    C002 must execute autonomously.

    The web route should delegate to the ADK bridge exactly once.
    """
    calls = []

    def fake_adk(contractor_id: str) -> dict:
        calls.append(contractor_id)
        return {
            "workflow_status": "completed",
            "execution_mode": "autonomous",
            "contractor_id": "C002",
            "contractor_name": "SafeBuild Services",
            "readiness_status": "ATTENTION_REQUIRED",
            "risk_level": "MEDIUM",
            "approval_required": False,
            "verification": {"verified": True},
            "workflow_steps": [{"step": "verification", "status": "completed"}],
        }

    async def fake_adk_async(contractor_id: str) -> dict:
        calls.append(contractor_id)
        return fake_adk(contractor_id)

    monkeypatch.setattr(web_main, "run_taskmaster_via_adk", fake_adk_async)

    response = client.post(
        f"/api/taskmaster/{AUTONOMOUS_CONTRACTOR_ID}"
    )

    assert response.status_code == 200

    data = response.json()

    assert calls == [AUTONOMOUS_CONTRACTOR_ID]
    assert data["workflow_status"] == "completed"
    assert data["execution_mode"] == "autonomous"
    assert data["contractor_id"] == "C002"
    assert data["contractor_name"] == "SafeBuild Services"
    assert data["readiness_status"] == "ATTENTION_REQUIRED"
    assert data["risk_level"] == "MEDIUM"
    assert data["approval_required"] is False
    assert data["verification"]["verified"] is True
    assert data["workflow_steps"]


def test_c003_taskmaster_api(clean_taskmaster_state, monkeypatch) -> None:
    """
    C003 must stop at the human-approval boundary.

    The web route delegates to ADK, while the returned Taskmaster result
    still exposes the existing approval contract to the UI.
    """
    calls = []

    async def fake_adk(contractor_id: str) -> dict:
        calls.append(contractor_id)
        return {
            "workflow_status": "awaiting_human_approval",
            "execution_mode": "human_approval",
            "contractor_id": "C003",
            "contractor_name": "ABC Construction",
            "readiness_status": "NOT_READY",
            "risk_level": "HIGH",
            "approval_required": True,
            "approval_reasons": ["HIGH risk requires human approval."],
            "approval": {"approval_id": "APR-TEST", "status": "pending"},
            "workflow_steps": [{"step": "human_approval", "status": "approval_required"}],
        }

    monkeypatch.setattr(web_main, "run_taskmaster_via_adk", fake_adk)

    response = client.post(
        f"/api/taskmaster/{APPROVAL_CONTRACTOR_ID}"
    )

    assert response.status_code == 200

    data = response.json()

    assert calls == [APPROVAL_CONTRACTOR_ID]
    assert data["workflow_status"] == "awaiting_human_approval"
    assert data["execution_mode"] == "human_approval"
    assert data["contractor_id"] == "C003"
    assert data["contractor_name"] == "ABC Construction"
    assert data["readiness_status"] == "NOT_READY"
    assert data["risk_level"] == "HIGH"
    assert data["approval_required"] is True
    assert data["approval_reasons"]
    assert data["approval"]["approval_id"] == "APR-TEST"
    assert data["approval"]["status"] == "pending"

    # This API test only validates routing/contract shape; the existing
    # Taskmaster workflow tests continue to prove the no-action-before-approval
    # boundary against the real Firestore-backed implementation.


def test_taskmaster_api_health_contract() -> None:
    """
    Verify the public health contract.
    """
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "siteready-ai"
