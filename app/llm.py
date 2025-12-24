from __future__ import annotations

from typing import Dict, List

from .parser import WorkflowData

DEFAULT_SYSTEM_PROMPT = (
    "You are an expert UiPath developer. Provide concise, markdown-friendly summaries of workflows. "
    "Highlight business purpose, key activities, invoked workflows, and important logic/conditions."
)


def _logic_flow_as_text(logic_flow: List[tuple[int, str]]) -> str:
    """Render the collected logic flow into a readable text block."""
    lines: List[str] = []
    for depth, step in logic_flow:
        indent = "  " * depth
        lines.append(f"{indent}- {step}")
    return "\n".join(lines)


def enrich_with_llm(
    parsed_data: Dict[str, WorkflowData], config: dict | None
) -> Dict[str, str]:
    """
    Optionally enrich parsed workflows with LLM-generated summaries.

    If config is falsy, missing use_llm flag, or lacks an api_key, an empty
    dictionary is returned so the core functionality works without AI.
    """
    config = config or {}
    if not config.get("use_llm"):
        return {}

    api_key = config.get("api_key")
    if not api_key:
        return {}

    base_url = config.get("base_url") or "https://api.openai.com/v1"

    try:
        from openai import OpenAI
    except ImportError:
        return {}

    client = OpenAI(api_key=api_key, base_url=base_url)
    model = config.get("model") or "gpt-4o-mini"
    system_prompt = config.get("prompt") or DEFAULT_SYSTEM_PROMPT
    use_source = bool(config.get("use_source"))

    summaries: Dict[str, str] = {}

    for workflow_path, workflow in parsed_data.items():
        logic_text = _logic_flow_as_text(workflow.logic_flow)

        if use_source and workflow.raw_xml:
            user_content = (
                "Analyze the following UiPath XAML workflow and produce a concise markdown paragraph "
                "summarizing its purpose, key activities, invoked workflows, and noteworthy conditions. "
                "Prefer clear bullet-like sentences and keep it short.\n\n"
                f"Path: {workflow_path}\n"
                f"Raw XAML:\n```xml\n{workflow.raw_xml}\n```"
            )
        else:
            user_content = (
                "Summarize this UiPath workflow. Describe business purpose, important logic, and key activities.\n"
                f"Path: {workflow_path}\n"
                f"Invokes: {', '.join(workflow.invoked_workflows) or 'none'}\n"
                f"Key activities: {', '.join(workflow.key_activities) or 'none'}\n"
                f"Logic flow:\n{logic_text}\n\n"
                "Return a concise markdown paragraph."
            )

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                max_tokens=200,
            )
            summaries[workflow_path] = (
                completion.choices[0].message.content.strip()
                if completion.choices
                else ""
            )
        except Exception:
            # Continue without AI content if a request fails
            continue

    return summaries
