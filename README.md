# UiPath Workflow To Markdown

Upload a UiPath project archive (`.zip` or `.nupkg`) and receive a Markdown document that visualizes the workflow structure. Optional LLM enrichment can add human-readable summaries without impacting the core parsing flow.

## Backend (FastAPI)

### Install and run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Analyze a project

```bash
curl -X POST "http://localhost:8000/analyze/upload/" \
  -F "file=@/path/to/project.zip" \
  -F 'config={"use_llm": false}'
```

- `file`: UiPath project archive (`.zip`/`.nupkg`)
- `config` (optional): JSON string. Example enabling AI:

```json
{
  "use_llm": true,
  "llm_provider": "openai_compatible",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1"
}
```

The response is returned as `text/markdown` with an `analysis.md` attachment.

## Frontend

A minimal React-based UI is available at `frontend/index.html`. Open it in a browser, upload the archive, optionally enable AI descriptions, and download the resulting Markdown.
