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

### Ingest pre-processed files

For frontend applications that pre-process XAML files (e.g., with client-side LLM), use the `/api/workflows/ingest` endpoint:

```bash
curl -X POST "http://localhost:8000/api/workflows/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [{
      "path": "Main.xaml",
      "size": 2048,
      "checksum": "abc123...",
      "content": "<?xml version=\"1.0\"?>...",
      "llmProcessed": false
    }]
  }'
```

This endpoint accepts an array of file objects with:
- `path`: Relative path in the project
- `size`: File size in bytes
- `checksum`: SHA-256 checksum
- `content`: XAML file content (raw or LLM-processed)
- `llmProcessed`: Boolean indicating if LLM preprocessing was applied

## Frontend

### Modern Vue 3 UI (Recommended)

A modern Vue 3 + Vite frontend with factory.ai-inspired styling is available in the `ui/` directory.

**Features:**
- Client-side archive extraction using JSZip
- XAML file discovery with checksums
- Optional LLM preprocessing with OpenAI-compatible endpoints (API key stays in browser)
- Dark, glassy theme with gradient accents
- Backend integration via `/api/workflows/ingest`

**Setup:**

```bash
cd ui
npm install
npm run build
```

The built UI is automatically served at `http://localhost:8000/` when the FastAPI server is running.

For development with hot-reload:

```bash
cd ui
npm run dev
```

See `ui/README.md` for more details.

### Legacy React UI

A minimal React-based UI is also available at `frontend/index.html`. Open it in a browser, upload the archive, optionally enable AI descriptions, and download the resulting Markdown.
