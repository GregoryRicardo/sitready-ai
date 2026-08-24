async function apiPost(url) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    });

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            data.detail ||
            `Request failed: ${response.status}`
        );
    }

    return data;
}


function contractorId() {
    return document
        .getElementById("contractor-id")
        .value
        .trim()
        .toUpperCase();
}


function showReadiness(data) {
    document
        .getElementById("readiness-card")
        .classList.remove("hidden");

    document
        .getElementById("contractor-name")
        .textContent = data.contractor_name;

    document
        .getElementById("contractor-id-display")
        .textContent = data.contractor_id;

    document
        .getElementById("readiness-status")
        .textContent = data.readiness_status;

    document
        .getElementById("risk-level")
        .textContent = data.risk_level;
}


function showResults(title, html) {
    document
        .getElementById("results")
        .classList.remove("hidden");

    document
        .getElementById("results-content")
        .innerHTML = `
            <h3>${title}</h3>
            ${html}
        `;
}


function showApproval(data) {
    const approvalCard =
        document.getElementById("approval-card");

    approvalCard.classList.remove("hidden");

    const approvalIdElement =
        document.getElementById("approval-id");

    approvalIdElement.textContent =
        data.approval_id || "";

    const approvalStatusElement =
        document.getElementById("approval-status");

    approvalStatusElement.textContent =
        data.status === "pending"
            ? "Pending Human Approval"
            : data.status || "Unknown";

    const approvalMessageElement =
        document.getElementById("approval-message");

    approvalMessageElement.textContent =
        data.message ||
        "Follow-up actions are awaiting human approval.";

    const approveButton =
        document.getElementById("approve-button");

    const isPending =
        data.status === "pending";

    approveButton.disabled = !isPending;

    approveButton.textContent =
        isPending
            ? "Approve Actions"
            : "Already Approved";

    approvalCard.scrollIntoView({
        behavior: "smooth",
        block: "start",
    });
}


async function assessContractor() {
    try {
        const id = contractorId();

        if (!id) {
            alert("Please enter a contractor ID.");
            return;
        }

        const data = await apiPost(
            `/api/assess/${id}`
        );

        showReadiness(data);

        const issues = (data.issues || [])
            .map(
                issue => `
                    <div class="issue">
                        <strong>
                            ${issue.issue_reference}
                        </strong>
                        <div>
                            ${issue.description}
                        </div>
                    </div>
                `
            )
            .join("");

        showResults(
            "Readiness Assessment",
            `
                <p>
                    <strong>${data.issue_count || (data.issues || []).length}</strong>
                    issues identified.
                </p>
                ${issues}
            `
        );

    } catch (error) {
        alert(error.message);
    }
}


async function explainContractor() {
    try {
        const id = contractorId();

        if (!id) {
            alert("Please enter a contractor ID.");
            return;
        }

        const data = await apiPost(
            `/api/explain/${id}`
        );

        const explanations =
            (data.explanations || [])
                .map(
                    item => `
                        <div class="issue">
                            <strong>
                                ${item.issue_reference}
                            </strong>

                            <div>
                                ${item.description}
                            </div>

                            <small>
                                ${item.impact}
                            </small>
                        </div>
                    `
                )
                .join("");

        showResults(
            "Why is this contractor not ready?",
            explanations
        );

    } catch (error) {
        alert(error.message);
    }
}


