# SiteReady AI — Final Submission Evidence

**Submission track:** Taskmaster  
**Repository:** `https://github.com/GregoryRicardo/sitready-ai`  
**Primary branch:** `main`  
**Submission baseline commit:** `9bfa1e7`  
**Google Cloud project:** `siteready-ai-506306`  
**Google Cloud project number:** `176096390035`  
**Cloud Run service:** `sitready-ai`  
**Cloud Run region:** `africa-south1`  
**Production URL:** `https://sitready-ai-176096390035.africa-south1.run.app`  
**Configured model:** `gemini-3.5-flash`  
**Agent framework:** Google ADK  

---

## 1. Purpose

This document is the final evidence control sheet for the SiteReady AI hackathon submission.

It maps the major judge-facing claims to repository implementation, automated tests, live production validation, Firestore state, UI/demo evidence, and explicit claim limitations.

The goal is to keep the submission technically defensible and prevent accidental over-claiming.

## 2. Executive Evidence Summary

| Evidence area | Status | Primary proof |
|---|---|---|
| Google ADK integration | PASS | `app/agent.py`, `run_agent.py` |
| Gemini 3.5 Flash configured | PASS | `app/agent.py` |
| Web-to-ADK bridge | PASS | `web/main.py`, `app/adk_taskmaster.py` |
| Taskmaster workflow | PASS | `agent/tools/taskmaster_tools.py` |
| Google Cloud deployment | PASS | Cloud Run |
| Production health | PASS | `/health` → HTTP 200 |
| Firestore persistence | PASS | Production Firestore |
| C002 autonomous execution | PASS | Live production Taskmaster response |
| C002 verification | PASS | `verification.verified = true` |
| C003 human approval boundary | PASS | Live production Taskmaster response |
| C003 zero actions before approval | PASS for the fresh production approval state observed during validation | Direct production-state query before approval |
| C003 approval execution | PASS | Live production approval endpoint |
| C003 production actions | PASS | 5 open/high actions confirmed in production Firestore |
| Duplicate protection | PASS | Approval response returned `duplicate = true` for all five existing actions |
| Notification audit layer | PASS | Notification implementation + validation |
| Demo escalation | PASS — local demo | 60-second persisted countdown and reconciliation |
| Automated regression | PASS | 15 tests passed |
| Repository hygiene | PASS | No runtime artifacts/secrets tracked |
| Git synchronization | PASS | `main` synchronized with `origin/main` |

## 3. Google Technology Evidence

### 3.1 Gemini + Google ADK

**Claim:** SiteReady AI uses Google ADK with Gemini 3.5 Flash.

**Inspect:**

- `app/agent.py`
- `run_agent.py`
- `pyproject.toml`

**Key implementation evidence:**

```text
MODEL = "gemini-3.5-flash"
```

**Judge-facing proof:** show `app/agent.py` and, where appropriate, the direct `run_agent.py` path.

### 3.2 Production web path

**Claim:** Production Taskmaster requests are routed through the ADK/Gemini bridge.

**Inspect:**

- `web/main.py`
- `app/adk_taskmaster.py`
- `app/agent.py`

**Architecture:**

```text
User / UI
    |
    v
Cloud Run / FastAPI
    |
    v
Google ADK Agent
    |
    v
Gemini 3.5 Flash
    |
    v
run_taskmaster_workflow
    |
    v
Taskmaster policy + SiteReady tools
    |
    v
Firestore / actions / approval / verification
```

Gemini provides the model reasoning/orchestration layer. The deterministic Taskmaster workflow remains responsible for policy, persistence, approval boundaries, notification state, escalation, and verification.

## 4. Google Cloud Production Evidence

### 4.1 Cloud Run

**Claim:** SiteReady AI is deployed and running on Google Cloud Run.

```text
Service:  sitready-ai
Region:   africa-south1
URL:      https://sitready-ai-176096390035.africa-south1.run.app
```

**Validation command:**

```powershell
Invoke-WebRequest "https://sitready-ai-176096390035.africa-south1.run.app/health" -UseBasicParsing
```

**Observed result:**

```text
StatusCode        : 200
StatusDescription : OK
Content           : {"status":"ok","service":"siteready-ai","environment":"cloud"}
```

**Evidence status:** PASS.

### 4.2 Google Cloud project and IAM

```text
Project ID:     siteready-ai-506306
Project number: 176096390035
```

The active account was verified with Owner and Vertex AI user access for the project.

**Evidence status:** PASS.

## 5. Automated Regression Evidence

### 5.1 Full test suite

**Command:**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**Observed result:**

```text
15 passed, 1 warning
```

The warning is a non-blocking `DeprecationWarning` concerning `BaseAgentConfig`. No tests failed.

**Evidence status:** PASS.

**Judge proof:** show the terminal result with `15 passed`.

## 6. C002 — Controlled Autonomous Execution

### 6.1 Live production result

**Production request:**

```powershell
$r = Invoke-WebRequest "https://sitready-ai-176096390035.africa-south1.run.app/api/taskmaster/C002" -Method POST -UseBasicParsing
$r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 20
```

