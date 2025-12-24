# UiPath Workflow To Markdown

Upload a UiPath project archive (`.zip` or `.nupkg`) and receive a Markdown document that visualizes the workflow structure. Optional LLM enrichment can add human-readable summaries.

## Features

### Core Parsing & Analysis
- **XAML Workflow Parsing**: Extract and analyze UiPath workflow files from `.zip` or `.nupkg` archives
- **Hierarchical Workflow Structure**: Automatically detect workflow invocation chains and display as nested structure
- **Activity Detection**: Identify and list key activities (TypeInto, Click, If, ForEach, Assign, While, etc.)
- **Logic Flow Visualization**: Hierarchical representation of workflow logic with branch annotations (Then/Else/Case)
- **Control Flow Analysis**: Detect control structures (FlowDecision, FlowSwitch, Switch, TryCatch, Parallel, etc.)
- **Safe Archive Extraction**: Path traversal protection when extracting uploaded archives

### Output Formats
- **Markdown List Format**: Hierarchical list view with workflow structure, activities, and logic flow (default)
- **Mermaid Sequence Diagrams**: Generate interactive sequence diagrams showing workflow invocations with Mermaid syntax
  - Set `"format": "sequence"` in config to enable

### AI Enhancement (Optional)
- **LLM-Powered Summaries**: Generate human-readable business purpose descriptions for each workflow
- **OpenAI-Compatible APIs**: Supports OpenAI and compatible endpoints (local LLMs, Azure, etc.)
- **Configurable Models**: Choose any model (default: gpt-4o-mini)
- **Privacy-Focused**: API keys only used server-side when explicitly provided
- **Graceful Fallback**: Core parsing works without LLM - AI is purely optional

### Frontend Features (Vue 3 SPA)
- **Client-Side Archive Processing**: Extract and analyze workflows in the browser using JSZip
- **File Management**: View discovered XAML files with paths, sizes, and SHA-256 checksums
- **Frontend LLM Processing**: Optional client-side LLM preprocessing with custom prompts (API keys stay in browser)
- **Selective Processing**: Choose which files to process and send to backend
- **Live Preview**: View generated Markdown analysis with download option
- **Modern UI**: Dark theme with glassmorphism effects, gradient accents, and smooth animations

### API Endpoints
- **`/analyze/upload/`**: Upload archive, get Markdown analysis (supports both formats and LLM)
- **`/api/workflows/ingest`**: Accept pre-processed XAML files from frontend for backend-only parsing
- **`/docs`**: Interactive API documentation (FastAPI/Swagger)

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

**Configuration Options:**
- `use_llm` (boolean): Enable LLM-powered workflow summaries (default: false)
- `api_key` (string): API key for LLM provider (required if use_llm is true)
- `base_url` (string): Base URL for OpenAI-compatible API (optional)
- `model` (string): Model to use (default: "gpt-4o-mini")
- `prompt` (string): Custom system prompt for LLM analysis (optional)
- `use_source` (boolean): When true, send raw XAML content for richer markdown-style summaries
- `format` (string): Output format - "list" (default) or "sequence" (Mermaid diagram)

**Example with LLM enrichment:**

```json
{
  "use_llm": true,
  "llm_provider": "openai_compatible",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini"
}
```

**Environment variable configuration (optional):**
- `LLM_USE_LLM=true` to enable backend LLM enrichment without passing config
- `OPENAI_API_KEY` or `LLM_API_KEY` for authentication
- `LLM_BASE_URL` / `OPENAI_BASE_URL` and `LLM_MODEL` / `OPENAI_MODEL` to customize endpoints and models
- `LLM_PROMPT` to override the system prompt
- `LLM_USE_SOURCE=true` to send raw XAML to the model for markdown-friendly analysis

**Example with Mermaid sequence diagram:**

```json
{
  "use_llm": false,
  "format": "sequence"
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

## Supported UiPath Activities

The parser recognizes and extracts the following activity types:

**Key Activities:**
- TypeInto, Click, Assign
- If, Switch, While, DoWhile, ForEach
- Sequence

**Control Flow & Logic:**
- InvokeWorkflowFile
- FlowDecision, FlowSwitch
- TryCatch, Catch, Finally
- Pick, Parallel
- Flowchart, FlowStep
- StateMachine, State

The logic flow visualization includes branch annotations (Then/Else/Case/Default) to show conditional paths.

## Frontend Features

The Vue 3 frontend provides:

- **Client-side Archive Extraction**: Upload `.zip` or `.nupkg` files, extract XAML workflows using JSZip
- **File Management**: View discovered files with checksums and content
- **Optional LLM Preprocessing**: Process files with OpenAI-compatible endpoints (API keys stay in browser)
- **Modern UI**: Dark theme with glassmorphism effects inspired by factory.ai

See `ui/README.md` for detailed frontend documentation.

## License

MIT License - see LICENSE file for details.
