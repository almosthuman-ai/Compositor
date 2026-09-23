# Start creating in Compositor

For the portable download, extract the entire ZIP and open `Compositor.exe` inside the Compositor folder. Keep `_internal` and `Compositor-Tools.exe` beside it. The setup download creates Desktop and Start Menu shortcuts for you.

Compositor runs on 64-bit Windows 10 or later. You do not need Python, Node or a terminal. The editor works without an account.

Preview executables are unsigned. Windows may show an unknown-publisher warning when you open them.

- **Open artwork:** use File → Open, or create a document with File → New. Save as `.compwin` to retain editable layers. Export PNG, JPEG or WebP for sharing.
- **Draw pixel art:** choose File → New pixel canvas. Use the Pixel pencil for hard edges. Image → Convert to pixel art creates a separate palette-limited study from an existing image.
- **Use Glitch Temple:** choose Filters → Glitch Temple. Apply a treatment, then export an animated GIF or MP4. Pixel enlargement in Recipe exports solid pixel blocks at a whole-number scale.
- **Work with ChatGPT:** open the ChatGPT panel and choose Sign in with ChatGPT. Required support installs automatically. Image generation availability follows your account; API providers are configured separately in Settings.
- **Use Gemini Pro Image:** in Settings, choose Google Gemini API and Gemini 3 Pro Image (Nano Banana Pro). Add your Google API key once, then choose Google Gemini API in the Generate panel. Resolution and aspect ratio are available in Image provider settings.
- **Edit part of an image:** draw a rectangular or freehand selection and click Edit with AI in the selection toolbar, or right-click the canvas and choose Edit selected area with AI. Enter your prompt, choose your provider and generate a candidate. Inspect it, then Apply to add a masked layer while preserving pixels outside the selection. Ctrl+Alt+G opens the same controls. API requests go directly to the selected image provider.
- **Make comics or books:** open Projects to organize pages, character references and a shared visual style. Save a `.compbook` to carry the project between computers.

This is a preview release. PSD imports can convert unsupported Photoshop features; inspect the conversion notes and preserve your originals. Windows stores settings and recovery separately from the application, under `%LOCALAPPDATA%/Compositor`.

[Guide and current capabilities](https://github.com/almosthuman-ai/Compositor/blob/windows-studio/windows/README.md) · [Report an issue](https://github.com/almosthuman-ai/Compositor/issues) · [Legion](https://legion.tw)
