from typing import Any

from agent.tools.audited_readiness_tools import (
    assess_contractor_readiness_with_audit,
)
from agent.tools.change_detection_tools import (
    compare_contractor_assessments,
)
from agent.tools.explanation_tools import (
    explain_contractor_readiness,
)
from agent.tools.followup_approval_tools import (
    propose_followup_actions,
)
from agent.tools.followup_orchestration import (
    create_followup_actions_for_readiness,
)
from agent.tools.human_attention_tools import create_human_attention
from agent.tools.notification_tools import create_human_notification_events


def _requires_human_approval(
    assessment: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Determine whether the Taskmaster workflow requires human approval."""
    reasons: list[str] = []
    risk_level = str(assessment.get("risk_level", "")).upper()

    if risk_level == "HIGH":
        reasons.append("Contractor risk level is HIGH.")

    for issue in assessment.get("issues", []):
        severity = str(issue.get("severity", "")).lower()
        if severity == "critical":
            reasons.append("At least one readiness issue has critical severity.")
            break

    return bool(reasons), reasons


def _verify_autonomous_actions(
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify that the action engine returned actionable records."""
    verified_actions = []
    verification_failures = []

    for action in actions:
        followup_id = action.get("followup_id")
        status = action.get("status")

        if not followup_id:
            verification_failures.append(
                "Action response did not contain a follow-up ID."
            )
            continue

        if status != "open":
            verification_failures.append(
                f"Action '{followup_id}' did not return status 'open'."
            )
            continue

        verified_actions.append(followup_id)

    return {
        "verified": len(verification_failures) == 0,
        "verified_action_ids": verified_actions,
        "verification_failures": verification_failures,
    }


def run_taskmaster_workflow(contractor_id: str) -> dict[str, Any]:
    """Execute the SiteReady Taskmaster workflow."""
    if not contractor_id or not contractor_id.strip():
        raise ValueError("contractor_id is required.")

    contractor_id = contractor_id.strip().upper()

    assessment = assess_contractor_readiness_with_audit(contractor_id)
    comparison = compare_contractor_assessments(contractor_id)
    explanation = explain_contractor_readiness(contractor_id)
    approval_required, approval_reasons = _requires_human_approval(assessment)

    workflow_steps = [
        {
            "step": "assessment",
            "status": "completed",
            "assessment_id": assessment["audit"]["assessment_id"],
        },
        {
            "step": "historical_comparison",
            "status": (
                "completed"
                if comparison.get("comparison_available")
                else "not_available"
            ),
        },
        {
            "step": "explanation",
            "status": "completed",
            "issue_count": explanation.get(
                "issue_count", len(explanation.get("explanations", []))
            ),
        },
    ]

    if approval_required:
        proposal = propose_followup_actions(contractor_id)
        attention = create_human_attention(proposal)
        notifications = create_human_notification_events(attention)

        workflow_steps.extend(
            [
                {
                    "step": "execution_policy",
                    "status": "approval_required",
                    "reasons": approval_reasons,
                },
                {
                    "step": "human_attention",
                    "status": "open",
                    "attention_id": attention.get("attention_id"),
                    "approval_id": proposal.get("approval_id"),
                },
                {
                    "step": "notification_dispatch",
                    "status": "recorded",
                    "notification_ids": [
                        item.get("notification_id") for item in notifications
                    ],
                    "mode": "demo_simulation",
                },
                {
                    "step": "followup_proposal",
                    "status": (
                        "pending"
                        if proposal.get("status") == "pending"
                        else proposal.get("status")
                    ),
                    "approval_id": proposal.get("approval_id"),
                },
            ]
        )

        return {
            "workflow_status": "awaiting_human_approval",
            "execution_mode": "human_approval",
            "contractor_id": assessment["contractor_id"],
            "contractor_name": assessment["contractor_name"],
            "readiness_status": assessment["readiness_status"],
            "risk_level": assessment["risk_level"],
            "assessment": assessment,
            "comparison": comparison,
            "explanation": explanation,
            "approval_required": True,
            "approval_reasons": approval_reasons,
            "approval": proposal,
            "human_attention": attention,
            "notifications": notifications,
            "workflow_steps": workflow_steps,
            "message": (
                "The Taskmaster workflow completed its investigation, created "
                "a practitioner attention item, recorded notification events, "
                "and prepared the required follow-up actions. Consequential work "
                "requires human approval."
            ),
        }

    execution = create_followup_actions_for_readiness(contractor_id)
    actions = execution.get("actions", [])
    verification = _verify_autonomous_actions(actions)

    workflow_steps.extend(
        [
            {
                "step": "execution_policy",
                "status": "autonomous_execution",
                "reasons": [],
            },
            {
                "step": "followup_execution",
                "status": (
                    "completed" if verification["verified"] else "verification_failed"
                ),
                "created_count": sum(
                    1 for action in actions if action.get("created") is True
                ),
                "duplicate_count": sum(
                    1 for action in actions if action.get("duplicate") is True
                ),
            },
            {
                "step": "execution_verification",
                "status": "completed" if verification["verified"] else "failed",
            },
        ]
    )

    return {
        "workflow_status": (
            "completed" if verification["verified"] else "verification_failed"
        ),
        "execution_mode": "autonomous",
        "contractor_id": assessment["contractor_id"],
        "contractor_name": assessment["contractor_name"],
        "readiness_status": assessment["readiness_status"],
        "risk_level": assessment["risk_level"],
        "assessment": assessment,
        "comparison": comparison,
        "explanation": explanation,
        "approval_required": False,
        "approval_reasons": [],
        "execution": execution,
        "verification": verification,
        "workflow_steps": workflow_steps,
        "message": (
            "The Taskmaster workflow completed autonomous execution and verified the result."
        ),
    }
