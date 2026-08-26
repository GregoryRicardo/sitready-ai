# SiteReady AI — Judge Evidence Matrix

This document is a fast navigation map for judges and reviewers. Each major competition claim is paired with a concrete repository location or validated production evidence.

## 1. Agent / AI Technology

| Claim | Evidence | Where to inspect |
|---|---|---|
| Gemini 3.6 Flash is the configured model | `MODEL = "gemini-3.6-flash"` and `Gemini(model=MODEL)` | `app/agent.py` |
| Google ADK is the agent framework | `from google.adk.agents import Agent` and `from google.adk.models import Gemini` | `app/agent.py` |
| ADK/Gemini dependencies are declared | `google-adk[gcp]` dependency | `pyproject.toml` |
| SiteReady root agent exposes domain tools | `root_agent = Agent(...)` with SiteReady tools | `app/agent.py` |

## 2. Agentic Workflow

| Claim | Evidence | Where to inspect |
|---|---|---|
| Multi-step readiness workflow | Assessment → comparison → explanation → execution policy → execution/approval → verification | `agent/tools/taskmaster_tools.py` |
| Execution policy is explicit | HIGH risk or CRITICAL issue requires human approval | `agent/tools/taskmaster_tools.py` |
| Autonomous path exists | Routine permitted work calls the follow-up action engine | `agent/tools/taskmaster_tools.py` |
| Verification is required before completion | Returned actions must have follow-up IDs and status `open` | `agent/tools/taskmaster_tools.py` |
| Consequential work is not executed automatically | HIGH/CRITICAL path returns `awaiting_human_approval` and creates a pending proposal | `agent/tools/taskmaster_tools.py` |

## 3. Human Governance

| Claim | Evidence | Where to inspect |
|---|---|---|
| Approval is a first-class workflow state | `workflow_status = awaiting_human_approval` | `agent/tools/taskmaster_tools.py` |
| Pending approval is surfaced to the user | Approval ID and pending state are returned to the API | `agent/tools/taskmaster_tools.py`, `web/main.py` |
| Approval endpoint is explicit | `POST /api/approve/{approval_id}` | `web/main.py` |
| Approval requires exact approval identity | The root agent instructions prohibit guessing or reusing an approval ID | `app/agent.py` |
| Actions are not created before approval | Test asserts zero C003 actions before approval | `tests/test_taskmaster_api.py` |

## 4. Production Cloud Architecture

| Claim | Evidence | Where to inspect |
|---|---|---|
| Production API is hosted on Cloud Run | Production service and URL are documented | `README.md`, `docs/HACKATHON_VALIDATION.md` |
| FastAPI exposes the Taskmaster API | `/api/taskmaster/{contractor_id}` | `web/main.py` |
| Firestore is the persistence layer | Firestore client and collections are used by agent tools | `agent/firestore_client.py`, `agent/` |
| Local/cloud environment separation is hardened | Local requires emulator; cloud rejects emulator configuration | `agent/firestore_client.py` |

## 5. Production Scenario Evidence

### C002 — controlled autonomy

Validated production behavior:

```text
workflow_status   = completed
execution_mode    = autonomous
readiness_status  = ATTENTION_REQUIRED
risk_level        = MEDIUM
approval_required = false
verification      = true
```

Repository regression test:

`tests/test_taskmaster_api.py::test_c002_taskmaster_api`

### C003 — controlled human approval

Validated production behavior:

```text
workflow_status   = awaiting_human_approval
execution_mode    = human_approval
readiness_status  = NOT_READY
risk_level        = HIGH
approval_required = true
```

Before approval:

```text
C003 follow-up actions = 0
approval status        = pending
```

Repository regression test:

`tests/test_taskmaster_api.py::test_c003_taskmaster_api`

After explicit approval, five production follow-up actions were confirmed as `open` with `high` priority:

```text
DOC007
INS003
DOC008
TR009
CA002
```

## 6. Idempotency Evidence

A repeat production approval scenario with existing open C003 actions returned:

```text
created   = false
duplicate = true
```

This demonstrates duplicate protection for consequential follow-up actions.

## 7. Automated Test Evidence

The repository contains a shared pytest fixture that:

- requires `FIRESTORE_EMULATOR_HOST` for local tests;
- requires `SITEREADY_ENV=local`;
- seeds deterministic baseline datasets once per session;
- verifies C002 and C003 exist;
- clears generated Taskmaster actions/approvals for isolated tests.

Primary fixture:

`tests/conftest.py`

Relevant test files:

```text
tests/test_readiness.py
tests/test_audit_and_explanation.py
tests/test_change_detection.py
tests/test_end_to_end_readiness.py
tests/test_followup_approval.py
tests/test_phase12_end_to_end.py
tests/test_taskmaster_api.py
tests/test_taskmaster_workflow.py
```

Validated local result:

```text
11 passed
```

## 8. Judge-Facing UI Evidence

The web interface exposes the agent workflow rather than only the final result.

Visible elements include:

```text
Taskmaster Agent
ASSESS → COMPARE → EXPLAIN → DECIDE → ACT / APPROVE → VERIFY

Agent Activity
✓ completed stages
⚡ autonomous execution
🛑 approval required
⏳ pending approval
```

The UI also identifies the technology stack:

```text
Powered by Google ADK · Gemini 3.6 Flash · Google Cloud
```

Implementation locations:

- `web/templates/index.html`
- `web/static/app.js`
- `web/static/style.css`

## 9. Competition Navigation

Start here when reviewing the repository:

1. `README.md` — product, architecture, production scenarios, API, and demo flow.
2. `docs/COMPETITION_PROOF.md` — consolidated competition evidence.
3. `docs/HACKATHON_VALIDATION.md` — production validation record.
4. `docs/JUDGE_EVIDENCE_MATRIX.md` — claim-to-code traceability.
5. `app/agent.py` — Gemini + ADK implementation.
6. `agent/tools/taskmaster_tools.py` — Taskmaster workflow and policy boundary.
7. `web/main.py` — production API boundary.
8. `tests/` — automated regression evidence.
9. `web/` — judge-facing interface.

## 10. Evidence Discipline

The competition submission should distinguish clearly between:

- **implemented in code** — repository evidence;
- **validated locally** — automated test evidence;
- **validated in production** — Cloud Run + Firestore execution evidence;
- **demonstrated in the video** — judge-facing visual evidence.

Do not claim that Gemini itself directly performs deterministic database writes or safety-rule evaluation. The defensible architecture is: Gemini provides the model reasoning layer through Google ADK, while SiteReady tools and the Taskmaster policy control evidence access, execution boundaries, persistence, approval, and verification.
