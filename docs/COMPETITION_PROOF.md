# SiteReady AI — Competition Proof

## 1. Competition Technology

**Track:** Taskmaster  
**Agent framework:** Google ADK  
**Gemini model:** `gemini-3.6-flash`  
**Google Cloud:** Cloud Run + Cloud Firestore

The repository contains a Google ADK `Agent` configured with `Gemini(model="gemini-3.6-flash")`. The ADK runner is provided in `run_agent.py` for direct model-driven agent execution.

The production web console invokes the Taskmaster workflow through an ADK/Gemini bridge. Gemini selects the authoritative `run_taskmaster_workflow` tool, while SiteReady tools and Taskmaster policy control evidence, execution boundaries, persistence, approval, escalation and verification.

## 2. What the Agent Does

SiteReady turns a contractor-readiness goal into a controlled multi-step workflow:

```text
Goal
  ↓
Assess evidence
  ↓
Compare historical state
  ↓
Explain findings
  ↓
Apply execution policy
  ├── Routine / permitted → autonomous execution
  │                         ↓
  │                     verification
  │
  └── HIGH risk / CRITICAL issue
                              ↓
                       human approval
                              ↓
                       action creation
                              ↓
                         verification
```

For the human-governance scenario, the workflow additionally provides:

```text
Human attention
      ↓
Notification event
      ↓
60-second demo escalation schedule
      ↓
DEMO — ESCALATION TRIGGERED
      ↓
Human approval
      ↓
Action creation
      ↓
Verification
```

The current demo configuration uses a **60-second** escalation window. The UI displays the persisted countdown and automatically reconciles the due event through the notification monitoring path.

The design principle is **controlled autonomy**: the agent can execute permitted routine work, but consequential work is stopped at an explicit human-approval boundary.

## 3. Technology Responsibilities

### Gemini 3.6 Flash

Provides the model reasoning capability for the Google ADK SiteReady agent.

### Google ADK

Provides the agent framework, model integration, session/runtime support, and tool orchestration used by the SiteReady agent path.

### SiteReady tools

Provide deterministic access to contractor evidence, readiness data, historical comparisons, explanations, action creation, approval records, notification records, and verification.

### Taskmaster policy

Determines whether the requested work can proceed autonomously or must stop for human approval. The policy is implemented in SiteReady workflow code and is not presented as a legal or H&S regulation.

### Cloud Run

Hosts the production FastAPI application and Taskmaster API workflow.

### Firestore

Stores contractor evidence, readiness state, follow-up actions, approval records, human-attention items, notification events, and workflow audit state.

## 4. Important Architecture Boundary

For evidence accuracy, the competition demo should distinguish the model reasoning/orchestration layer from the deterministic execution controls.

The ADK agent exposes `run_taskmaster_workflow` as one of its available tools. The production web endpoint invokes the ADK bridge, which instructs Gemini to use that authoritative tool and captures the tool's structured response. The Taskmaster workflow remains responsible for policy, persistence, approval boundaries, notification state, escalation, and verification.

The repository therefore demonstrates both:

```text
Production web path:
User / UI
      ↓
Cloud Run / FastAPI
      ↓
Google ADK Agent
      ↓
Gemini 3.6 Flash
      ↓
run_taskmaster_workflow
      ↓
Taskmaster policy + SiteReady tools
      ↓
Firestore / human attention / actions / verification
```

and the direct runner:

