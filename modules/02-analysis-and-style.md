# 02 — Analysis, style, colour, editing psychology

Output: `style.json`. Every choice carries a `why`.

## A. Analyse the topic
Answer in `style.json.analysis`: topic, audience, platform behaviour, emotional arc
(e.g. curiosity → tension → clarity → action), the **one** idea the viewer must remember,
and cultural context of the language/region.

## B. Pick an energy level (1–5) and a personality
| Level | Name | Cut rhythm | Camera | Type | Typical topics |
|------|------|-----------|--------|------|----------------|
| 1 | Minimal / calm | 4–10 s holds | one slow move per scene, mostly still | large, airy, few words | reflection, luxury, health, education |
| 2 | Editorial | 3–6 s | gentle push/pan, parallax | confident serif/sans pairing | explainers, journalism, history |
| 3 | Balanced | 2–4 s | purposeful moves, some drift | mixed scale | product, business, how-to |
| 4 | Energetic | 1.2–2.5 s | frequent moves, drift on every hold | big kinetic words, hard cuts | tech, sports, motivation |
| 5 | High energy | 0.6–1.8 s | continuous camera, whips, punch-ins | huge type, cuts on beat | hype, promos, shorts/reels |
Energy may change across the video (arc). Record the level per beat.

## C. Colour theory (decide before designing)
- **60 / 30 / 10:** dominant (background), secondary (surfaces/shapes), accent (one emphasis colour used rarely).
- Pick the relationship on purpose: monochrome (calm), analogous (harmony), complementary (tension/emphasis),
  split-complementary (energy with control). State which and why.
- Start from the topic's emotion and the culture of the audience, not from a trendy palette.
  Check cultural meaning (e.g. white = mourning in parts of Asia, red = luck in China / danger elsewhere, green = Islam/nature).
- Contrast: text vs background ≥ 4.5:1 (≥ 3:1 for huge type). Do not rely on red/green alone.
- Avoid the blacklist defaults (purple-blue gradients, neon on black). Prefer flat colour, real photographic colour, or one restrained gradient from analogous hues.
- Write palette as hex with roles: `bg, surface, ink, muted, accent`.

## D. Typography and fonts (multilingual)
- Use Noto families per script, downloaded once to `fonts/` and loaded with `@font-face` from local files
  (Noto Sans/Serif Bengali, Devanagari, Arabic / Naskh / Kufi, SC/JP/KR, Thai, Tamil, etc.). Never use a CDN at render time.
- Pair two fonts at most: one display, one text, chosen for the topic (blacklist item 13). Latin fallback goes second in the stack.
- Type scale ratio (e.g. 1.333), max 3 sizes per scene. Line-height 1.15–1.3 (Indic/Arabic need 1.4+).
- Letter-spacing 0 for connected scripts; CJK uses `line-break: strict`.
- Verify glyph coverage with fontTools (`cmap`) for every on-screen string before rendering.

## E. Editing psychology — rules with reasons
| Rule | Why | Constraint |
|------|-----|-----------|
| Hook in the first 3 s: strongest image/claim/question first | attention drop-off is steepest early | no logo intros |
| Pattern interrupt every 6–10 s (energy ≥ 3) or 12–20 s (≤ 2) | renews attention | change one thing: scale, angle, layout, or sound |
| Emphasise keywords only (≤ 1 emphasis per ~5 s) | emphasis everywhere = nothing | emphasis = scale, colour, or hold |
| Push-in toward a subject on serious reveals | approach signals importance and intimacy | only for the key reveal of a section |
| Pull-out for context, relief or conclusion | widening resolves tension | |
| Hold after a key line (≥ 0.4 s) | gives time to absorb | |
| Cut on a beat, on an action, or in a speech pause | cuts feel motivated | never mid-word |
| One idea per beat; ≤ 7 words on screen (≤ 14 CJK characters) | reading while listening is limited | captions are separate from titles |
| Reading time ≥ 0.25 s per word + 0.4 s | text must be readable | |
| Contrast between beats (loud/quiet, wide/close, busy/empty) | rhythm | |
| End with resolution or a clear action | memory favours endings | |

## F. Output `style.json`
```json
{
  "analysis": {"topic": "", "audience": "", "arc": [], "core_idea": "", "culture_notes": ""},
  "energy": {"default": 3, "per_section": []},
  "palette": {"bg": "", "surface": "", "ink": "", "muted": "", "accent": "", "scheme": "", "why": ""},
  "type": {"display": "", "text": "", "scale": 1.333, "scripts": ["bn"], "why": ""},
  "motion": {"eases": ["named curves, max 4"], "personality": "", "why": ""},
  "languages": ["bn"], "fps": 30, "size": [1920, 1080]
}
```
