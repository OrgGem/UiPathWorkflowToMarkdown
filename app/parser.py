from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from xml.etree import ElementTree
from zipfile import ZipFile


KEY_ACTIVITY_NAMES = {
    "TypeInto",
    "Click",
    "If",
    "ForEach",
    "Assign",
    "While",
    "DoWhile",
    "Sequence",
}


@dataclass
class WorkflowData:
    """Represents a parsed UiPath workflow."""

    path: str
    display_name: str
    invoked_workflows: List[str]
    key_activities: List[str]


def get_local_name(tag: str) -> str:
    """Return the local name of an XML tag, ignoring namespaces."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def safe_extract_archive(archive_path: Path, extract_to: Path) -> Path:
    """Extract a zip/nupkg archive while preventing path traversal."""
    extract_to.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_path) as zf:
        for member in zf.infolist():
            dest_path = (extract_to / member.filename).resolve()
            if not str(dest_path).startswith(str(extract_to.resolve())):
                raise ValueError("Archive contains unsafe paths")
        zf.extractall(extract_to)
    return extract_to


def _collect_key_activities(element: ElementTree.Element, activities: List[str]) -> None:
    """Recursively collect key activity names."""
    name = get_local_name(element.tag)
    if name in KEY_ACTIVITY_NAMES:
        activities.append(element.get("DisplayName") or name)
    for child in element:
        _collect_key_activities(child, activities)


def _find_invoked_workflows(element: ElementTree.Element, workflows: List[str]) -> None:
    """Recursively collect invoked workflow file names."""
    name = get_local_name(element.tag)
    if name == "InvokeWorkflowFile":
        target = (
            element.get("WorkflowFileName")
            or element.get("WorkflowFile")
            or element.get("DisplayName")
        )
        if target:
            workflows.append(str(target))
    for child in element:
        _find_invoked_workflows(child, workflows)


def parse_workflow(xaml_path: Path, base_dir: Path) -> WorkflowData:
    """Parse a single XAML file into workflow data."""
    tree = ElementTree.parse(xaml_path)
    root = tree.getroot()

    invoked_workflows: List[str] = []
    key_activities: List[str] = []

    _find_invoked_workflows(root, invoked_workflows)
    _collect_key_activities(root, key_activities)

    relative_path = str(xaml_path.relative_to(base_dir))
    display_name = root.get("DisplayName") or xaml_path.stem

    return WorkflowData(
        path=relative_path,
        display_name=display_name,
        invoked_workflows=invoked_workflows,
        key_activities=key_activities,
    )


def parse_project(extracted_dir: Path) -> Dict[str, WorkflowData]:
    """Parse all XAML files in a directory."""
    workflows: Dict[str, WorkflowData] = {}
    for xaml_path in extracted_dir.rglob("*.xaml"):
        workflows[str(xaml_path.relative_to(extracted_dir))] = parse_workflow(
            xaml_path, extracted_dir
        )
    return workflows


def load_config(config_str: str | None) -> dict:
    """Safely parse optional JSON config string."""
    if not config_str:
        return {}
    try:
        return json.loads(config_str)
    except json.JSONDecodeError:
        return {}

