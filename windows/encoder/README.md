# Compositor animation encoder

Compositor runs FFmpeg as a separate process for GIF and MP4 export. This build includes FFmpeg 7.1, x264 at the commit in `sources.json`, and zlib 1.3.1. It enables only the image sequences, filters and codecs used by the editor. It uses Windows system libraries and needs no separate runtime installation.

The encoder is GPL-2.0-or-later; x264 uses GPL-2.0-or-later and zlib retains its own license. Their license texts accompany the executable. Compositor's editor code remains MIT licensed.

Every application package includes `encoder-sources.zip` beside the encoder, containing the complete corresponding source archives and build scripts. `manifest.json` records the executable, source archive and build-script hashes. The archive also records compiler versions and the encoder configuration.

## Build on Windows

Install MSYS2 with the MINGW64 GCC toolchain, make and pkgconf. Use Python 3.11.8 or later and Git for Windows. From the repository root:

```powershell
.venv/Scripts/python.exe windows/encoder/prepare.py
C:/msys64/usr/bin/bash.exe -lc 'cd /path/to/Compositor && bash windows/encoder/build.sh'
.venv/Scripts/python.exe windows/encoder/package.py
```

Use the MSYS2 path to your checkout in the shell command, such as `/c/src/Compositor`. `prepare.py` verifies the downloaded FFmpeg and zlib archives and checks out the pinned x264 commit. Outputs live under `windows/local/encoder/output`, which is ignored by Git. The Windows CI workflow performs these steps before packaging the app.

To rebuild from the accompanying source archive without network access, extract it, then extract each archive in `windows/local/encoder` into that same directory. Run `build.sh` and `package.py`; skip `prepare.py`. The build requires only the development tools listed above. Application users do not need them.
