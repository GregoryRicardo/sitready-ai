# SiteReady AI — Judge Evidence Matrix

This document is a fast navigation map for judges and reviewers. Each major competition claim is paired with a concrete repository location or validated evidence.

## 1. Agent / AI Technology

| Claim | Evidence | Where to inspect |
|---|---|---|
| Gemini 3.5 Flash is the configured model | `MODEL = "gemini-3.5-flash"` and `Gemini(model=MODEL)` | `app/agent.py` |
| Google ADK is the agent framework | `Agent` + `Gemini` imports and `root_agent = Agent(...)` | `app/agent.py` |
| ADK/Gemini dependencies are declared | `google-adk[gcp]` dependency | `pyproject.toml` |
| Direct ADK/Gemini execution path exists | `Runner` executes `root_agent` | `run_agent.py` |
| Production Taskmaster requests are routed through ADK/Gemini | FastAPI delegates to `run_taskmaster_via_adk`, which captures the authoritative Taskmaster tool result | `web/main.py`, `app/adk_taskmaster.py` |

## 2. Agentic Workflow

| Claim | Evidence | Where to inspect |
|---|---|---|
| Multi-step readiness workflow | Assessment → comparison → explanation → execution policy → execution/approval → verification | `agent/tools/taskmaster_tools.py` |
| Execution policy is explicit | HIGH risk or CRITICAL issue requires human approval | `agent/tools/taskmaster_tools.py` |
| Autonomous path exists | Routine permitted work calls the follow-up action engine | `agent/tools/taskmaster_tools.py` |
| Verification is required before completion | Returned actions must have follow-up IDs and status `open` | `agent/tools/taskmaster_tools.py` |
| Consequential work is not executed automatically | HIGH/CRITICAL path returns `awaiting_human_approval` and creates a pending proposal | `agent/tools/taskmaster_tools.py` |
| Notification/escalation layer exists | Human-attention item → notification event → scheduled escalation → triggered escalation | `agent/tools/taskmaster_tools.py`, `agent/tools/notification_tools.py` |

## 3. Human Governance

| Claim | Evidence | Where to inspect |
|---|---|---|
| Approval is a first-class workflow state | `workflow_status = awaiting_human_approval` | `agent/tools/taskmaster_tools.py` |
| Pending approval is surfaced to the user | Approval ID and pending state are returned to the API | `agent/tools/taskmaster_tools.py`, `web/main.py` |
| Approval endpoint is explicit | `POST /api/approve/{approval_id}` | `web/main.py` |
| Approval requires exact approval identity | Agent instructions prohibit guessing or reusing an approval ID | `app/agent.py` |
| Actions are not created before approval | C003 tests assert zero actions before approval | `tests/test_taskmaster_api.py`, `tests/test_taskmaster_workflow.py` |
| Human attention resolves after approval | Approval tool updates `human_attention` to `resolved` with resolver identity | `agent/tools/followup_approval_tools.py`, `agent/tools/human_attention_tools.py` |

## 4. Notification / Escalation Evidence

| Claim | Evidence | Where to inspect |
|---|---|---|
| Human notification is persisted | Email notification event is stored with notification ID, recipient roles, timestamp, approval ID and message | `agent/tools/notification_tools.py` |
| Escalation is scheduled | WhatsApp demo event persists `status=scheduled` and `escalation_due_at` | `agent/tools/notification_tools.py` |
| Configured demo window is 60 seconds | Taskmaster uses `DEMO_ESCALATION_DELAY_SECONDS = 60` and tests verify the persisted deadline | `agent/tools/taskmaster_tools.py`, `tests/test_notifications.py` |
| Due escalation transitions automatically in the application flow | Due scheduled event is reconciled when the notification log is read/polled | `agent/tools/notification_tools.py`, `web/templates/index.html` |
| Escalation is auditable | Triggered event stores `triggered_at`, reason and final status | `agent/tools/notification_tools.py` |
| External WhatsApp delivery is not falsely claimed | Demo event explicitly states no external WhatsApp message was sent | `agent/tools/notification_tools.py`, `tests/test_notifications.py` |

Important evidence discipline: the current WhatsApp and email notification channels are **demo simulations / audit events**, not proof of external delivery.

## 5. Production Cloud Architecture

