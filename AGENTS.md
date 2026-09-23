# Compositor Windows

This is the Windows fork of Robbie Tilton's MIT-licensed Compositor. Upstream Apple implementation remains in `Compositor/`. Windows implementation belongs in `windows/`. Read `module-manifest.md`.

Goal: a public open-source Windows 10 layered art editor shared by a human and an MCP operator. General generation and refinement are standalone capabilities; Owen & Vic is an optional configured connector. No household paths, identities, private models or credentials in public defaults.

Document operations have one owner. UI and MCP dispatch the same commands on the Qt owner thread. Never mutate live state through a second engine. Imported files and Studio assets are originals. Save copies and retain generation provenance. Long generation runs in Studio's existing scheduled service and must survive an editor close.

Use the local `.venv`, keep dependencies isolated, and preserve full upstream attribution. Test actual pixels, persistence, undo, stale generation rejection, human editing and MCP. Windows scripts own launch/install. Never infer completion or parity from menus or passing structural tests.

Keep development studies in an isolated `COMPOSITOR_DATA` workspace. When actual use of the installed editor is needed, save and close documents created for that check afterward. Preserve the person's requested artwork and selected document; do not leave the editor crowded with development images.
