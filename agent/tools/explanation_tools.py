from agent.tools.readiness_tools import assess_contractor_readiness


def explain_contractor_readiness(contractor_id: str) -> dict:
    """
    Explain exactly why a contractor is READY, ATTENTION_REQUIRED,
    or NOT_READY.

    ALWAYS use this tool when the user asks:
    - why a contractor is not ready
    - why a contractor requires attention
    - what is causing a contractor's readiness result
    - what issues caused a contractor's risk level
    - which evidence explains a contractor's readiness decision

    The explanation must be based only on the deterministic
    SiteReady readiness assessment and its evidence.
    """
    assessment = assess_contractor_readiness(contractor_id)

    explanations = []

    for issue in assessment["issues"]:
        explanations.append(
            {
                "issue_type": issue["issue_type"],
                "issue_reference": issue["issue_reference"],
                "rule_id": issue["rule_id"],
                "severity": issue["severity"],
                "description": issue["description"],
                "impact": (
                    f"Rule {issue['rule_id']} identified this as a "
                    f"{issue['severity']} readiness issue. "
                    f"It contributed to the contractor being classified "
                    f"as {assessment['readiness_status']}."
                ),
            }
        )

    return {
        "contractor_id": assessment["contractor_id"],
        "contractor_name": assessment["contractor_name"],
        "readiness_status": assessment["readiness_status"],
        "risk_level": assessment["risk_level"],
        "issue_count": len(explanations),
        "explanations": explanations,
    }