from agent.firestore_client import get_firestore_client


STATUS_PRIORITY = {
    "READY": 1,
    "ATTENTION_REQUIRED": 2,
    "NOT_READY": 3,
}

SUPPORTED_RESULTS = set(STATUS_PRIORITY)


def load_readiness_rules() -> list[dict]:
    """Load enabled readiness rules from Firestore."""
    db = get_firestore_client()

    rules = []

    for document in db.collection("readiness_rules").stream():
        rule = {
            "rule_id": document.id,
            **document.to_dict(),
        }

        if rule.get("enabled", True):
            rules.append(rule)

    rules.sort(key=lambda item: item["rule_id"])

    return rules


def evaluate_readiness(
    contractor: dict,
    documents: list[dict],
    training_records: list[dict],
    inspections: list[dict],
    corrective_actions: list[dict],
) -> dict:
    """
    Evaluate contractor readiness against configured prototype rules.

    The decision is deterministic: readiness is based on explicit
    rules and the evidence supplied to this function.
    """

    rules = load_readiness_rules()

    current_status = "READY"
    issues = []

    for rule in rules:
        condition = rule.get("condition_type")
        rule_result = rule.get("result")

        if rule_result not in SUPPORTED_RESULTS:
            raise ValueError(
                f"Invalid readiness result '{rule_result}' "
                f"for rule '{rule['rule_id']}'."
            )

        matched = False

        if condition == "expired_mandatory_document":
            matched_documents = [
                document
                for document in documents
                if document.get("mandatory") is True
                and document.get("status") == "expired"
            ]

            for document in matched_documents:
                matched = True
                issues.append(
                    {
                        "category": "document",
                        "issue_type": "expired_document",
                        "issue_reference": document["document_id"],
                        "rule_id": rule["rule_id"],
                        "severity": rule["severity"],
                        "description": (
                            f"{document['document_name']} is expired."
                        ),
                    }
                )

        elif condition == "missing_mandatory_document":
            matched_documents = [
                document
                for document in documents
                if document.get("mandatory") is True
                and document.get("status") == "missing"
            ]

            for document in matched_documents:
                matched = True
                issues.append(
                    {
                        "category": "document",
                        "issue_type": "missing_document",
                        "issue_reference": document["document_id"],
                        "rule_id": rule["rule_id"],
                        "severity": rule["severity"],
                        "description": (
                            f"{document['document_name']} is missing."
                        ),
                    }
                )

        elif condition == "expiring_mandatory_document":
            matched_documents = [
                document
                for document in documents
                if document.get("mandatory") is True
                and document.get("status") == "expiring_soon"
            ]

            for document in matched_documents:
                matched = True
                issues.append(
                    {
                        "category": "document",
                        "issue_type": "expiring_document",
                        "issue_reference": document["document_id"],
                        "rule_id": rule["rule_id"],
                        "severity": rule["severity"],
                        "description": (
                            f"{document['document_name']} is approaching expiry."
                        ),
                    }
                )

        elif condition == "missing_mandatory_training":
            matched_training = [
                training
                for training in training_records
                if training.get("mandatory") is True
                and training.get("status") == "missing"
            ]

            for training in matched_training:
                matched = True
                issues.append(
                    {
                        "category": "training",
                        "issue_type": "missing_training",
                        "issue_reference": training["training_id"],
                        "rule_id": rule["rule_id"],
                        "severity": rule["severity"],
                        "description": (
                            f"{training['training_type']} training is missing."
                        ),
                    }
                )

        elif condition == "expired_mandatory_training":
            matched_training = [
                training
                for training in training_records
                if training.get("mandatory") is True
                and training.get("status") == "expired"
            ]

            for training in matched_training:
                matched = True
                issues.append(
                    {
                        "category": "training",
                        "issue_type": "expired_training",
                        "issue_reference": training["training_id"],
                        "rule_id": rule["rule_id"],
                        "severity": rule["severity"],
                        "description": (
                            f"{training['training_type']} training is expired."
                        ),
                    }
                )

        elif condition == "failed_required_inspection":
            matched_inspections = [
                inspection
                for inspection in inspections
                if inspection.get("status") == "failed"
            ]

            for inspection in matched_inspections:
                matched = True
                issues.append(
                    {
                        "category": "inspection",
                        "issue_type": "failed_inspection",
                        "issue_reference": inspection["inspection_id"],
                        "rule_id": rule["rule_id"],
                        "severity": rule["severity"],
                        "description": (
                            f"{inspection['inspection_type']} inspection "
                            f"failed with {inspection['findings_count']} findings."
                        ),
                    }
                )

        elif condition == "high_priority_overdue_action":
            matched_actions = [
                action
                for action in corrective_actions
                if action.get("priority") == "high"
                and action.get("status") == "overdue"
            ]

            for action in matched_actions:
                matched = True
                issues.append(
                    {
                        "category": "corrective_action",
                        "issue_type": "overdue_corrective_action",
                        "issue_reference": action["action_id"],
                        "rule_id": rule["rule_id"],
                        "severity": rule["severity"],
                        "description": (
                            "High-priority corrective action is overdue: "
                            f"{action['description']}."
                        ),
                    }
                )

        elif condition == "open_medium_priority_action":
            matched_actions = [
                action
                for action in corrective_actions
                if action.get("priority") == "medium"
                and action.get("status") == "open"
            ]

            for action in matched_actions:
                matched = True
                issues.append(
                    {
                        "category": "corrective_action",
                        "issue_type": "open_corrective_action",
                        "issue_reference": action["action_id"],
                        "rule_id": rule["rule_id"],
                        "severity": rule["severity"],
                        "description": (
                            "Medium-priority corrective action is open: "
                            f"{action['description']}."
                        ),
                    }
                )

        elif condition == "all_required_checks_pass":
            # READY is the baseline result.
            # Higher-priority results override it below.
            matched = True

        else:
            raise ValueError(
                f"Unsupported readiness condition '{condition}' "
                f"for rule '{rule['rule_id']}'."
            )

        if matched:
            if STATUS_PRIORITY[rule_result] > STATUS_PRIORITY[current_status]:
                current_status = rule_result

    if current_status == "NOT_READY":
        risk_level = "HIGH"
    elif current_status == "ATTENTION_REQUIRED":
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "contractor_id": contractor["contractor_id"],
        "contractor_name": contractor["company_name"],
        "readiness_status": current_status,
        "risk_level": risk_level,
        "issues": issues,
    }