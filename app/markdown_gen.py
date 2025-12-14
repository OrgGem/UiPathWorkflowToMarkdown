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


def build_sequence_markdown(
    workflows: Dict[str, WorkflowData], llm_descriptions: Dict[str, str] | None = None
) -> str:
    """
    Build a Mermaid sequence diagram representing workflow invocations.

    - Each workflow is a participant.
    - Each `InvokeWorkflowFile` becomes a message from caller to callee.
    - Key activities of the callee are included as a note.
    - Optional LLM descriptions are appended in the note.
    """
    # Determine roots to start traversal (workflows that are not invoked by others)
    invoked = {t for d in workflows.values() for t in d.invoked_workflows}
    roots = [p for p in workflows if p not in invoked] or list(workflows)

    # Map workflow path to a safe Mermaid participant name
    def pname(path: str) -> str:
        return Path(path).stem.replace(" ", "_")

    # Collect all participants
    participants: List[str] = []
    for wf in sorted(workflows):
        participants.append(f"participant {pname(wf)} as {Path(wf).name}")

    lines: List[str] = ["# UiPath Project Sequence", "", "```mermaid", "sequenceDiagram"]
    lines.extend(participants)

    visited: Set[str] = set()

    def walk(caller_path: str) -> None:
        if caller_path in visited:
            return
        visited.add(caller_path)
        caller = workflows.get(caller_path)
        if not caller:
            return
        for callee_path in caller.invoked_workflows:
            lines.append(f"{pname(caller_path)}->>+{pname(callee_path)}: Invoke")
            callee = workflows.get(callee_path)
            # Add a note describing the callee's logic
            if callee:
                note_lines: List[str] = []
                if callee.key_activities:
                    note_lines.append(
                        "Key activities: " + ", ".join(callee.key_activities)
                    )
                if llm_descriptions and callee_path in llm_descriptions:
                    note_lines.append(llm_descriptions[callee_path])
                if note_lines:
                    # Use a Note over the callee participant
                    lines.append(
                        f"Note over {pname(callee_path)}: "
                        + "\\n".join(note_lines).replace("\n", " ")
                    )
            walk(callee_path)
            lines.append(f"{pname(caller_path)}<<- {pname(callee_path)}: Return")

    for root in sorted(roots):
        walk(root)

    lines.append("```")
    return "\n".join(lines).strip() + "\n"

