from datetime import datetime, timezone

from agent.firestore_client import get_firestore_client


def record_readiness_assessment(
    assessment: dict,
    source: str = "site_readiness_agent",
) -> dict:
    """
    Persist a readiness assessment to Firestore as an audit record.
    """

    required_fields = [
        "contractor_id",
        "contractor_name",
        "readiness_status",
        "risk_level",
        "issues",
    ]

    for field in required_fields:
        if field not in assessment:
            raise ValueError(
                f"Assessment is missing required field '{field}'."
            )

    db = get_firestore_client()

    assessed_at = datetime.now(timezone.utc).isoformat()

    assessment_id = (
        f"RA-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    )

    audit_record = {
        "assessment_id": assessment_id,
        "contractor_id": assessment["contractor_id"],
        "contractor_name": assessment["contractor_name"],
        "readiness_status": assessment["readiness_status"],
        "risk_level": assessment["risk_level"],
        "issues": assessment["issues"],
        "issue_count": len(assessment["issues"]),
        "assessed_at": assessed_at,
        "source": source,
    }

    (
        db.collection("readiness_assessments")
        .document(assessment_id)
        .set(audit_record)
    )

    return audit_record