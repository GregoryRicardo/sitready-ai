# SiteReady AI — Hackathon Validation Record

## Purpose

This document records the end-to-end validation completed for the All Things Agentic Hackathon Taskmaster submission.

## Competition alignment

- **Track:** Taskmaster
- **Gemini model:** `gemini-3.6-flash`
- **Google agent framework:** Google ADK
- **Google Cloud services:** Cloud Run and Cloud Firestore
- **Live Cloud Run service:** `sitready-ai`
- **Region:** `africa-south1`

The repository contains a Google ADK `Agent` with `Gemini(model="gemini-3.6-flash")`. The direct ADK/Gemini execution path is provided by `run_agent.py`.

The production web console invokes the Taskmaster workflow through an ADK/Gemini bridge. Gemini selects the authoritative `run_taskmaster_workflow` tool, while SiteReady tools and Taskmaster policy control deterministic evidence access, execution, persistence, approval, escalation and verification.

## Production data validation

The following Firestore datasets were successfully populated in the production `(default)` database:

| Collection | Records | Status |
|---|---:|---|
| `contractors` | 3 | Verified |
| `documents` | 9 | Verified |
| `training_records` | 9 | Verified |
| `inspections` | 3 | Verified |
| `corrective_actions` | 2 | Verified |
| `readiness_rules` | 9 | Verified |

## Taskmaster validation

### C002 — autonomous execution

Live endpoint returned:

- `workflow_status`: `completed`
- `execution_mode`: `autonomous`
- `contractor_id`: `C002`
- `approval_required`: `False`

Firestore verification confirmed two open follow-up actions for C002 created by the autonomous Taskmaster workflow.

### C003 — human approval boundary

Live endpoint returned:

- `workflow_status`: `awaiting_human_approval`
- `execution_mode`: `human_approval`
- `contractor_id`: `C003`
- `readiness_status`: `NOT_READY`
- `risk_level`: `HIGH`
- `approval_required`: `True`

Five readiness issues were identified. A pending approval was created and duplicate protection was verified: re-running the workflow returned the existing pending approval instead of creating another one.

Before approval, Firestore verification showed no C003 follow-up actions.

After explicit human approval through `/api/approve/{approval_id}`, five C003 follow-up actions were created and verified as `open`.

## Notification and escalation demo validation

The local emulator workflow provides a judge-visible human-attention and escalation layer.

The flow is:

```text
Human attention required
        ↓
EMAIL | SIMULATED
        ↓
WHATSAPP | DEMO — SCHEDULED
        ↓
60-second demo countdown
        ↓
WHATSAPP | DEMO — ESCALATION TRIGGERED
```

The escalation event is triggered without a practitioner pressing an escalation button. The audit record includes notification ID, recipient roles, approval ID, timestamp, escalation reason and triggered status.

Important: these email/WhatsApp events are **demo simulation / audit events**, not evidence of external message delivery. The implementation explicitly records that no external WhatsApp message was sent.

The application reconciles due demo escalations using the persisted `escalation_due_at` timestamp when the notification log is read/polled. The browser monitoring loop polls the notification endpoint and therefore makes the transition visible during the competition demonstration. This is suitable for the competition demonstration but is not a Cloud Scheduler or Cloud Tasks background worker.

## ADK/Gemini validation

A direct local ADK runner was validated after correcting the Google Cloud ADC quota project configuration. `run_agent.py` successfully executed the SiteReady agent against contractor `C003` and returned a contractor-specific readiness assessment identifying five critical issues.

The production web Taskmaster endpoint is now routed through `app/adk_taskmaster.py`, which invokes the ADK runner and captures the `run_taskmaster_workflow` tool's structured response. API regression tests validate this web-to-ADK routing contract; the full local workflow suite remains green.

## Approval API

The production approval endpoint is:

`POST /api/approve/{approval_id}`

The endpoint calls the authoritative `approve_followup_actions` function. Approval is required before consequential C003 actions are persisted.

## Evidence of controlled autonomy

The validated behavior demonstrates the intended Taskmaster control boundary:

1. Assess contractor readiness.
2. Compare against historical assessment state.
3. Explain evidence-backed issues.
4. Determine execution policy.
5. Execute routine C002 work autonomously.
6. Stop C003 consequential work at a human-approval gate.
7. Create a human-attention item and audit notification events.
8. Demonstrate automatic escalation at the configured demo threshold.
9. Execute C003 work only after explicit approval.
10. Verify persisted action records.
11. Prevent duplicate pending approvals and duplicate open actions.

## Automated regression validation

The local suite uses the Firestore emulator with a shared pytest fixture. The fixture requires local mode, seeds deterministic baseline data, and clears generated actions, approvals, human-attention records and notification events between isolated tests.

Current regression checkpoint:

```text
15 passed
```

Notification-specific tests cover creation/scheduling, due-escalation reconciliation without a manual trigger, and prevention of escalation after human attention is resolved. API tests also validate the web-to-ADK routing contract using a controlled test double.

## Firestore diagnostic cleanup

Temporary diagnostic documents created during the Firestore connectivity investigation were removed from the `diagnostic` collection after production validation.

Runtime Firestore data is not committed to this repository. Production validation above describes the deployed state verified on 25 August 2026.

## Important implementation note

The repository's original `scripts/seed_firestore.py` uses the Python Firestore client. During deployment troubleshooting, Firestore writes through that client showed intermittent `CONSUMER_INVALID` behavior, while the Firestore REST API path was reliable. Production datasets were therefore populated using controlled REST writes during validation.

No application secrets or access tokens are stored in this repository.
