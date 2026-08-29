# SiteReady AI

**Autonomous contractor-readiness agent for Health & Safety and SHEQ teams.**

SiteReady AI turns contractor-readiness evidence into a controlled, action-oriented workflow. It assesses readiness, compares historical state, explains identified issues, determines whether work may execute autonomously, creates a human-approval gate for consequential work, and verifies the resulting actions.

## Hackathon positioning

**Track:** Taskmaster  
**Google Agent Framework:** Google ADK  
**Gemini model:** `gemini-3.5-flash`  
**Google Cloud:** Cloud Run + Cloud Firestore

The repository contains a Google ADK `Agent` configured with `Gemini(model="gemini-3.5-flash")`. The direct ADK/Gemini runner is `run_agent.py`.

The production web console now invokes the Taskmaster workflow through an ADK/Gemini bridge. Gemini selects the authoritative `run_taskmaster_workflow` tool, while SiteReady tools and Taskmaster policy control evidence, execution boundaries, persistence, approval, escalation and verification.

## What SiteReady does

A contractor readiness request follows this workflow:

```text
Contractor ID
    ↓
Readiness assessment + audit
    ↓
Historical comparison
    ↓
Evidence-backed explanation
    ↓
Execution policy
    ├── Routine / permitted work → autonomous execution
    │                              ↓
    │                           verification
    │
    └── HIGH risk or CRITICAL issue
                                   ↓
                          human approval required
                                   ↓
                              approval gate
                                   ↓
                           action creation
                                   ↓
                              verification
```

For consequential work, the human-governance layer also provides:

```text
Human attention
    ↓
Notification audit event
    ↓
60-second+ demo escalation schedule
    ↓
DEMO — ESCALATION TRIGGERED
    ↓
Human approval
    ↓
Action creation
    ↓
Verification
```

For the current judge demo build, the configured demo escalation window is **60 seconds**. The UI displays the persisted countdown and automatically reconciles the due event through the notification polling path.

The system is designed around **controlled autonomy** rather than unrestricted automation.

## Validated production scenarios

### C002 — autonomous execution

The live Cloud Run Taskmaster endpoint was validated with contractor `C002` and returned:

- `workflow_status`: `completed`
- `execution_mode`: `autonomous`
- `approval_required`: `False`

Firestore verification confirmed two open follow-up actions created by the autonomous Taskmaster workflow.

### C003 — human approval

The live Taskmaster endpoint was validated with contractor `C003` and returned:

- `workflow_status`: `awaiting_human_approval`
- `execution_mode`: `human_approval`
- `readiness_status`: `NOT_READY`
- `risk_level`: `HIGH`
- `approval_required`: `True`

Five critical issues were identified. The workflow created a pending approval and did not create C003 follow-up actions before approval.

An identical repeat request returned the existing pending approval instead of creating a duplicate approval.

After explicit approval through the production approval endpoint, five C003 follow-up actions were created and verified as `open`.

## Architecture

### Production web path

```text
User / UI
    ↓
Cloud Run / FastAPI
    ↓
ADK Agent
    ↓
Gemini 3.6 Flash
    ↓
run_taskmaster_workflow tool
    ↓
Taskmaster policy + SiteReady tools
    ↓
Human attention / autonomous action
    ↓
Firestore + verification
```

The ADK agent exposes `run_taskmaster_workflow` as an authoritative tool. Gemini provides the model reasoning/orchestration layer; the deterministic Taskmaster workflow remains responsible for policy, persistence, approval boundaries, notification state, escalation, and verification.

### Direct ADK/Gemini path

```text
User prompt
    ↓
Google ADK Agent
    ↓
Gemini 3.6 Flash
    ↓
SiteReady tools
    ↓
Taskmaster workflow
```

This direct path is exercised by `run_agent.py` and provides a separate, judge-visible proof of the ADK/Gemini integration.

## Firestore data model

Production validation covered these datasets:

| Collection | Records |
|---|---:|
| `contractors` | 3 |
| `documents` | 9 |
| `training_records` | 9 |
| `inspections` | 3 |
| `corrective_actions` | 2 |
| `readiness_rules` | 9 |

