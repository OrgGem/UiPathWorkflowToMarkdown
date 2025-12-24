# UiPath Workflow Analyzer - Vue 3 Frontend

A modern Vue 3 + Vite + TypeScript frontend for analyzing UiPath workflows with factory.ai-inspired styling.

## Features

- **Archive Upload**: Upload `.zip` or `.nupkg` files and extract XAML workflows client-side using JSZip
- **File Management**: View discovered XAML files with path, size, and SHA-256 checksums
- **LLM Preprocessing**: Optional frontend LLM processing using OpenAI-compatible endpoints
  - API keys stay in the browser (never sent to backend)
  - Configure model IDs and custom system prompts
  - Configure custom system prompts
  - Process selected files with chat completions
- **Backend Integration**: Send raw or LLM-processed files to backend via `/api/workflows/ingest`
- **Modern UI**: Dark theme with glassy, gradient design inspired by factory.ai

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **Vite** - Lightning-fast build tool
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **JSZip** - Client-side ZIP file handling
- **Web Crypto API** - SHA-256 checksum computation

## Development

Install dependencies:

```bash
npm install
```

Run development server:

```bash
npm run dev
```

Build for production:

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

## Components

- **UploadCard**: Handle archive upload, extraction, and XAML file discovery
- **FilesCard**: Display and manage discovered XAML files
- **LLMCard**: Configure and run LLM preprocessing on selected files
- **ProcessCard**: Send files to backend and display results

## Configuration

The Vite dev server proxies API requests to the FastAPI backend running on `http://localhost:8000`.

See `vite.config.ts` for proxy configuration.

## Styling

The UI uses Tailwind CSS v4 with a custom dark theme featuring:
- Dark background with gradient overlays
- Glassmorphism effects (backdrop blur, transparency)
- Purple/blue/pink gradient accents
- Smooth transitions and animations

Custom styles are defined in `src/style.css`.
