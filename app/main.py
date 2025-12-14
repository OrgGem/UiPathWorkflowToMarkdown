from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Body
from fastapi.responses import PlainTextResponse, HTMLResponse
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel

from .llm import enrich_with_llm
from .markdown_gen import build_markdown, build_sequence_markdown
from .parser import load_config, parse_project, safe_extract_archive, WorkflowData

app = FastAPI(
    title="UiPath Flow Visualizer",
    description=(
        "Upload a UiPath project (.zip/.nupkg) to generate a Markdown summary. "
        "Optional AI enrichment is supported via the config field."
    ),
)

# Serve the static frontend and make "/" return index.html
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
ui_dir = Path(__file__).resolve().parent.parent / "ui" / "dist"

# Prefer the new Vue UI if it exists, otherwise fall back to the old React frontend
assets_dir = ui_dir / "assets"
if ui_dir.exists():
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", response_class=HTMLResponse)
    def read_root():
        index_path = ui_dir / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return "<h1>Frontend not found</h1>"
elif frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir), html=True), name="static")

    @app.get("/", response_class=HTMLResponse)
    def read_root():
        index_path = frontend_dir / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return "<h1>Frontend not found</h1>"


@app.post("/analyze/upload/", response_class=PlainTextResponse)
async def analyze_upload(
    file: UploadFile = File(...), config: Optional[str] = Form(None)
):
    """Analyze an uploaded UiPath project and return a Markdown document."""
    filename = file.filename or ""
    if not filename.lower().endswith((".zip", ".nupkg")):
        raise HTTPException(
            status_code=400, detail="Only .zip or .nupkg project archives are supported."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        upload_path = Path(tmpdir) / (filename or "upload.zip")
        content = await file.read()
        upload_path.write_bytes(content)

        extract_dir = Path(tmpdir) / "extracted"
        try:
            safe_extract_archive(upload_path, extract_dir)
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        workflows = parse_project(extract_dir)
        if not workflows:
            raise HTTPException(status_code=400, detail="No XAML workflows found.")

        cfg = load_config(config)
        llm_descriptions = enrich_with_llm(workflows, cfg)
        # Choose output format: default list or Mermaid sequence diagram
        output_format = (cfg or {}).get("format")
        if output_format == "sequence":
            markdown = build_sequence_markdown(workflows, llm_descriptions or None)
        else:
            markdown = build_markdown(workflows, llm_descriptions or None)
        headers = {"Content-Disposition": 'attachment; filename="analysis.md"'}
        return PlainTextResponse(markdown, media_type="text/markdown", headers=headers)


class IngestFilePayload(BaseModel):
    """Represents a file payload from the frontend"""
    path: str
    size: int
    checksum: str
    content: str
    llmProcessed: bool = False


class IngestRequest(BaseModel):
    """Request payload for the /api/workflows/ingest endpoint"""
    files: List[IngestFilePayload]


@app.post("/api/workflows/ingest", response_class=PlainTextResponse)
async def ingest_workflows(request: IngestRequest = Body(...)):
    """
    Accept pre-processed XAML files from the frontend.
    Files include path, size, checksum, and content (raw or LLM-processed).
    Returns a Markdown analysis document.
    """
    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Convert frontend payload to WorkflowData format
    # For simplicity, we'll create a temporary directory and write files
    with tempfile.TemporaryDirectory() as tmpdir:
        extract_dir = Path(tmpdir) / "frontend_files"
        extract_dir.mkdir(parents=True, exist_ok=True)

        # Write each file to the temporary directory
        for file_payload in request.files:
            file_path = extract_dir / file_payload.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_payload.content, encoding="utf-8")

        # Parse the workflows
        workflows = parse_project(extract_dir)
        if not workflows:
            raise HTTPException(status_code=400, detail="No valid XAML workflows found")

        # Generate markdown (no additional LLM enrichment as files may already be processed)
        markdown = build_markdown(workflows, None)
        headers = {"Content-Disposition": 'attachment; filename="analysis.md"'}
        return PlainTextResponse(markdown, media_type="text/markdown", headers=headers)


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
