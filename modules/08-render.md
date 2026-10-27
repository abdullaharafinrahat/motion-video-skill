# 08 — Render (CPU, deterministic, chunked, background)

**Blacklist reminder (CORE §5):** glow · purple gradients · card-in-card · glass blur · one easing for all · Ken Burns ·
meaningless decoration · bounce · emoji/icon grids · template layout · text/faces in generated images · gradient text ·
default fonts · invented data · filler motion. Run `python tools/lint_blacklist.py .` first; it must exit 0.

## Pipeline
1. **Pre-flight:** lint passes; fonts present and cover all text; every asset in the manifest exists; approvals recorded in `PROJECT.md`.
2. **Benchmark:** render 20 frames, measure seconds/frame, compute ETA = frames × s/frame ÷ workers, and tell the user.
3. **Split** the timeline into chunks of ~5 s (at beat boundaries when possible). Workers = `min(cpu_count − 1, RAM_GB ÷ 1.2)`.
4. **Each worker** (own Chromium page, viewport = video size, `device_scale_factor=1`):
   `await page.evaluate("t => window.renderFrame(t)", t)` → screenshot (PNG for final, JPEG q95 for preview) → pipe into ffmpeg
   (`-f image2pipe -framerate FPS -i -`) → `chunks/chunk_###.mp4` (`libx264 -crf 12 -preset veryfast -pix_fmt yuv420p`, intermediate).
   Frame time is `t = frame_index / fps` computed with integers, never accumulated floats.
5. **Concat** chunks: `ffmpeg -f concat -safe 0 -i chunks.txt -c copy video_nosound.mp4`.
6. **Final encode + mux:** `-c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709`
   `-c:a aac -b:a 192k -movflags +faststart`. Audio from `audio/final_mix.wav`.
7. Output `out/final.mp4` (and `out/final_vertical.mp4` etc. only if requested).

## Rules
- **Run renders as background jobs**: `nohup python tools/render.py … > logs/render.log 2>&1 &`, write progress to `logs/progress.json`, poll every 30–60 s. Never block on a long foreground command.
- **Resumable:** skip chunks that already exist and pass `ffprobe`. After a crash, re-render only missing chunks.
- **Determinism check:** render the first frame of a chunk twice; hashes must match. If not, a clock/random/animation leak exists: find and fix it.
- Decode all images before screenshot; wait for `document.fonts.ready`; disable CSS animations globally (`*{animation:none!important;transition:none!important}`).
- Memory: if a worker is killed (OOM), halve the worker count and resume.
- Banding on gradients/dark areas: add a very low-amplitude seeded dither layer only if banding is visible in QA.
- Never write "done" until `ffprobe out/final.mp4` shows the expected duration, resolution, fps and audio stream.

## Failure policy
Asset fails to load → use the beat's fallback visual and flag it. Scene throws → capture the console log and a screenshot, fix, re-render that chunk only.
