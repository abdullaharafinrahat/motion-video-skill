# motion-video-skill

An agent skill for making motion-graphics videos **purely with code** from a script, a voice-over, or a raw talking-head video, in any language.

Design: a small always-loaded `CORE.md`, one module per stage (read on demand), a state file, a single `timeline.json` source of truth,
approval gates (storyboard, animatic), and a code-level linter for a 15-item "AI-slop" blacklist.

## Use
Copy this folder into the agent's workspace, then tell the agent:
> Read CORE.md fully, then follow its workflow. Read each module before its stage.

## Contents
| Path | Purpose |
|------|---------|
| `CORE.md` | mission, language rules, fixed stack, workflow gates, immutable 15-item blacklist |
| `modules/01..09` | intake, analysis/style, assets, talking video, camera/motion, audio, storyboard, render, QA |
| `tools/lint_blacklist.py` | blacklist linter for scenes, `timeline.json`, asset manifest (exit 0 required) |
| `tools/render.py` | deterministic chunked CPU renderer (Playwright + ffmpeg); resumable, content-hashed chunks, `--preview`, `--beats B05-B09`, `--benchmark` |
| `tools/ripple.py` | change one beat's duration and shift the rest |

## Requirements
Python 3, `pip install playwright && playwright install chromium`, ffmpeg. The agent writes `engine/render.html` (exposes `window.renderFrame(t)`) in stage 4.
Optional per module: faster-whisper, librosa, rembg/MediaPipe, a TTS and image-generation tool, depending on what the agent has.

## Status
`lint_blacklist.py`, `ripple.py` and `render.py` (final, preview, per-beat preview, resume) were smoke-tested with a minimal Bengali scene.
The modules are prompts and have not been validated against many real projects yet.
