# Compositor for Windows

A layered image editor for Windows 10, with generative editing and tools an AI collaborator can use on the same canvas as you.

This edition is in active development. It preserves Robbie Tilton's original Mac application in the repository and provides a separate Windows implementation. See [current capabilities and remaining work](../module-manifest.md) before relying on a feature for production.

## Run from source

Install Python 3.11 for Windows, then run:

```powershell
git clone https://github.com/almosthuman-ai/Compositor.git
cd Compositor
git switch windows-studio
powershell -ExecutionPolicy Bypass -File windows/setup.ps1
.venv/Scripts/pythonw.exe windows/run.py
```

The editor works without an account. Save `.compwin` documents to retain editable layers, masks, typography, adjustments and generation provenance. Export PNG, JPEG, WebP or TIFF for other applications. Imported originals stay intact.

## Build a standalone app

```powershell
powershell -File windows/build.ps1
powershell -File windows/install.ps1
```

The build creates `dist/Compositor/Compositor.exe` and a console companion, `Compositor-Tools.exe`, for MCP. Keep both beside the `_internal` directory. The installer creates Desktop and Start Menu shortcuts; the installed app does not require Python.

## ChatGPT in the editor

Open the ChatGPT panel and choose **Sign in with ChatGPT**. Compositor uses OpenAI's official [Codex App Server](https://learn.chatgpt.com/docs/app-server) to manage sign-in, authentication refresh and the conversation. If Codex is absent, the app downloads the official Windows runtime and verifies its published checksum. Compositor keeps its sign-in and conversation separate from other Codex installations.

ChatGPT can inspect the canvas and use the same editing operations as the application. Its available models and native image generation depend on the signed-in account. Native image results appear as retained candidates in Generate. Subscription access is separate from API billing; signing in does not provide an Images API key.

Runtime installation, initialization, model discovery and the official OAuth start/cancel flow have been verified on Windows 10. Signed-in conversation and subscription image generation still need account-level verification.

## Image providers

In Settings, choose an OpenAI-compatible or Gemini provider, enter its image model and save your API key. Keys are stored in Windows Credential Manager; `OPENAI_API_KEY` and `GEMINI_API_KEY` environment variables are also supported. A compatible OpenAI endpoint can be configured for another provider.

Generate a new image, edit the composite, or refine a selected region. Region edits send the exact crop and your chosen references. Candidates retain their inputs, prompt, provider and native dimensions. Applying a candidate adds a layer; if you changed its source while it was generating, the app keeps the candidate for manual placement.

## Use with any MCP client

Start Compositor, then configure a stdio MCP server:

```json
{
  "mcpServers": {
    "compositor": {
      "command": "C:/path/to/Compositor/Compositor-Tools.exe",
      "args": ["--mcp"]
    }
  }
}
```

For development, use the repository's `.venv/Scripts/python.exe` as the command and pass the absolute `windows/run.py` path followed by `--mcp`.

The tools expose workspace inspection, document creation and opening, layer and pixel operations, selections, masks, undo/redo, image inspection, generation, candidate application, saving and export. `compositor_prepare_generation` captures source images for a collaborator's own image-generation tools. Edits can carry `expectedRevision` to reject stale assumptions. The local connection uses a per-user authentication token; tools do not return credentials.

## Artwork, comics and books

The Projects panel creates standalone artwork, comics and illustrated books with up to 64 pages. Every page is a layered document. Add prose and a prompt to each page, set project-wide story and art direction, and add reference images labeled as character, style or composition. Page generation uses that direction and those references; the result remains a candidate until you apply it.

Projects save locally as you work. **Save** creates a portable `.compbook` containing all pages, editable layers, prose and references. Opening a portable copy creates a separate project, preserving any version already open. Page text drafts survive refreshes, page switches and restarts.

Export a self-contained HTML reading copy or a PDF with artwork and prose. **Present** opens a full-screen view with page navigation and an optional two-panel comic layout. Human navigation and MCP selection use the same page. These features work without a connected Studio service.

## Connect an existing studio

Owen & Vic Studio can be connected through its local service URL in Settings. Existing projects remain owned by that service. Bring a selected image into the editor, edit its layers, and return the composite as a new project image. Its existing enhancement and production operations remain available through the connector.

## Recovery and local data

Settings, recovery snapshots, generated candidates and chat history live in `%LOCALAPPDATA%/Compositor`. `COMPOSITOR_DATA` selects an alternate store for testing or a separate installation. Unsaved documents reopen from recovery; an explicit Save creates your chosen project file. Failed or interrupted requests remain visible in Generate and are never retried automatically.

## Development

```powershell
.venv/Scripts/python.exe -m pytest windows/tests -q
.venv/Scripts/python.exe windows/verify_distribution.py dist/Compositor
```

Tests use isolated stores and simulated image providers. They do not require accounts or spend image credits. The [module map](../module-manifest.md) identifies the shared document owner, rendering, UI, generation, chat, connector and operator surfaces.

The fork retains the [MIT license](../LICENSE). Runtime dependencies keep their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.md).
