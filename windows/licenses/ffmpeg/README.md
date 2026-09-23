# FFmpeg binary provenance

The Windows imageio-ffmpeg 0.6.0 wheel supplies `ffmpeg-win-x86_64-v7.1.exe`, reporting FFmpeg 7.1, Gyan essentials build, built with GCC 14.2.0 and GPL/version3 enabled. It runs as a separate process. Compositor does not link FFmpeg into its Python modules.

- Wrapper and wheel: https://github.com/imageio/imageio-ffmpeg/tree/v0.6.0
- Encoder source: https://github.com/FFmpeg/FFmpeg/tree/n7.1
- Build distribution, configuration and external library sources: https://www.gyan.dev/ffmpeg/builds/
- Build archive: https://github.com/GyanD/codexffmpeg/releases/tag/7.1
- GPL text: `COPYING.GPLv3.txt`

The encoder's license is separate from Compositor's MIT license. Public binary releases must make the matching corresponding encoder and dependency sources available alongside the release, including the build configuration. Local development builds collect these notices; they are not a public binary release.