Runtime workflow state is persisted in collections including `followup_approvals`, `followup_actions`, `human_attention`, and `notification_events`.

## Key agent capabilities

- Contractor lookup
- Readiness assessment
- Audited readiness assessment
- Evidence-backed explanations
- Historical change detection
- Follow-up action proposals
- Human approval for consequential work
- Autonomous execution for permitted routine work
- Human-attention notification audit trail
- Demo escalation workflow
- Duplicate protection for pending approvals and open actions
- Execution verification

The agent is instructed not to invent contractor information, action IDs, approval IDs, execution status, or verification results.

## Production API

**Cloud Run service:** `sitready-ai`  
**Region:** `africa-south1`

Base URL:

`https://sitready-ai-176096390035.africa-south1.run.app`

Key endpoints:

```text
GET  /health
POST /api/assess/{contractor_id}
POST /api/explain/{contractor_id}
POST /api/compare/{contractor_id}
POST /api/propose/{contractor_id}
POST /api/taskmaster/{contractor_id}
POST /api/approve/{approval_id}
GET  /api/notifications?approval_id={approval_id}
```

The notification API exposes auditable demo notification events. The current email and WhatsApp channels are simulation/audit events; they are not claims of external delivery.

## Local development

The repository includes a `Procfile` that starts the FastAPI application with Uvicorn:

```text
web: python -m uvicorn web.main:app --host 0.0.0.0 --port $PORT
```

A local ADK runner is also provided in `run_agent.py` for exercising the agent directly.

### Environment

The deployed Cloud Run service uses:

```text
SITEREADY_ENV=cloud
GOOGLE_CLOUD_PROJECT=sitready-ai-506306
```

For local Google Cloud access, authenticate with your Google account and configure the project:

```powershell
gcloud auth login
gcloud config set project siteready-ai-506306
```

Use Google Application Default Credentials when running the Python Google Cloud clients locally.

## Firestore seeding

The canonical repository seeding script is:

```text
scripts/seed_firestore.py
```

It maps the six JSON datasets in `data/` to the production Firestore collections using deterministic document IDs.

During production troubleshooting, a temporary Firestore REST-based seeding path was used because the Python Firestore write path intermittently returned `CONSUMER_INVALID`. The deployed application itself was validated independently through Cloud Run and Firestore.

## Demo flow

For a concise Taskmaster demonstration:

1. Run the Taskmaster workflow for `C002` and show autonomous completion plus verification.
2. Run the Taskmaster workflow for `C003` and show `awaiting_human_approval` and the human-attention boundary.
3. Show the notification audit log and the **60-second demo escalation countdown**.
4. Let the countdown reach zero and show `DEMO — ESCALATION TRIGGERED` without pressing an escalation button.
5. Show the pending approval ID and confirm no C003 actions exist before approval.
6. Approve the exact approval ID through `/api/approve/{approval_id}`.
7. Show the five C003 actions created and human attention resolved.
8. Briefly demonstrate duplicate protection by repeating the C003 workflow request.
9. Run `run_agent.py` when a direct ADK/Gemini proof is useful during judging.

This demonstrates the core product principle: **the agent reasons and orchestrates through Gemini/ADK, acts autonomously where policy permits, and stops for human control where the work is consequential.**

## Validation record

Detailed production validation notes are maintained in:

`docs/HACKATHON_VALIDATION.md`

Current local regression checkpoint:

```text
15 passed
```

## Repository structure

```text
app/                  Agent definition and application package
agent/                Agent tools, workflow, Firestore client and Taskmaster logic
data/                 Synthetic readiness datasets
scripts/              Data seeding utilities
web/                  FastAPI web application and UI
run_agent.py          Direct Google ADK/Gemini runner
Procfile              Cloud Run / Uvicorn process definition
```

## Security notes

- Do not commit OAuth tokens, service-account keys, or other secrets.
- Use Google Cloud IAM and Application Default Credentials for server-side access.
- The approval workflow requires an explicit approval ID before consequential follow-up actions are created.
