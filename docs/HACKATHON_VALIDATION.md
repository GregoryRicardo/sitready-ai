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

The live agent configuration uses Google ADK's `Agent` with `Gemini(model="gemini-3.6-flash")`.

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

Five critical readiness issues were identified. A pending approval was created and duplicate protection was verified: re-running the workflow returned the existing pending approval instead of creating another one.

Before approval, Firestore verification showed no C003 follow-up actions.

After explicit human approval through `/api/approve/{approval_id}`, five C003 follow-up actions were created and verified as `open`.

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
7. Execute C003 work only after explicit approval.
8. Verify persisted action records.
9. Prevent duplicate pending approvals and duplicate open actions.

## Firestore diagnostic cleanup

Temporary diagnostic documents created during the Firestore connectivity investigation were removed from the `diagnostic` collection after production validation.

Runtime Firestore data is not committed to this repository. Production validation above describes the deployed state verified on 25 August 2026.

## Important implementation note

The repository's original `scripts/seed_firestore.py` uses the Python Firestore client. During deployment troubleshooting, Firestore writes through that client showed intermittent `CONSUMER_INVALID` behavior, while the Firestore REST API path was reliable. Production datasets were therefore populated using controlled REST writes during validation.

No application secrets or access tokens are stored in this repository.
