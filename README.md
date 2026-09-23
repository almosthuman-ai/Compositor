# Compositor for Windows

An open-source image editor for layered artwork, comics, pixel art and glitch art, with a ChatGPT collaborator that can edit the same document you are working on.

[Download the Windows preview](https://github.com/almosthuman-ai/Compositor/releases/tag/v0.1.0-preview.1) · [Getting started](windows/QUICK_START.md) · [Full guide](windows/README.md) · [Report an issue](https://github.com/almosthuman-ai/Compositor/issues)

![Compositor's Windows editor](windows/docs/editor.png)

## Install

Choose **Setup.exe** from the release for a normal installation with Desktop and Start Menu shortcuts. Or extract the entire **Portable.zip** and open `Compositor.exe` inside the Compositor folder. Both downloads include the editor, MCP tools and animation encoder. Windows 10 or later, 64-bit, is required; Python, Node and terminal setup are not.

The editor works without an account. To collaborate with ChatGPT, open its panel and sign in. Compositor installs the official Codex runtime and connects its editing tools automatically. Available models and subscription image generation depend on your account. API image providers are configured separately.

## Make art

- **Layered editing:** paint, select, mask, transform and combine images with editable text, shapes, adjustments and blend modes. Save `.compwin` files to keep the layers.
- **Pixel art:** draw with a hard-edge pencil, convert larger images onto a logical pixel grid, limit the palette and export with whole-number nearest-neighbor enlargement. Conversion gives you a starting point for pencil cleanup.
- **Glitch Temple:** combine Tai Mei's 18 Canvas effects, retain the original image and recipe, and export GIF or MP4 loops. Pixel finishing can keep an animation within the document palette.
- **Comics and books:** organize pages, attach character references and give a project a reusable visual style. Inspect and revise the instructions assembled for image generation. Portable `.compbook` files carry pages and references together.
- **AI collaboration:** ask the embedded ChatGPT collaborator to inspect and edit your artwork, or connect an external MCP client to the same tools. Document commands work without moving your mouse or typing through the desktop.

The optional Owen & Vic Studio connector can exchange artwork with an existing studio service. General editing and generation work without it.

## Preview status

This Windows edition is under active development. It does not yet cover every Photoshop or upstream Compositor feature. PSD imports preserve supported layers and report conversions; retain your originals and inspect the result. Automatic subject selection, perspective distortion, independently transformed masks and GPU rendering remain unfinished. See the [module map](module-manifest.md) for current implementation boundaries.

Settings, recovery and ChatGPT history live under `%LOCALAPPDATA%/Compositor`, separately from the program. Save your artwork explicitly as `.compwin` or `.compbook` files to keep portable copies.

## Build and contribute

The Windows implementation lives in `windows/`. Follow the [source setup and build guide](windows/README.md#run-from-source). Build the animation encoder from the [pinned sources](windows/encoder/README.md), then run:

```powershell
powershell -File windows/build.ps1
.venv/Scripts/python.exe windows/package_release.py
```

The packaging script creates the installer, portable ZIP and checksums in `dist/releases`. The Windows workflow builds these same downloads. The [module map](module-manifest.md) explains the shared document owner, native interface, generation and MCP connection.

## Credits and license

Original [Compositor](https://github.com/robbietilton/Compositor) by **Robbie Tilton**. [Glitch Temple](https://github.com/taimei886/glitch-temple) by **Tai Mei**. Windows edition developed by **[Legion](https://legion.tw)** and contributors.

The editor is [MIT licensed](LICENSE). Dependencies retain their own licenses; [third-party notices](windows/THIRD_PARTY_NOTICES.md) and license texts ship with the downloads. The separate animation encoder includes its complete corresponding source archive and build instructions.

The original Apple source remains in `Compositor/`, with its [Mac documentation preserved here](docs/upstream-macos.md). Windows features and installation instructions belong to this fork's guide.

Legion builds software around the way you actually work. [Show us the ugly workflow.](https://legion.tw)
