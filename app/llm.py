from __future__ import annotations

from typing import Dict

from .parser import WorkflowData


def enrich_with_llm(
    parsed_data: Dict[str, WorkflowData], config: dict | None
) -> Dict[str, str]:
    """
    Optionally enrich parsed workflows with LLM-generated summaries.

    If config is falsy, missing use_llm flag, or lacks an api_key, an empty
    dictionary is returned so the core functionality works without AI.
    """
    if not config or not config.get("use_llm"):
        return {}

    api_key = config.get("api_key")
    if not api_key:
        return {}

    base_url = config.get("base_url")

    try:
        from openai import OpenAI
    except ImportError:
        return {}

    client = OpenAI(api_key=api_key, base_url=base_url)
    model = config.get("model") or "gpt-4o-mini"
    summaries: Dict[str, str] = {}

    for workflow_path, workflow in parsed_data.items():
        prompt = (
            "You are an expert UiPath developer. Based on the following XAML file "
            "summary, write a concise, one-sentence description of its business purpose in English.\n"
            f"Workflow Path: {workflow_path}\n"
            f"It invokes: {', '.join(workflow.invoked_workflows) or 'none'}\n"
            f"It contains key activities like: {', '.join(workflow.key_activities) or 'none'}\n"
            "Business Purpose Summary:"
        )
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=80,
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
