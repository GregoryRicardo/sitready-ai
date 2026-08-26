import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from agent.tools.audited_readiness_tools import assess_contractor_readiness_with_audit
from agent.tools.change_detection_tools import compare_contractor_assessments
from agent.tools.explanation_tools import explain_contractor_readiness
from agent.tools.followup_approval_tools import approve_followup_actions, propose_followup_actions
from agent.tools.human_attention_tools import list_open_human_attention
from agent.tools.taskmaster_tools import run_taskmaster_workflow


app = FastAPI(
    title="SiteReady AI",
    description="Contractor readiness Taskmaster console",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="web/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    with open("web/templates/index.html", "r", encoding="utf-8") as file:
        return HTMLResponse(file.read())


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "siteready-ai",
        "environment": os.getenv("SITEREADY_ENV", "local"),
    }


@app.post("/api/assess/{contractor_id}")
def assess(contractor_id: str) -> dict:
    return assess_contractor_readiness_with_audit(contractor_id)


@app.post("/api/explain/{contractor_id}")
def explain(contractor_id: str) -> dict:
    return explain_contractor_readiness(contractor_id)


@app.post("/api/compare/{contractor_id}")
def compare(contractor_id: str) -> dict:
    return compare_contractor_assessments(contractor_id)


@app.post("/api/propose/{contractor_id}")
def propose(contractor_id: str) -> dict:
    return propose_followup_actions(contractor_id)


@app.post("/api/taskmaster/{contractor_id}")
def taskmaster(contractor_id: str) -> dict:
    return run_taskmaster_workflow(contractor_id)


@app.get("/api/attention")
def attention(contractor_id: str | None = None) -> dict:
    return {
        "items": list_open_human_attention(contractor_id),
    }


@app.post("/api/approve/{approval_id}")
def approve(approval_id: str, approved_by: str = "web_demo_user") -> dict:
    return approve_followup_actions(
        approval_id=approval_id,
        approved_by=approved_by,
    )
