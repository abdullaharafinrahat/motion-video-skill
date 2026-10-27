# 04 — Talking-head video (CPU-only pipeline)

Read only when the user supplied raw talking video.

## 1. Prepare frames
```
ffmpeg -i inputs/raw.mp4 -vf "fps=30,scale=1920:-2" -q:v 2 frames/%05d.jpg
```
Frames are shown **by index** inside the scene (`frames/00123.jpg`), never via a `<video>` element
(seeking is not frame-exact). Original audio is muxed from the source file. Never retime video and
audio separately; lip-sync must be preserved.

## 2. Background removal (matte) — try in this order
1. **Chroma key** if the background is a flat green/blue (detect by sampling frame edges).
   `ffmpeg -vf "chromakey=0x00FF00:0.12:0.08,despill"` or in-canvas keying. Best quality, cheapest.
2. **MediaPipe selfie segmentation** (CPU, milliseconds per frame). Good default for a single person.
   Then refine: threshold, 1 px erode, 2 px feather, **temporal smoothing** (average mask with previous and next frame).
3. **rembg (u2net_human_seg / silueta)** on every frame at ≤ 640 px, parallel across cores. Slow: measure s/frame on 10 frames
   and tell the user the ETA before starting. Run as a background job.
4. **No matte fallback:** keep the original background. Use depth tricks that do not need a cutout:
   split layouts, picture-in-frame, masked shape reveals, vignette, graphics placed beside the speaker.
Save masks to `matte/%05d.png` (alpha). Never claim a clean cutout without the QA below.

## 3. Matte QA (mandatory)
- Composite 10 spread-out frames on a magenta background; view them. Look for edge halos, missing hair/hands, holes, shoulders cut off.
- Flicker test: compute mask area per frame; if frame-to-frame change > 8% outside real movement, increase smoothing.
- If failing after 2 fixes, use fallback 4 and tell the user why.

## 4. Editing the talking video (use word timestamps)
- Remove dead air > 0.5 s and filler words only if the cut lands in a pause and audio is crossfaded (≥ 20 ms).
- Hide jump cuts with alternating framing (100% / 112% punch-in) rather than leaving identical-frame jumps.
- **Reveal moment** (speaker states the topic): slow camera push toward the face (scale 1.0 → 1.08 over the sentence),
  background dims/desaturates, topic title appears **between** background plate and person (depth sandwich:
  bg plate → big title → speaker matte). Reason: seriousness + depth.
- Cover with B-roll or graphics when the speaker refers to something concrete; keep the voice continuous (J/L cuts).
- Replace the background with something related to the topic only if the matte passes QA; otherwise darken/blur the original.
- Keep faces clear: no text or graphics over eyes/mouth; captions go in the lower third (or per platform safe zones in 05).
- Captions: language of the speech, word-level highlight using transcript timestamps, max 2 lines, max ~42 Latin chars per line
  (~20 CJK, adapt for Indic widths by measuring in the browser).

## 5. Scene layer order (back → front)
`bg plate` → `bg graphics` → `title/word layers` → `speaker matte` → `fg graphics` → `captions`
Each layer has a `z` for the camera rig (see 05).
