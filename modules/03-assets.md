# 03 — Assets (online and generated)

Re-read CORE §5 items 6, 7, 11, 14 before starting.

## Choose the source per beat
- **Online image:** real things: places, products, events, objects, historical scenes, nature.
- **Generated image:** concepts, metaphors, abstract backgrounds, textures, illustrative plates, anything that must match the palette.
- **Code-drawn (SVG/CSS):** shapes, diagrams, charts, icons that need exact control. Prefer this over weak images.
- **Real people:** only faces the user supplied, or public-domain/editorial images with a clear licence. Never generate a real person's face.
- Each beat's `asset_need` in `timeline.json` states what the image must show and why.

## Online assets: search, download, verify
1. Search order (prefer free licences): Wikimedia Commons, NASA/government archives, Openverse, Pexels, Pixabay, Unsplash.
   Search queries in English **and** in the video's language.
2. Download the original size. Record `source_url`, `author`, `license` in `assets/manifest.json`.
3. **Verification test (all must pass):**
   - Resolution: ≥ frame size × (max camera scale in that beat). Full-bleed 1080p with a 1.3x push-in needs ≥ 2500 px wide.
   - **Relevance:** view the image yourself. Score 0–5 against `asset_need` on: subject match, context (place/era/culture) match, no misleading implication. **Pass ≥ 4.** Write one sentence of reasoning.
   - No visible watermark, stock-site overlay, UI chrome, or burnt-in text/logos (unless the logo *is* the subject and licence allows).
   - Not a famous-person lookalike used out of context; not culturally inappropriate for the audience.
4. Reject on any failure and log `rejected: reason`. Try up to 3 candidates, then switch to generated or code-drawn.

## Generated assets
1. **Style lock first:** create `assets/generated/style_ref.png` that matches `style.json` (palette, lighting, rendering style). Store the exact prompt prefix in `style.json.motion.image_prompt_prefix` and reuse it in every prompt.
2. Prompts always end with: "no text, no letters, no logos, no watermark, no people's faces" (unless people are required and fictional).
3. View every output. Reject for: any text-like marks, warped hands/faces/objects, off-palette colours, clutter, or mismatch with `asset_need` (same 0–5 relevance test, pass ≥ 4).
4. Max 3 attempts per asset, then fallback to code-drawn visual.
5. For parallax, generate **layers**: background plate, midground element, foreground element. For stills, cut out elements with `rembg` (fine on CPU for single images). Check the edges at 200% zoom.

## Preparation
- Convert to WebP/JPEG sized to ≤ 2x frame width to keep Chromium fast; keep originals.
- Decide focal point (x, y) per asset for camera targeting; store in manifest.
- Colour-grade in CSS/canvas to sit inside the palette (same tone curve across all photos), not per-image random filters.

## `assets/manifest.json`
```json
[{
  "id": "A03", "source": "online", "path": "assets/online/A03.jpg",
  "source_url": "", "author": "", "license": "CC0",
  "width": 4200, "height": 2800, "relevance": 5, "relevance_reason": "",
  "focal": [0.62, 0.40], "used_in": ["B05"]
},{
  "id": "A04", "source": "generated", "path": "assets/generated/A04.webp",
  "prompt": "", "text_in_image": false, "has_real_face": false,
  "relevance": 4, "relevance_reason": "", "focal": [0.5, 0.5], "used_in": ["B06"]
}]
```
`tools/lint_blacklist.py` rejects entries that violate these fields.
