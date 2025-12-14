from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set

from .parser import WorkflowData


def generate_markdown(
    workflow_path: str,
    workflows: Dict[str, WorkflowData],
    level: int,
    llm_descriptions: Dict[str, str] | None = None,
    visited: Set[str] | None = None,
) -> List[str]:
    """
    Generate markdown lines for a workflow, integrating optional LLM descriptions.

    This matches the updated design contract where llm_descriptions is optional
    and, when provided, an AI-generated summary is shown beneath the workflow name.
    """
    visited = visited or set()
    if workflow_path in visited:
        return []
    visited.add(workflow_path)

    lines: List[str] = []
    prefix = "  " * level
    workflow_data = workflows.get(workflow_path)
    name = Path(workflow_path).name
    lines.append(f"{prefix}- **{name}**")

    if llm_descriptions and workflow_path in llm_descriptions:
        lines.append(f"{prefix}  > {llm_descriptions[workflow_path]}")

    if workflow_data and workflow_data.key_activities:
        lines.append(
            f"{prefix}  - Key activities: {', '.join(workflow_data.key_activities)}"
        )

    if workflow_data and workflow_data.invoked_workflows:
        lines.append(f"{prefix}  - Invokes:")
        for child in workflow_data.invoked_workflows:
            lines.extend(
                generate_markdown(
                    child,
                    workflows,
                    level + 2,
                    llm_descriptions=llm_descriptions,
                    visited=visited,
                )
            )
    return lines


def build_markdown(workflows: Dict[str, WorkflowData], llm_descriptions=None) -> str:
    """Build a full markdown document for parsed workflows."""
    invoked = {
        target for data in workflows.values() for target in data.invoked_workflows
    }
    roots = [path for path in workflows if path not in invoked] or list(workflows)

    lines: List[str] = ["# UiPath Project Summary"]
    visited: Set[str] = set()

    for workflow_path in sorted(roots):
        lines.extend(
            generate_markdown(
                workflow_path,
                workflows,
                level=1,
                llm_descriptions=llm_descriptions,
                visited=visited,
            )
        )
        lines.append("")

    return "\n".join(lines).strip() + "\n"

