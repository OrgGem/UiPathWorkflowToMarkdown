# UiPath Workflow To Markdown

Upload a UiPath project archive (`.zip` or `.nupkg`) and receive a Markdown document that visualizes the workflow structure. Optional LLM enrichment can add human-readable summaries.

## Architecture

- **Backend**: Python/FastAPI in `/app` - Headless API server
- **Frontend**: Vue.js 3 + TypeScript in `/ui` - Modern SPA
- **Production**: Single Docker container serving both API and UI on port 8000

## Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- npm

### Backend Development

Install dependencies and start the FastAPI server:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

**API Documentation**: `http://localhost:8000/docs`

### Frontend Development

Install dependencies and start the Vite dev server:

```bash
cd ui
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` with hot-reload enabled.

The Vite dev server proxies API requests to `http://localhost:8000` (ensure backend is running).

### Development Workflow

1. Start the backend: `uvicorn app.main:app --reload`
2. In a new terminal, start the frontend: `cd ui && npm run dev`
3. Access the UI at `http://localhost:5173`
4. Make changes and see them reflected immediately

## Production Deployment

### Build Docker Image

The project uses a multi-stage Docker build that:
1. Builds the Vue.js frontend (Stage 1)
2. Copies the built assets into the Python backend image (Stage 2)

```bash
docker build -t uipath-workflow-markdown .
```

### Run Docker Container

```bash
docker run -p 8000:8000 uipath-workflow-markdown
```

Access the application at `http://localhost:8000`

Both the UI and API are served from the same port in production.

## API Usage

### Upload and Analyze Endpoint

```bash
curl -X POST "http://localhost:8000/analyze/upload/" \
  -F "file=@/path/to/project.zip" \
  -F 'config={"use_llm": false}'
```

**Parameters:**
- `file`: UiPath project archive (`.zip`/`.nupkg`)
- `config` (optional): JSON string for configuration

**Example with LLM enrichment:**

```json
{
  "use_llm": true,
  "llm_provider": "openai_compatible",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1"
}
```

The response is returned as `text/markdown` with an `analysis.md` attachment.

### Ingest Pre-processed Files Endpoint

For frontend applications that pre-process XAML files client-side:

```bash
curl -X POST "http://localhost:8000/api/workflows/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [{
      "path": "Main.xaml",
      "size": 2048,
      "checksum": "abc123...",
      "content": "&lt;?xml version=\"1.0\"?&gt;...",
      "llmProcessed": false
    }]
  }'
```

**File object structure:**
- `path`: Relative path in the project
- `size`: File size in bytes
- `checksum`: SHA-256 checksum
- `content`: XAML file content (raw or LLM-processed)
- `llmProcessed`: Boolean indicating if LLM preprocessing was applied

## Frontend Features

The Vue 3 frontend provides:

- **Client-side Archive Extraction**: Upload `.zip` or `.nupkg` files, extract XAML workflows using JSZip
- **File Management**: View discovered files with checksums and content
- **Optional LLM Preprocessing**: Process files with OpenAI-compatible endpoints (API keys stay in browser)
- **Modern UI**: Dark theme with glassmorphism effects inspired by factory.ai

See `ui/README.md` for detailed frontend documentation.

## License

MIT License - see LICENSE file for details.
