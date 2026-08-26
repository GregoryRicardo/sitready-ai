# SiteReady AI — Competition Proof

## 1. Competition Technology

**Track:** Taskmaster  
**Agent framework:** Google ADK  
**Gemini model:** `gemini-3.6-flash`  
**Google Cloud:** Cloud Run + Cloud Firestore

The production agent is configured with Google ADK's `Agent` and `Gemini(model="gemini-3.6-flash")`.

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

The design principle is **controlled autonomy**: the agent can execute permitted routine work, but consequential work is stopped at an explicit human-approval boundary.

## 3. Technology Responsibilities

### Gemini 3.6 Flash

Provides the agent reasoning layer used by SiteReady's Taskmaster workflow.

### Google ADK

Provides the agent framework and orchestration layer around the Gemini model and SiteReady tools.

### SiteReady tools

Provide deterministic access to contractor evidence, readiness data, historical comparisons, explanations, action creation, approval records, and verification.

### Taskmaster policy

Determines whether the requested work can proceed autonomously or must stop for human approval.

### Cloud Run

Hosts the production FastAPI application and agent workflow.

### Firestore

Stores contractor evidence, readiness state, follow-up actions, approval records, and workflow audit state.

## 4. Production Proof — C002

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

## 5. Production Proof — C003

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

## 6. Idempotency / Duplicate Protection

A repeat C003 approval scenario was executed while the five follow-up actions already existed.

The approval workflow detected the existing records as duplicates instead of creating a second set.

Observed behavior:

```text
created    = false
duplicate  = true
```

This demonstrates that repeated agent execution does not blindly duplicate open consequential actions.

## 7. Local Automated Validation

The repository test suite was hardened around a shared pytest Firestore fixture and local emulator setup.

Final local regression result:

```text
11 passed in 2.57s
```

The tests cover readiness, audit/explanation, change detection, end-to-end readiness, follow-up approval, Taskmaster API behavior, and Taskmaster workflow behavior.

## 8. Judge-Facing UI Evidence

The web console exposes the Taskmaster workflow directly to the user.

The UI displays:

```text
Taskmaster Agent
ASSESS → COMPARE → EXPLAIN → DECIDE → ACT / APPROVE → VERIFY
```

The Agent Activity panel renders the actual workflow steps returned by the Taskmaster backend.

The interface also exposes:

- a concise Taskmaster definition tooltip;
- a human-approval boundary for consequential work;
- approval ID and status;
- verification results;
- technology visibility through `Powered by Google ADK · Gemini 3.6 Flash · Google Cloud`.

## 9. Production API Entry Points

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

## 10. Evidence Summary

| Evidence | Result |
|---|---|
| Gemini 3.6 Flash identified | ✅ |
| Google ADK identified | ✅ |
| Google Cloud production deployment | ✅ |
| Cloud Run health | ✅ |
| Production Firestore | ✅ |
| C002 autonomous execution | ✅ |
| C002 verification | ✅ |
| C003 human approval gate | ✅ |
| C003 zero actions before approval | ✅ |
| C003 five actions after approval | ✅ |
| Duplicate protection | ✅ |
| Local automated tests | ✅ 11/11 |
| Judge-facing Agent Activity UI | ✅ |

## 11. Competition Demo Sequence

Recommended four-minute flow:

1. Introduce the contractor-readiness problem and SiteReady's goal.
2. Run C002 and show autonomous execution plus verification.
3. Run C003 and show `NOT_READY / HIGH` plus the human-approval boundary.
4. Show that no C003 actions exist before approval.
5. Approve the exact approval ID and show five follow-up actions created.
6. Briefly show duplicate protection.
7. Show the Taskmaster explanation, Gemini 3.6 Flash + Google ADK technology proof, and Google Cloud production deployment.

## 12. Repository and Validation References

Primary repository documentation:

- `README.md`
- `docs/HACKATHON_VALIDATION.md`
- `run_agent.py`
- `agent/`
- `web/`

The repository should be treated as the primary technical evidence source for the competition submission.
