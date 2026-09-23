# FFmpeg binary provenance

Compositor builds its separate animation encoder from pinned FFmpeg 7.1, x264 and zlib sources. It runs as a separate process; the editor does not link to it.

- Encoder source: https://github.com/FFmpeg/FFmpeg/tree/n7.1
- Build scripts and pinned dependencies: `windows/encoder` in the Compositor source repository
- Full source distribution: `_internal/encoder/encoder-sources.zip` in every application package
- Applicable license texts: `_internal/encoder/licenses`
- Binary and source hashes: `_internal/encoder/manifest.json`

This encoder build is GPL-2.0-or-later. Its license is separate from Compositor's MIT license. The source archive includes all three upstream source archives, the build scripts and the actual build's configuration and compiler versions. The earlier GPLv3 text retained here belongs to the previous Gyan encoder distribution; the current encoder's applicable texts are in its own `licenses` directory.