```text
Direct ADK/Gemini path:
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

This preserves a clear boundary: Gemini provides model reasoning and tool orchestration; deterministic SiteReady workflow code controls consequential execution and persistence.

## 5. Production Proof — C002

Contractor `C002` is the controlled autonomous scenario.

Production validation returned:

```text
workflow_status   = completed
execution_mode    = autonomous
readiness_status  = ATTENTION_REQUIRED
risk_level        = MEDIUM
approval_required = false
verification      = true
```

The production workflow completed the assessment, historical comparison, explanation, execution-policy decision, autonomous execution, and verification stages.

Two open follow-up actions were created for C002 and verified.

## 6. Production Proof — C003

Contractor `C003` is the controlled human-governance scenario.

Production validation returned:

```text
workflow_status   = awaiting_human_approval
execution_mode    = human_approval
readiness_status  = NOT_READY
risk_level        = HIGH
approval_required = true
```

Five readiness issues were identified.

Before approval:

```text
C003 follow-up actions = 0
approval status        = pending
```

The approval record proposed five follow-up actions:

```text
DOC007
INS003
DOC008
TR009
CA002
```

After explicit production approval:

```text
approved       = true
status         = approved
created        = true
duplicate      = false
```

All five C003 follow-up actions were then confirmed in production Firestore with status `open` and priority `high`.

## 7. Notification and Escalation Demo Evidence

The local emulator demonstration adds a judge-visible human-attention and escalation layer.

Initial state:

```text
EMAIL     | SIMULATED
WHATSAPP  | DEMO — SCHEDULED
countdown | 60 seconds
```

After the threshold:

```text
WHATSAPP  | DEMO — ESCALATION TRIGGERED
```

The audit record includes a notification ID, recipient role(s), approval ID, timestamp, escalation reason, and triggered status.

Important: this is **demo simulation / audit evidence**, not proof that an external WhatsApp message was delivered. The implementation explicitly records that no external WhatsApp message was sent.

The escalation is reconciled through the notification log/polling flow using the persisted `escalation_due_at` timestamp. This is sufficient for the competition demonstration, but it should not be described as a Cloud Scheduler/Cloud Tasks background job.

## 8. Idempotency / Duplicate Protection

A repeat C003 approval scenario was executed while the five follow-up actions already existed.

The approval workflow detected the existing records as duplicates instead of creating a second set.

Observed behavior:

```text
created    = false
duplicate  = true
```

This demonstrates that repeated execution does not blindly duplicate open consequential actions.

## 9. Local Automated Validation

The repository test suite is hardened around a shared pytest Firestore fixture and local emulator setup.

Current local regression checkpoint:

```text
15 passed
```

The expanded suite covers readiness, audit/explanation, change detection, end-to-end readiness, follow-up approval, human attention, Taskmaster API/workflow behavior, ADK web routing contract, and notification/escalation behavior.

## 10. Judge-Facing UI Evidence

The web console exposes the Taskmaster workflow directly to the user.

The UI displays:

```text
Taskmaster Agent
ASSESS → COMPARE → EXPLAIN → DECIDE → ACT / APPROVE → VERIFY
```

The Agent Activity panel renders the workflow steps returned by the Taskmaster backend.

The interface also exposes:

- visible Taskmaster explanation via the `i` control;
- human-attention queue;
- approval ID and status;
- notification and escalation audit log;
- live demo escalation countdown;
- escalation trigger state;
- verification results;
- technology visibility through `Powered by Google ADK · Gemini 3.6 Flash · Google Cloud`.

## 11. Production API Entry Points

Production Cloud Run service:

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
```

## 12. Evidence Summary

| Evidence | Result |
|---|---|
| Gemini 3.6 Flash configured | ✅ |
| Google ADK Agent configured | ✅ |
| Direct ADK runner available | ✅ |
| ADK + Gemini web bridge implemented | ✅ |
| Google Cloud production deployment | ✅ |
| Cloud Run health | ✅ |
| Production Firestore | ✅ |
| C002 autonomous execution | ✅ |
| C002 verification | ✅ |
| C003 human approval gate | ✅ |
| C003 zero actions before approval | ✅ |
| C003 five actions after approval | ✅ |
| Duplicate protection | ✅ |
| Human attention layer | ✅ |
| Notification audit events | ✅ |
| Demo escalation trigger | ✅ local demo |
| Local automated tests | ✅ 15/15 |
| Judge-facing Agent Activity UI | ✅ |

## 13. Competition Demo Sequence

Recommended four-minute flow:

1. Introduce the contractor-readiness problem and SiteReady's goal.
2. Show the Taskmaster UI and briefly open the `i` explanation to explain controlled autonomy.
3. Run C002 and show autonomous completion plus verification.
4. Run C003 and show `NOT_READY / HIGH` plus the human-attention boundary.
5. Show the notification log and the **60-second agent escalation countdown**.
6. Let the countdown reach zero and show `DEMO — ESCALATION TRIGGERED` without pressing an escalation button.
7. Show the pending approval ID and the fact that no C003 actions exist before approval.
8. Approve the exact approval ID and show five follow-up actions created and the human-attention item resolved.
9. Briefly show duplicate protection.
10. Optionally run `run_agent.py` if the judging criteria require a separate direct proof of ADK/Gemini execution.
11. Finish with the repository evidence and Google Cloud production deployment.

## 14. Repository and Validation References

Primary repository documentation:

- `README.md`
- `docs/HACKATHON_VALIDATION.md`
- `docs/JUDGE_EVIDENCE_MATRIX.md`
- `run_agent.py`
- `app/agent.py`
- `app/adk_taskmaster.py`
- `agent/tools/taskmaster_tools.py`
- `agent/tools/notification_tools.py`
- `web/main.py`
- `tests/`
- `web/`

The repository should be treated as the primary technical evidence source for the competition submission.
