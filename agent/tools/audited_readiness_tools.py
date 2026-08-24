from agent.tools.audit_tools import record_readiness_assessment
from agent.tools.readiness_tools import assess_contractor_readiness


def assess_contractor_readiness_with_audit(
    contractor_id: str,
) -> dict:
    """
    Assess contractor readiness and record the result in the
    SiteReady AI audit trail.
    """

    assessment = assess_contractor_readiness(contractor_id)

    audit_record = record_readiness_assessment(
        assessment=assessment,
    )

    return {
        **assessment,
        "audit": {
            "assessment_id": audit_record["assessment_id"],
            "assessed_at": audit_record["assessed_at"],
        },
    }