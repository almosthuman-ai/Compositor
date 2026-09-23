# Third-party software

The Windows application is built on the following projects. Their licenses remain separate from Compositor's MIT license.

| Project | Purpose | Source and license |
| --- | --- | --- |
| Qt / PySide6 / Shiboken | Native interface and optional embedded browser | [Qt for Python](https://code.qt.io/cgit/pyside/pyside-setup.git/), LGPL/GPL/commercial terms supplied with the distribution |
| Pillow | Raster image I/O and operations | [Pillow](https://github.com/python-pillow/Pillow), HPND |
| NumPy | Pixel arithmetic | [NumPy](https://github.com/numpy/numpy), BSD-3-Clause |
| OpenCV | Selection and retouching operations | [OpenCV](https://github.com/opencv/opencv), Apache-2.0 |
| psd-tools | Photoshop import | [psd-tools](https://github.com/psd-tools/psd-tools), MIT |
| pillow-heif / libheif | HEIF import | [pillow-heif](https://github.com/bigcat88/pillow_heif), see package and bundled library license files |
| MCP Python SDK | Agent tool protocol | [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), MIT |
| keyring | Windows credential storage | [keyring](https://github.com/jaraco/keyring), MIT |
| PyInstaller | Standalone packaging | [PyInstaller](https://github.com/pyinstaller/pyinstaller), GPL with bootloader exception |
| Codex | Optional ChatGPT integration runtime | [OpenAI Codex](https://github.com/openai/codex), Apache-2.0 |
| Glitch Temple | Glitch treatments, sorting, character fields and animation algorithms | [Tai Mei / Glitch Temple](https://github.com/taimei886/glitch-temple), MIT; original sources and attribution retained in `windows/glitch-engine/vendor` |
| imageio-ffmpeg | Locating the bundled animation encoder | [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg), BSD-2-Clause |
| FFmpeg | Separate executable for GIF and MP4 export | [FFmpeg 7.1](https://github.com/FFmpeg/FFmpeg/tree/n7.1), GPL-3.0-or-later for the bundled Gyan essentials build; see `third-party-licenses/ffmpeg` |

Qt libraries are shipped as separate dynamic libraries in `_internal`. Their original binaries and notices are preserved. Source for matching versions is available from the linked upstream projects. The package's `third-party-licenses` directory contains the installed dependency license texts collected during the build. Codex, when installed through the application, remains in a separate per-user runtime directory.

This list identifies the principal components. The collected license texts include their dependencies and govern the corresponding components.

Glitch Temple's Canvas engine runs locally through Qt WebEngine. Compositor retains its recipe format and original effect algorithms; its Qt controls, document ownership and export pipeline are adaptations. The Processing engine is not included. Qt WebEngine also includes Chromium components under their respective notices, available through its `qtwebengine://credits` page and the [matching Qt sources](https://download.qt.io/official_releases/qt/).
