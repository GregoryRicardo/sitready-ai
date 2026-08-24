from datetime import datetime

from google.cloud.firestore_v1.base_query import FieldFilter

from agent.firestore_client import get_firestore_client


def _parse_timestamp(value: str) -> datetime:
    """
    Parse an ISO-8601 timestamp into a timezone-aware datetime.
    """
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _issue_key(issue: dict) -> tuple[str, str, str]:
    """
    Create a stable identity for a readiness issue.
    """
    return (
        issue["issue_type"],
        issue["issue_reference"],
        issue["rule_id"],
    )


def get_recent_assessments(
    contractor_id: str,
    limit: int = 2,
) -> list[dict]:
    """
    Retrieve the most recent readiness assessments for a contractor.
    """

    if not contractor_id or not contractor_id.strip():
        raise ValueError("contractor_id is required.")

    if limit < 1:
        raise ValueError("limit must be at least 1.")

    contractor_id = contractor_id.strip().upper()

    db = get_firestore_client()

    documents = (
        db.collection("readiness_assessments")
        .where(
            filter=FieldFilter(
                "contractor_id",
                "==",
                contractor_id,
            )
        )
        .stream()
    )

    assessments = []

    for document in documents:
        assessment = {
            "document_id": document.id,
            **document.to_dict(),
        }

        if assessment.get("assessed_at"):
            assessments.append(assessment)

    assessments.sort(
        key=lambda item: _parse_timestamp(item["assessed_at"]),
        reverse=True,
    )

    return assessments[:limit]


def compare_contractor_assessments(
    contractor_id: str,
) -> dict:
    """
    Compare the two most recent readiness assessments for a contractor.

    The comparison is deterministic and based only on persisted
    readiness assessment evidence.
    """

    assessments = get_recent_assessments(
        contractor_id=contractor_id,
        limit=2,
    )

    if len(assessments) == 0:
        return {
            "contractor_id": contractor_id.upper(),
            "comparison_available": False,
            "reason": "No readiness assessments found.",
        }

    if len(assessments) == 1:
        latest = assessments[0]

        return {
            "contractor_id": contractor_id.upper(),
            "comparison_available": False,
            "reason": "Only one readiness assessment is available.",
            "latest_assessment": {
                "assessment_id": latest["assessment_id"],
                "assessed_at": latest["assessed_at"],
                "readiness_status": latest["readiness_status"],
                "risk_level": latest["risk_level"],
            },
        }

    latest = assessments[0]
    previous = assessments[1]

    latest_issues = {
        _issue_key(issue): issue
        for issue in latest.get("issues", [])
    }

    previous_issues = {
        _issue_key(issue): issue
        for issue in previous.get("issues", [])
    }

    new_issue_keys = latest_issues.keys() - previous_issues.keys()
    resolved_issue_keys = previous_issues.keys() - latest_issues.keys()
    persistent_issue_keys = (
        latest_issues.keys() & previous_issues.keys()
    )

    new_issues = [
        latest_issues[key]
        for key in sorted(new_issue_keys)
    ]

    resolved_issues = [
        previous_issues[key]
        for key in sorted(resolved_issue_keys)
    ]

    persistent_issues = [
        latest_issues[key]
        for key in sorted(persistent_issue_keys)
    ]

    return {
        "contractor_id": latest["contractor_id"],
        "contractor_name": latest["contractor_name"],
        "comparison_available": True,
        "previous_assessment": {
            "assessment_id": previous["assessment_id"],
            "assessed_at": previous["assessed_at"],
            "readiness_status": previous["readiness_status"],
            "risk_level": previous["risk_level"],
        },
        "latest_assessment": {
            "assessment_id": latest["assessment_id"],
            "assessed_at": latest["assessed_at"],
            "readiness_status": latest["readiness_status"],
            "risk_level": latest["risk_level"],
        },
        "status_changed": (
            previous["readiness_status"]
            != latest["readiness_status"]
        ),
        "risk_changed": (
            previous["risk_level"]
            != latest["risk_level"]
        ),
        "new_issues": new_issues,
        "resolved_issues": resolved_issues,
        "persistent_issues": persistent_issues,
        "new_issue_count": len(new_issues),
        "resolved_issue_count": len(resolved_issues),
        "persistent_issue_count": len(persistent_issues),
    }