from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple
from xml.etree import ElementTree
from zipfile import ZipFile


KEY_ACTIVITY_NAMES = {
    "TypeInto",
    "Click",
    "If",
    "ForEach",
    "Assign",
    "MultipleAssign",
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
    logic_flow: List[Tuple[int, str]] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    raw_xml: str | None = None


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


def _collect_components(element: ElementTree.Element, components: List[str]) -> None:
    """Recursively collect activity/component display names."""
    name = get_local_name(element.tag)
    display = element.get("DisplayName")
    if display or name:
        label = display or name
        if display and display != name:
            label = f"{label} [{name}]"
        elif not display:
            label = name
        components.append(label)
    for child in element:
        _collect_components(child, components)


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


LOGIC_ACTIVITY_NAMES = KEY_ACTIVITY_NAMES | {
    # Control and orchestration activities we want to surface in logic flow
    "InvokeWorkflowFile",
    "FlowDecision",
    "FlowSwitch",
    "Switch",
    "TryCatch",
    "Catch",
    "Finally",
    "Pick",
    "Parallel",
    "State",
    "StateMachine",
    "Flowchart",
    "FlowStep",
    "MultipleAssign",
}


def _branch_label(name: str) -> str | None:
    """Return a normalized branch label when applicable."""
    label = name.split(".")[-1]
    return label if label in {"Then", "Else", "Case", "Default"} else None


DETAIL_ATTRS = (
    "Condition",
    "ExpressionText",
    "Expression",
    "Value",
    "Text",
    "VBExpression",
    "CSharpExpression",
)

MAX_DETAIL_LENGTH = 180

CONFIG_KEYS = {
    "use_llm",
    "llm_provider",
    "api_key",
    "base_url",
    "model",
    "format",
    "prompt",
    "use_source",
}


def _filter_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return only recognized configuration keys."""
    return {k: v for k, v in data.items() if k in CONFIG_KEYS}


def _extract_logic_detail(element: ElementTree.Element) -> str | None:
    """Extract a concise detail string from common expression-bearing nodes."""
    tag_name = get_local_name(element.tag)

    if tag_name == "MultipleAssign":
        detail = _extract_multiple_assign_detail(element)
        if detail:
            return detail

    for attr in DETAIL_ATTRS:
        val = element.get(attr)
        if val and val.strip():
            return val.strip()

    for child in element:
        child_name = get_local_name(child.tag).split(".")[-1]
        if child_name in {"Condition", "Expression", "Value", "Text", "Code", "Statement"}:
            content = (child.text or "").strip()
            if not content:
                for grandchild in child.iter():
                    if grandchild is child:
                        continue
                    candidate = (grandchild.text or "").strip()
                    if candidate:
                        content = candidate
                        break
            if content:
                return content[:MAX_DETAIL_LENGTH] + (
                    "…" if len(content) > MAX_DETAIL_LENGTH else ""
                )
    return None


def _first_text(element: ElementTree.Element) -> str | None:
    """Return the first meaningful text within an element or its descendants."""
    if element.text and element.text.strip():
        return element.text.strip()
    for child in element.iter():
        if child is element:
            continue
        if child.text and child.text.strip():
            return child.text.strip()
    return None


def _find_child_text(
    element: ElementTree.Element, target_names: set[str], max_depth: int = 3
) -> str | None:
    """Find the first text content from matching child names up to a depth."""
    stack: List[Tuple[ElementTree.Element, int]] = [(child, 1) for child in element]
    while stack:
        current, depth = stack.pop()
        child_name = get_local_name(current.tag).split(".")[-1]
        if child_name in target_names:
            text = _first_text(current)
            if text:
                return text
        if depth < max_depth:
            for child in current:
                stack.append((child, depth + 1))
    return None


def _extract_multiple_assign_detail(element: ElementTree.Element) -> str | None:
    """Collect assignment pairs within a MultipleAssign activity."""
    assignments: List[str] = []

    def _walk(node: ElementTree.Element, is_root: bool = False) -> None:
        node_name = get_local_name(node.tag).split(".")[-1]
        if not is_root and node_name == "MultipleAssign":
            return

        if node_name == "Assign":
            target = node.get("To")
            if not target:
                target = _find_child_text(node, {"To"}) or "[target]"

            value = node.get("Value")
            if not value:
                value = _find_child_text(
                    node, {"Value", "Expression", "ExpressionText"}
                )

            if value is None:
                return

            statement = f"{target} = {value}".strip()
            if len(statement) > MAX_DETAIL_LENGTH:
                statement = statement[:MAX_DETAIL_LENGTH] + "…"
            assignments.append(statement)
            return

        for child in node:
            _walk(child)

    _walk(element, is_root=True)

    if assignments:
        return "; ".join(assignments)
    return None


def _collect_logic_flow(
    element: ElementTree.Element,
    steps: List[Tuple[int, str]],
    depth: int = 0,
    branch_label: str | None = None,
) -> None:
    """Recursively collect a hierarchical logic flow with branch annotations."""
    tag_name = get_local_name(element.tag)
    display = element.get("DisplayName")
    should_record = tag_name in LOGIC_ACTIVITY_NAMES or (
        display is not None and tag_name not in {"Activity"}
    )

    current_depth = depth
    if should_record:
        label = f"{branch_label}: " if branch_label else ""
        text = f"{label}{display or tag_name}"
        if display and display != tag_name:
            text = f"{text} [{tag_name}]"
        detail = _extract_logic_detail(element)
        if detail:
            text = f"{text}: {detail}"
        steps.append((depth, text))
        current_depth = depth + 1

    for child in element:
        child_name = get_local_name(child.tag)
        label_name = _branch_label(child_name)
        if label_name:
            for nested in child:
                _collect_logic_flow(
                    nested, steps, current_depth, branch_label=label_name
                )
        else:
            _collect_logic_flow(child, steps, current_depth, branch_label=None)


def parse_workflow(xaml_path: Path, base_dir: Path) -> WorkflowData:
    """Parse a single XAML file into workflow data."""
    raw_xml = xaml_path.read_text(encoding="utf-8", errors="ignore")
    tree = ElementTree.parse(xaml_path)
    root = tree.getroot()

    invoked_workflows: List[str] = []
    key_activities: List[str] = []
    logic_flow: List[Tuple[int, str]] = []
    components: List[str] = []

    _find_invoked_workflows(root, invoked_workflows)
    _collect_key_activities(root, key_activities)
    _collect_components(root, components)
    for child in root:
        _collect_logic_flow(child, logic_flow)

    relative_path = str(xaml_path.relative_to(base_dir))
    display_name = root.get("DisplayName") or xaml_path.stem

    return WorkflowData(
        path=relative_path,
        display_name=display_name,
        invoked_workflows=invoked_workflows,
        key_activities=key_activities,
        logic_flow=logic_flow,
        components=components,
        raw_xml=raw_xml,
    )


def parse_project(extracted_dir: Path) -> Dict[str, WorkflowData]:
    """Parse all XAML files in a directory."""
    workflows: Dict[str, WorkflowData] = {}
    for xaml_path in extracted_dir.rglob("*.xaml"):
        workflows[str(xaml_path.relative_to(extracted_dir))] = parse_workflow(
            xaml_path, extracted_dir
        )
    return workflows


def _env_bool(name: str) -> bool | None:
    """Return a boolean from an environment variable when set."""
    raw = os.getenv(name)
    if raw is None:
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_config(config_input: str | Dict[str, Any] | None) -> dict:
    """Safely parse optional JSON config string or dict."""
    if isinstance(config_input, dict):
        parsed = dict(config_input)
    elif config_input:
        try:
            parsed = json.loads(config_input)
        except json.JSONDecodeError:
            parsed = {}
    else:
        parsed = {}

    parsed = _filter_config(parsed) if isinstance(parsed, dict) else {}

    env_defaults = {
        "use_llm": _env_bool("LLM_USE_LLM") or _env_bool("USE_LLM"),
        "api_key": os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
        "model": os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL"),
        "format": os.getenv("OUTPUT_FORMAT"),
        "prompt": os.getenv("LLM_PROMPT"),
        "use_source": _env_bool("LLM_USE_SOURCE"),
    }

    config: dict = {}
    for key, value in env_defaults.items():
        if value is not None:
            config[key] = value

    config.update(parsed)

    if config.get("use_llm") and not config.get("base_url"):
        config["base_url"] = "https://api.openai.com/v1"

    return config
