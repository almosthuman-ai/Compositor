# Glitch Temple engine

Tai Mei's Glitch Temple supplies the effect algorithms and recipe vocabulary. The vendored `studio.ts` and `LivePreview.tsx` are unchanged copies from the commit recorded in `vendor/commit.txt`. Their MIT license is retained beside them.

Run `.venv/Scripts/python.exe windows/build-glitch.py` from the repository root to rebuild the checked-in JavaScript bundle. The build uses pinned esbuild 0.25.12 through Node; neither Node nor esbuild is required by installed users. To update the vendored source, pass `--source` pointing to a Glitch Temple checkout with its license file.

The build extracts the original Canvas functions before the React component and enables nearest-neighbor source sampling. `bridge.ts` adds full-resolution rendering, recipe normalization and a small command interface. The Python owner supplies document layers, masks, retained originals, jobs, history and animation composition. Rendering is local in an invisible Qt WebEngine page; no web service is involved.

This integrates the Canvas algorithms. It does not promise pixel-equivalence with Glitch Temple's separate Processing renderer. PETSCII Study is its existing raster tile effect, not a byte-native C64 editor.