| Claim | Evidence | Where to inspect |
|---|---|---|
| Production API is hosted on Cloud Run | Production service and URL are documented | `README.md`, `docs/HACKATHON_VALIDATION.md` |
| FastAPI exposes the Taskmaster API | `/api/taskmaster/{contractor_id}` | `web/main.py` |
| Web Taskmaster route delegates through ADK | `/api/taskmaster/{contractor_id}` awaits `run_taskmaster_via_adk` | `web/main.py`, `app/adk_taskmaster.py` |
| Firestore is the persistence layer | Firestore client and agent tools use persisted collections | `agent/firestore_client.py`, `agent/` |
| Local/cloud environment separation is hardened | Local requires emulator; cloud rejects emulator configuration | `agent/firestore_client.py` |

## 6. Production Scenario Evidence

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

After explicit approval, five production follow-up actions were confirmed as `open` with `high` priority:

```text
DOC007
INS003
DOC008
TR009
CA002
```

### C003 — local demo escalation evidence

The local emulator demonstration validates:

```text
EMAIL     = SIMULATED
WHATSAPP  = DEMO — SCHEDULED
countdown = 60 seconds
then      = DEMO — ESCALATION TRIGGERED
```

This is **demo evidence**, not production proof of external WhatsApp delivery.

## 7. Idempotency Evidence

A repeat production approval scenario with existing open C003 actions returned:

```text
created   = false
duplicate = true
```

This demonstrates duplicate protection for consequential follow-up actions.

## 8. Automated Test Evidence

The repository contains a shared pytest fixture that:

- requires `FIRESTORE_EMULATOR_HOST` for local tests;
- requires `SITEREADY_ENV=local`;
- seeds deterministic baseline datasets once per session;
- verifies C002 and C003 exist;
- clears generated Taskmaster actions, approvals, human-attention records and notification events for isolated tests.

Primary fixture:

`tests/conftest.py`

Relevant test files include:

```text
tests/test_readiness.py
tests/test_audit_and_explanation.py
tests/test_change_detection.py
tests/test_end_to_end_readiness.py
tests/test_followup_approval.py
tests/test_taskmaster_api.py
tests/test_taskmaster_workflow.py
tests/test_human_attention.py
tests/test_notifications.py
```

Current local regression checkpoint:

```text
15 passed
```

## 9. Judge-Facing UI Evidence

The web interface exposes the workflow rather than only the final result.

Visible elements include:

```text
Taskmaster Agent
ASSESS → COMPARE → EXPLAIN → DECIDE → ACT / APPROVE → VERIFY

Agent Activity
✓ completed stages
⚡ autonomous execution
🛑 approval required
⏳ pending approval

Notification & Escalation Log
EMAIL → SIMULATED
WHATSAPP → DEMO — SCHEDULED → DEMO — ESCALATION TRIGGERED

Escalation monitor
Escalation in 60s
```

The UI also identifies the technology stack:

```text
Powered by Google ADK · Gemini 3.5 Flash · Google Cloud
```

Implementation locations:

- `web/templates/index.html`
- `web/static/app.js`
- `web/static/style.css`
- `web/main.py`

## 10. Competition Navigation

Start here when reviewing the repository:

1. `README.md` — product, architecture, production scenarios, API, and demo flow.
2. `docs/COMPETITION_PROOF.md` — consolidated competition evidence.
3. `docs/HACKATHON_VALIDATION.md` — production validation record.
4. `docs/JUDGE_EVIDENCE_MATRIX.md` — claim-to-code traceability.
5. `app/agent.py` — Gemini + ADK implementation.
6. `app/adk_taskmaster.py` — web-to-ADK bridge and structured tool-result capture.
7. `run_agent.py` — direct ADK/Gemini runner.
8. `agent/tools/taskmaster_tools.py` — Taskmaster workflow and policy boundary.
9. `agent/tools/notification_tools.py` — notification/escalation audit layer.
10. `web/main.py` — production API boundary.
11. `tests/` — automated regression evidence.
12. `web/` — judge-facing interface.

## 11. Evidence Discipline

The competition submission should distinguish clearly between:

- **implemented in code** — repository evidence;
- **validated locally** — automated and live local evidence;
- **validated in production** — Cloud Run + Firestore execution evidence;
- **demonstrated in the video** — judge-facing visual evidence.

Do not claim that Gemini itself directly performs deterministic database writes or safety-rule evaluation. The defensible architecture is: Gemini provides the model reasoning and tool-orchestration layer through Google ADK, while SiteReady tools and the Taskmaster policy control evidence access, execution boundaries, persistence, approval, escalation, and verification.

For the current production web path, the UI request is routed through the ADK/Gemini bridge. The bridge instructs Gemini to use the authoritative `run_taskmaster_workflow` tool and returns that tool's structured result to FastAPI. The Taskmaster tool remains the deterministic control plane for consequential execution and persistence.

Be explicit that the email and WhatsApp notification records are demo simulation/audit events rather than external delivery proof.
