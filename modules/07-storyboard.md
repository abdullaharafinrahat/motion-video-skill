# 07 — Timeline, storyboard, animatic, revisions

Re-read CORE §5 now. `timeline.json` is the **only** place for timing, text, assets, camera and sound.

## A. `timeline.json` schema
```json
{
  "meta": {"fps": 30, "size": [1920,1080], "duration": 62.4, "languages": ["bn"], "energy_default": 3},
  "facts": [{"id": "F1", "text": "…", "source_url": "…"}],
  "beats": [{
    "id": "B07", "start": 18.40, "end": 21.10, "energy": 4,
    "speech": "exact words spoken (original language)",
    "purpose": "reveal the topic",
    "why": "push-in because the speaker names the topic; signals seriousness",
    "layers": [
      {"id": "L1", "type": "image", "asset": "A03", "z": 400, "x": 0, "y": 0, "scale": 1.1},
      {"id": "L2", "type": "text", "text": "on-screen text in input language", "z": 100, "role": "title", "reveal": "mask_up"},
      {"id": "L3", "type": "matte_video", "frames": "frames", "matte": "matte", "z": 0}
    ],
    "camera": {"move": "push_in", "from": {"z": 0}, "to": {"z": 180}, "ease": "in_out_cubic", "why": ""},
    "transition_out": {"type": "hard_cut", "why": "cut on the pause"},
    "hits": [{"t": 18.55, "sfx": "impact_soft", "why": "title lands"}],
    "facts": ["F1"],
    "status": "draft"
  }]
}
```
Rules: beats are contiguous, no gaps/overlaps (except deliberate L/J audio overlaps), start/end snap to frames, every beat has `why`,
any on-screen number/claim lists `facts`. `status`: draft → approved → rendered.

## B. Stage 4 — Storyboard (before any animation is rendered)
1. Build `timeline.json` from transcript, style, assets, and the motion/audio modules.
2. Run `python tools/lint_blacklist.py .` and fix everything.
3. Render **keyframe stills** with the real scene code: for each beat the mid frame, and for camera moves also the first and last frames.
   Size 960×540 (or 540×960).
4. Build the **contact sheet(s)** `storyboard/sheet_01.png…`: 6 beats per sheet; each tile labelled with beat ID, time range, camera move, energy, asset source, and the one-line `why`.
   Also `storyboard/storyboard.md`: a table of all beats (ID, time, speech, visual, camera, sound, why).
5. Present the sheets and the table to the user. Say clearly what you assumed. **Stop and wait for approval (Gate A).**

## C. Stage 5 — Animatic (cheap preview)
- 480p (or 480×854), 12 fps, scratch audio (VO + music, no final mix), no motion blur, same scene code.
- `python tools/render.py --preview` renders everything; `--beats B05-B09 --preview` renders only those beats so the user can see a part of the video before the full render (output `preview/B05-B09.mp4`).
- Present the preview, wait for approval (Gate B).

## D. Revisions by beat ID
User says e.g. "B07: slower, different image, bigger title".
1. Edit only B07 in `timeline.json` (duration, asset, text, camera).
2. Run the ripple script: downstream `start/end` shift and the audio timeline updates automatically. List what moved.
3. Re-run lint, re-render the stills (and preview clip) only for the changed beats.
4. Show before/after tiles. Never modify approved beats that the user did not mention; if a ripple forces a change, ask.
5. Append the change to `PROJECT.md` → `revision_log`.