**Observed key result:**

```text
workflow_status   = completed
execution_mode    = autonomous
contractor_id     = C002
contractor_name   = SafeBuild Services
readiness_status  = ATTENTION_REQUIRED
risk_level        = MEDIUM
approval_required = false
```

Workflow stages included:

```text
assessment             = completed
historical_comparison  = completed
explanation            = completed
execution_policy       = autonomous_execution
followup_execution     = completed
execution_verification = completed
```

Verification returned:

```text
verified = true
```

Two existing open follow-up actions were detected as duplicates during the latest run, demonstrating idempotent behavior rather than creating duplicate actions.

**Evidence status:** PASS.

## 7. C003 — Human Approval Boundary

### 7.1 Live production assessment

**Production request:**

```powershell
$r = Invoke-WebRequest "https://sitready-ai-176096390035.africa-south1.run.app/api/taskmaster/C003" -Method POST -UseBasicParsing
$r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 20
```

**Observed result:**

```text
workflow_status   = awaiting_human_approval
execution_mode    = human_approval
contractor_id     = C003
readiness_status  = NOT_READY
risk_level        = HIGH
approval_required = true
```

Approval reasons:

```text
Contractor risk level is HIGH.
At least one readiness issue has critical severity.
```

### 7.2 Five readiness issues

| Reference | Issue |
|---|---|
| `DOC007` | Public Liability Certificate is expired |
| `DOC008` | Safety File is missing |
| `TR009` | working_at_height training is missing |
| `INS003` | site_safety inspection failed with 3 findings |
| `CA002` | High-priority corrective action is overdue |

All five were identified as critical-severity readiness issues in the live assessment.

### 7.3 Pending approval

The fresh production C003 workflow created:

```text
approval_id = APR-20260829060923041391
status      = pending
```

The Taskmaster response explicitly stated:

```text
No follow-up actions were created.
```

## 8. Zero Actions Before Approval

Before approving the fresh C003 production approval, production Firestore was queried with emulator mode disabled.

Observed:

```text
PRODUCTION C003 ACTION COUNT= 0
```

This is the evidence for the fresh approval state:

```text
C003
  |
  v
HIGH / NOT_READY
  |
  v
approval_required = true
  |
  v
pending approval
  |
  v
follow-up actions = 0
```

**Evidence discipline:** this zero-action result applied to the fresh approval state and was checked against production Firestore, not the local emulator.

## 9. C003 Approval and Production Actions

### 9.1 Approval endpoint

The production approval endpoint is:

```text
POST /api/approve/{approval_id}
```

For the fresh approval:

```text
APR-20260829060923041391
```

the response returned:

```text
approved = true
status   = approved
```

The approval response found the existing five actions as duplicates rather than creating a second set.

### 9.2 Current production Firestore state

Production Firestore was queried with:

```text
SITEREADY_ENV=cloud
FIRESTORE_EMULATOR_HOST unset
```

Observed:

```text
PRODUCTION C003 ACTION COUNT= 5
```

The five production actions are:

```text
FA-20260826091825062725  DOC007  open  high
FA-20260826091825294433  INS003  open  high
FA-20260826091825679016  DOC008  open  high
FA-20260826091825910633  TR009   open  high
FA-20260826091826121128  CA002   open  high
```

**Evidence status:** PASS.

## 10. Duplicate Protection / Idempotency

The production approval request for:

```text
APR-20260829060923041391
```

returned five action results with:

```text
created  = false
duplicate = true
status   = open
```

for the five existing C003 actions.

This demonstrates that repeated consequential approval execution does not blindly create duplicate open follow-up actions.

**Evidence status:** PASS.

## 11. Human Attention

The repository contains a dedicated human-attention layer.

**Inspect:**

- `agent/tools/human_attention_tools.py`
- `agent/tools/taskmaster_tools.py`
- `agent/tools/followup_approval_tools.py`
- `web/main.py`
- `web/templates/index.html`

**Important limitation:** a current production query for C003 returned:

```text
PRODUCTION C003 HUMAN ATTENTION COUNT= 0
```

Therefore this document does not claim that a current production `human_attention` record is presently persisted. The historical validation record and approval workflow evidence remain the basis for the broader human-attention feature claim.

## 12. Notification and Escalation Demo

The local emulator demonstration provides:

```text
Human attention required
        |
        v
EMAIL | SIMULATED
        |
        v
WHATSAPP | DEMO — SCHEDULED
        |
        v
60-second demo countdown
        |
        v
WHATSAPP | DEMO — ESCALATION TRIGGERED
```

The UI reconciles the persisted `escalation_due_at` timestamp through the notification polling/read path.

**Evidence status:** PASS — local demo.

### What is not claimed

The submission does not claim:

- external WhatsApp delivery;
- external email delivery;
- Cloud Scheduler execution;
- Cloud Tasks execution;
- a production background WhatsApp worker.

The notification records are demo simulation/audit events.

## 13. Evidence-to-Code Map