async function compareContractor() {
    try {
        const id = contractorId();

        if (!id) {
            alert("Please enter a contractor ID.");
            return;
        }

        const data = await apiPost(
            `/api/compare/${id}`
        );

        const newIssues =
            data.new_issues || [];

        const resolvedIssues =
            data.resolved_issues || [];

        const persistentIssues =
            data.persistent_issues || [];

        const newIssueList =
            newIssues
                .map(
                    issue => `
                        <div class="issue">
                            <strong>
                                ${issue.issue_reference}
                            </strong>
                            <div>
                                ${issue.description}
                            </div>
                        </div>
                    `
                )
                .join("");

        const resolvedIssueList =
            resolvedIssues
                .map(
                    issue => `
                        <div class="issue">
                            <strong>
                                ${issue.issue_reference}
                            </strong>
                            <div>
                                ${issue.description}
                            </div>
                        </div>
                    `
                )
                .join("");

        showResults(
            "What Changed?",
            `
                <p>
                    <strong>Status changed:</strong>
                    ${data.status_changed}
                </p>

                <p>
                    <strong>Risk changed:</strong>
                    ${data.risk_changed}
                </p>

                <p>
                    <strong>New issues:</strong>
                    ${data.new_issue_count}
                </p>

                <p>
                    <strong>Resolved issues:</strong>
                    ${data.resolved_issue_count}
                </p>

                <p>
                    <strong>Persistent issues:</strong>
                    ${data.persistent_issue_count}
                </p>

                ${
                    newIssues.length
                        ? `
                            <h4>New Issues</h4>
                            ${newIssueList}
                        `
                        : ""
                }

                ${
                    resolvedIssues.length
                        ? `
                            <h4>Resolved Issues</h4>
                            ${resolvedIssueList}
                        `
                        : ""
                }

                ${
                    persistentIssues.length
                        ? `
                            <h4>Persistent Issues</h4>
                            <p>
                                All ${
                                    persistentIssues.length
                                } persistent issues remain active.
                            </p>
                        `
                        : ""
                }
            `
        );

    } catch (error) {
        alert(error.message);
    }
}


async function proposeActions() {
    const button = document.querySelector(
        'button[onclick="proposeActions()"]'
    );

    try {
        if (button) {
            button.disabled = true;
            button.textContent = "Preparing...";
        }

        const id = contractorId();

        if (!id) {
            alert("Please enter a contractor ID.");
            return;
        }

        const data = await apiPost(
            `/api/propose/${id}`
        );

        showApproval(data);

        const actions =
            data.proposed_actions || [];

        const actionList =
            actions
                .map(
                    action => `
                        <div class="issue">
                            <strong>
                                ${action.issue_reference}
                            </strong>

                            <div>
                                ${action.description}
                            </div>

                            <small>
                                Owner: ${action.owner}
                                |
                                Due: ${action.due_date}
                            </small>
                        </div>
                    `
                )
                .join("");

        showResults(
            "Proposed Follow-up Actions",
            `
                <p>
                    <strong>
                        ${actions.length}
                    </strong>
                    actions are pending human approval.
                </p>

                ${actionList}
            `
        );

    } catch (error) {
        alert(error.message);

    } finally {
        if (button) {
            button.disabled = false;
            button.textContent =
                "Prepare Follow-ups";
        }
    }
}


async function approveActions() {
    const approvalId =
        document
            .getElementById("approval-id")
            .textContent
            .trim();

    if (!approvalId) {
        alert("No approval ID is available.");
        return;
    }

    const button =
        document.getElementById("approve-button");

    try {
        button.disabled = true;
        button.textContent = "Approving...";

        const data = await apiPost(
            `/api/approve/${approvalId}`
        );

        showResults(
            "Approval Result",
            `
                <p>
                    Status:
                    <strong>
                        ${data.status}
                    </strong>
                </p>

                <p>
                    Actions returned:
                    <strong>
                        ${
                            (data.created_actions || [])
                                .length
                        }
                    </strong>
                </p>
            `
        );

        const approvalStatusElement =
            document.getElementById(
                "approval-status"
            );

        const approvalMessageElement =
            document.getElementById(
                "approval-message"
            );

        if (data.status === "approved") {
            approvalStatusElement.textContent =
                "Approved";

            approvalMessageElement.textContent =
                "Human approval was recorded. " +
                "The follow-up action request has been executed.";

            button.textContent = "Approved";
            button.disabled = true;

        } else {
            approvalStatusElement.textContent =
                data.status || "Unavailable";

            approvalMessageElement.textContent =
                "This approval request is no longer pending.";

            button.textContent = "Unavailable";
            button.disabled = true;
        }

        document
            .getElementById("approval-card")
            .scrollIntoView({
                behavior: "smooth",
                block: "start",
            });

    } catch (error) {
        button.disabled = false;
        button.textContent =
            "Approve Actions";

        alert(error.message);
    }
}


async function checkHealth() {
    try {
        const response =
            await fetch("/health");

        if (!response.ok) {
            throw new Error(
                "Health check failed"
            );
        }

        const data =
            await response.json();

        document
            .getElementById("system-status")
            .textContent =
                data.status === "ok"
                    ? "● ONLINE"
                    : "● OFFLINE";

    } catch {
        document
            .getElementById("system-status")
            .textContent =
                "● OFFLINE";
    }
}


checkHealth();