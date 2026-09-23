# Compositor Windows module map

Public open-source Windows 10 image editor derived from Robbie Tilton's MIT-licensed Compositor. Upstream Swift/AppKit/Metal sources remain intact; the Windows implementation replaces those platform facilities with Qt, Pillow, NumPy and OpenCV. This is a native Windows reimplementation within the fork, not SwiftUI running on Windows.

The public app runs independently of the Axiomatic workspace. General editing, generation and MCP are core capabilities. Owen & Vic is an optional local-service connector. Per-user state lives under `%LOCALAPPDATA%/Compositor`, overridable through `COMPOSITOR_DATA` for isolated verification.

| Owner | Source | Contract |
| --- | --- | --- |
| Document and history | `windows/compositor/document.py` | Single transactional document model; immutable pixel references, editable raster/text/shape/gradient/adjustment/group layers, masks, selections, transforms, paint/retouch, file formats and bounded in-memory undo. |
| Rendering | `windows/compositor/pixels.py` | sRGB RGBA compositing, 20 blend modes, shapes/text/gradients, layer effects, filters and adjustments. Mirrors upstream transform and blend intent with Windows libraries. |
| Shared workspace | `windows/compositor/workspace.py` | Qt owner thread; both native UI and HTTP/MCP enter the same dispatch. Open documents, revisions, recovery, generation application, inspection and optional connector. |
| Native editor | `windows/compositor/ui.py`, `windows/compositor/chrome.py` | Qt canvas with pixel rulers, original vector tool icons, direct color selection, stacked Color/Properties/Layers inspector and optional generation, ChatGPT and project panels. Human edits use the canonical workspace commands. |
| Public production projects | `windows/compositor/projects.py`, `windows/compositor/production_ui.py` | Standalone artwork/comic/book projects, lazily loaded canonical page documents, authored prose, project direction, labeled references, portable `.compbook` files, HTML/PDF reading exports and shared human/MCP presentation. Page drafts persist separately until saved. |
| Generation | `windows/compositor/generation.py` | Configurable OpenAI-compatible and Gemini providers, immutable input capture, asynchronous jobs, actual returned dimensions, retained candidates, exact-source application and explicit recovery after interruption. No provider output-token caps. |
| Subscription collaboration | `windows/compositor/chat.py`, `windows/compositor/prompts/editor.md` | Official Codex App Server stdio; isolated managed ChatGPT OAuth, persistent conversation, MCP tools, streamed replies and native image-result ingestion. Account sign-in belongs to the user. |
| Optional runtime installation | `windows/compositor/codex_runtime.py` | Downloads the pinned official Codex Windows package when no runtime is installed; verifies registry SHA-512 integrity and extracts into per-user app storage. |
| Configuration | `windows/compositor/settings.py` | Public per-user settings; API keys in Windows Credential Manager or environment; local operator capability in a separate file. No household paths or keys in defaults. |
| Agent transport | `windows/compositor/server.py`, `windows/compositor/mcp_server.py` | Authenticated loopback command queue plus portable stdio MCP. Inspection returns images from actual document rendering. HTTP work runs on the same Qt owner and rejects stale revisions. |
| Production connector | `windows/compositor/connectors.py` | Optional Owen & Vic HTTP adapter: project listing, selected image pull, copy-back and existing authoring/generation/presentation/export operations. Never opens its canonical data in a second writer. |
| Installation | `windows/run.py`, `windows/setup.ps1`, `windows/build.ps1`, `windows/Compositor.spec`, `windows/install.ps1`, `windows/start-desktop.ps1` | Isolated dependencies, standalone GUI and console MCP binaries, per-user installation/shortcuts and independent interactive launch. Single-instance lock precedes recovery and job loading. |
| Verification | `windows/tests/` | Pixel contracts, masks, selection, blend alpha, persistence, undo, stale candidates, real Qt pointer input and HTTP-to-UI shared ownership. Tests use temporary stores and fake providers; they spend no image credits. |

## State and preservation

`.compwin` is a ZIP with versioned JSON, lossless source layers/masks, selection and a merged preview. Atomic replacement occurs only after full serialization. `.ora` adds standard OpenRaster layers for compatible documents and retains the native manifest for exact Compositor reopening; unsupported portable semantics produce an error. Imported raster originals remain untouched. Export refuses their original paths.

Recovery saves open documents and a session index under the user's app data. It is separate from an explicit document save. Generation folders retain requests, captured source/reference images, original provider bytes, normalized candidates and application provenance. The native subscription runtime stores its own authentication and conversations under the app's isolated `chat/codex` directory. Compositor never borrows the developer's Codex authentication.

## Current implementation frontier

The document, production and native UI integration has passed 44 focused tests on Windows 10. The installed GUI and packaged MCP have been exercised together: document creation, editing, stale-revision rejection, actual image inspection, layered save, exact export pixels and undo. The initial public Windows CI build also passed on a clean GitHub runner. `windows/verify_distribution.py` repeats the packaged journey in an isolated store and now includes portable project reopening and reading export.

Editor chrome is verified separately from document operations. The GUI tests exercise color selection, visibility eye controls, pixel-dimension transforms and keeping Layers visible while switching secondary panels. Rendered checks cover 1600×1000 and 1280×800 windows. The inspector retains a bounded width when a secondary panel closes. Visual review remains necessary; these checks do not establish professional finish by themselves.

Production tests verify editable page layers, prose and reference roles across a portable save/reopen, independent identities for opened copies, retained drafts through agent refreshes and restart, presentation navigation through the canonical page, and actual PDF rendering plus extractable prose. `.compbook` contains `project.json`, page `.compwin` archives and copied reference images. Local project state lives under per-user `projects/`; opened pages are owned by Workspace, and other pages load on demand.

Live OpenAI generation returned a 1024×1024 image. A separate crop edit sent a 512×512 source and retained the 1024×1024 result; application preserved every pixel outside the crop. An optional Studio push/pull round trip through a dedicated test project preserved exact pixels. Codex App Server 0.156.0 was downloaded with SHA-512 verification, initialized in an isolated app home, returned its model catalog and started/cancelled the official OpenAI OAuth flow. A signed-in conversation and subscription image generation still require account-level proof.

Remaining upstream feature gaps include automatic subject selection/background removal, perspective distortion, independently transformed linked/unlinked masks, GPU rendering, smooth pressure-aware live raster painting, richer inline typography, and several upstream import/filter details. Separable blending uses bounded strips to limit temporary memory. PSD preserves raster channels, hidden layers, opacity, groups and pixel masks; unsupported effects and modes produce conversion notes. PSD and upstream imports do not yet promise pixel-exact compatibility.

## Commands

- `powershell -File windows/setup.ps1`: install isolated Python dependencies.
- `.venv/Scripts/python.exe windows/run.py`: development GUI.
- `.venv/Scripts/python.exe windows/run.py --mcp`: stdio MCP connecting to the open app.
- `.venv/Scripts/python.exe -m pytest windows/tests -q`: focused verification.
- `powershell -File windows/build.ps1`: standalone Windows distribution in `dist/Compositor`.
- `powershell -File windows/install.ps1`: install a versioned local copy and shortcuts.
- `powershell -File windows/start-desktop.ps1`: independent Windows task launch for agent-operated installation.