| Judge claim | Repository evidence |
|---|---|
| Gemini 3.5 Flash configured | `app/agent.py` |
| Google ADK agent | `app/agent.py` |
| Direct ADK runner | `run_agent.py` |
| Web-to-ADK bridge | `app/adk_taskmaster.py`, `web/main.py` |
| Taskmaster workflow | `agent/tools/taskmaster_tools.py` |
| Readiness assessment | `agent/tools/readiness_tools.py` |
| Historical comparison | `agent/tools/change_detection_tools.py` |
| Explanation | `agent/tools/explanation_tools.py` |
| Follow-up actions | `agent/tools/followup_action_tools.py` |
| Approval | `agent/tools/followup_approval_tools.py` |
| Human attention | `agent/tools/human_attention_tools.py` |
| Notifications | `agent/tools/notification_tools.py` |
| Firestore access | `agent/firestore_client.py` |
| Seeding | `scripts/seed_firestore.py` |
| API boundary | `web/main.py` |
| Judge UI | `web/templates/index.html`, `web/static/` |
| Regression evidence | `tests/` |

## 14. Recommended Four-Minute Demo

1. Introduce the contractor-readiness problem and SiteReady's goal.
2. Show the Taskmaster UI and briefly open the `i` explanation.
3. Run C002 and show autonomous completion plus verification.
4. Run C003 and show `NOT_READY / HIGH` plus the human-approval boundary.
5. Show the notification audit log and the 60-second demo escalation countdown.
6. Let the countdown reach zero and show `DEMO — ESCALATION TRIGGERED`.
7. Show the pending approval ID and confirm no C003 actions exist before approval.
8. Approve the exact approval ID and show the production follow-up actions.
9. Demonstrate duplicate protection.
10. Optionally run `run_agent.py` for direct ADK/Gemini proof.
11. Finish with the repository and Google Cloud production deployment.

## 15. Submission Screenshot / Recording Checklist

### Repository
- GitHub repository homepage
- `main` branch
- README
- `docs/`
- `app/`
- `agent/`
- `tests/`

### Google technology
- `app/agent.py` showing Gemini 3.5 Flash
- direct ADK runner where useful
- Cloud Run service

### Production
- Cloud Run `/health` HTTP 200
- C002 production Taskmaster response
- C003 production Taskmaster response
- fresh zero-action-before-approval proof
- approval response
- five C003 actions in production
- duplicate protection response

### Quality
- `15 passed`
- clean Git working tree
- synchronized `main`

### Demo
- Taskmaster Agent Activity
- human-approval boundary
- notification audit
- 60-second demo escalation
- approval
- resulting actions

## 16. Claims to Avoid

Do not state or imply that:

1. Gemini itself directly writes deterministic Firestore records.
2. Gemini itself evaluates the deterministic readiness rules.
3. WhatsApp messages are externally delivered.
4. Email messages are externally delivered.
5. The demo escalation is a Cloud Scheduler or Cloud Tasks worker.
6. A fresh approval that returned duplicates created five new actions.
7. Current production human-attention state is persisted unless directly verified at the time of the claim.
8. Autonomous execution happened unless the runtime returned `workflow_status = completed` and `execution_mode = autonomous`.

The defensible architecture is:

```text
Gemini / ADK
    =
reasoning + tool orchestration

Taskmaster / SiteReady tools
    =
deterministic evidence + policy + execution control + persistence + verification
```

## 17. Final Pre-Submission Gate

```text
[ ] Git working tree clean
[ ] main == origin/main
[ ] Gemini 3.5 references consistent
[ ] Gemini model references match the configured application model
[ ] No secrets tracked
[ ] No .venv tracked
[ ] No runtime logs tracked
[ ] README accurate
[ ] Competition proof accurate
[ ] Hackathon validation accurate
[ ] Judge evidence matrix accurate
[ ] 15/15 tests
[ ] Cloud Run health = 200
[ ] C002 production proof captured
[ ] C003 production proof captured
[ ] Zero-action-before-approval proof captured
[ ] Approval proof captured
[ ] Five C003 actions verified
[ ] Duplicate protection demonstrated
[ ] Escalation demo captured
[ ] Demo limitations disclosed
[ ] Repository URL confirmed
[ ] Final demo recording ready
```

## 18. Final Evidence Position

The strongest overall submission narrative is:

```text
SiteReady AI
    |
    +--> Understands evidence
    |
    +--> Compares historical state
    |
    +--> Explains findings
    |
    +--> Applies deterministic execution policy
    |
    +---- permitted routine work ----> AUTONOMOUS
    |                                    |
    |                                    v
    |                                VERIFY
    |
    +---- HIGH / CRITICAL -----------> HUMAN APPROVAL
                                         |
                                         v
                                     ACTIONS
                                         |
                                         v
                                     VERIFY
```

The differentiator is **controlled autonomy**:

> The agent does not simply recommend actions and it does not blindly automate consequential work. It investigates, decides within an explicit policy boundary, acts where permitted, and stops for human approval where required.

**Submission state:** Engineering and repository hardening are complete. Remaining work is evidence capture, final demo/recording, final submission text, and submission execution.
