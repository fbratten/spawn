"""Example generated MCP server.

This file is a small golden sample of the output shape spawn is designed to
produce. It keeps the logic deliberately simple so the generated server contract
is easy to inspect.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("issue-triage-mcp")

IssueCategory = Literal["bug", "feature", "security", "ops", "unknown"]


class IssueClassification(TypedDict):
    category: IssueCategory
    confidence: float
    reason: str


@mcp.tool()
def classify_issue(issue_text: str) -> IssueClassification:
    """Classify an issue using a small deterministic keyword heuristic."""
    text = issue_text.lower()

    if any(term in text for term in ["cve", "token", "secret", "credential", "vulnerability"]):
        return {
            "category": "security",
            "confidence": 0.85,
            "reason": "Security-sensitive terms were found in the issue text.",
        }

    if any(term in text for term in ["crash", "error", "traceback", "failed", "bug"]):
        return {
            "category": "bug",
            "confidence": 0.78,
            "reason": "Failure or defect terms were found in the issue text.",
        }

    if any(term in text for term in ["add", "support", "feature", "enhancement"]):
        return {
            "category": "feature",
            "confidence": 0.72,
            "reason": "Enhancement-oriented terms were found in the issue text.",
        }

    if any(term in text for term in ["deploy", "backup", "runtime", "service", "pipeline"]):
        return {
            "category": "ops",
            "confidence": 0.70,
            "reason": "Operational terms were found in the issue text.",
        }

    return {
        "category": "unknown",
        "confidence": 0.35,
        "reason": "No strong category signal was found.",
    }


@mcp.tool()
def create_triage_checklist(category: IssueCategory) -> list[str]:
    """Create a short triage checklist for the issue category."""
    checklists: dict[IssueCategory, list[str]] = {
        "security": [
            "Check for exposed credentials or sensitive data.",
            "Identify affected systems and blast radius.",
            "Preserve logs and evidence before changing state.",
            "Escalate if exploitation is plausible.",
        ],
        "bug": [
            "Reproduce the failure with the smallest input.",
            "Capture logs, stack traces, and environment details.",
            "Identify recent changes touching the failing path.",
            "Add or update a regression test.",
        ],
        "feature": [
            "Clarify the user outcome and acceptance criteria.",
            "Check whether an existing tool or workflow already covers it.",
            "Scope the smallest useful version.",
            "Define test or demo evidence for completion.",
        ],
        "ops": [
            "Confirm current runtime/service state.",
            "Check deployment, backup, and rollback paths.",
            "Identify monitoring or alert gaps.",
            "Record operational follow-up actions.",
        ],
        "unknown": [
            "Ask for a clearer reproduction or desired outcome.",
            "Collect examples, logs, or screenshots.",
            "Assign an initial owner for classification.",
        ],
    }
    return checklists[category]


@mcp.tool()
def write_triage_report(issue_text: str) -> str:
    """Classify an issue and write a short triage report."""
    classification = classify_issue(issue_text)
    checklist = create_triage_checklist(classification["category"])
    checklist_md = "\n".join(f"- {item}" for item in checklist)

    return (
        f"## Triage report\n\n"
        f"**Category:** {classification['category']}\n\n"
        f"**Confidence:** {classification['confidence']:.2f}\n\n"
        f"**Reason:** {classification['reason']}\n\n"
        f"### Checklist\n\n{checklist_md}\n"
    )


if __name__ == "__main__":
    mcp.run()
