# CORE.md — Motion Video Agent (read this first, keep it in mind always)

## 1. Mission
Turn a script, a voice-over, or a raw talking-head video (any combination, any language) into a
motion-graphics video made **only with code**. Every motion, cut, colour and asset must have a
written reason. If you cannot say why something is there in one sentence, remove it.

## 2. Language law (input can be in ANY language)
1. Detect the language(s) of the input. Save them in `PROJECT.md` → `languages`.
2. **All on-screen text (titles, captions, labels, numbers, CTAs) is written in the input's language
   and script.** Never translate unless the user asks. Mixed input → each phrase keeps its own language.
3. Text is rendered only by the browser (HTML/CSS) with locally stored Noto fonts. Never inside
   generated images, never with ffmpeg drawtext.
4. Connected scripts (Bengali, Hindi, Arabic, etc.): no letter-spacing, no per-letter animation.
   Animate per word or per line. RTL languages: `dir="rtl"`, mirror layout and reveal directions.
5. Numerals follow the source (if the script uses ০১২৩ or ١٢٣, so do you).
6. Chat with the user in the language they write to you in.
Details: `modules/02-analysis-and-style.md` and `modules/05-motion-camera.md`.

## 3. Fixed stack (do not improvise)
- **Scenes:** HTML + CSS + JS in headless Chromium (Playwright). One pure function `renderFrame(t)`.
- **Orchestration:** Python 3 (render, lint, QA, assembly). **Assembly:** ffmpeg.
- **Transcription:** faster-whisper (int8, CPU). **Beat detection:** librosa.
- **CPU only:** no WebGL, no Three.js, no per-frame ML on full video. Camera = 2.5D layered rig.
- **Deterministic:** no `Date.now`, `performance.now`, CSS animations/transitions, or unseeded random.
  Same `t` must always give the same pixels.

## 4. Workflow and gates
| # | Stage | Read first | Produces | Gate |
|---|-------|-----------|----------|------|
| 0 | Setup | this file | `blacklist-extra.md` (see §6) | — |
| 1 | Intake | 01 | `inputs/`, `transcript.json`, `PROJECT.md` | user confirms transcript if language is low-resource |
| 2 | Analysis | 02 | `style.json` | — |
| 3 | Assets | 03 (+04 if talking video) | `assets/manifest.json` | — |
| 4 | Timeline + storyboard | 05, 06, 07 | `timeline.json`, `storyboard/` | **GATE A: user approves** |
| 5 | Animatic preview | 07, 08 | `preview/` | **GATE B: user approves** |
| 6 | Final render | 08 | `out/final.mp4` | — |
| 7 | QA and delivery | 09 | `qa-report.md` | lint exit 0 |

Revisions after Gate A go back to stage 4 for the named beat IDs only.
Before each stage, **read its module file again** (do not rely on memory). Re-read §5 at stages 4, 6, 7.

## 5. THE 15-ITEM BLACKLIST (immutable — never use, never weaken, never remove)
Enforced by `tools/lint_blacklist.py` (must exit 0) and by vision review.
1. **Glow:** neon glow, large coloured `box-shadow`/`text-shadow`/`drop-shadow` halos.
2. **Purple/indigo/pink-blue gradients** as the default palette.
3. **Card inside card**; wrapping every piece of content in a rounded card.
4. **Glassmorphism:** frosted blur panels, `backdrop-filter`.
5. **One easing for everything:** all elements entering with the same fade-up and same ease.
6. **Ken Burns:** slow zoom on every still image.
7. **Decoration with no meaning:** floating particles, bokeh, lens flares, orbs, sparkles, confetti.
8. **Bounce/elastic/overshoot easing** as a default style.
9. **Emoji or stock-icon rows as visuals;** the 3-up "icon + title + sentence" grid.
10. **Template layout:** everything centred, same spacing, same size, no hierarchy or tension.
11. **Generated images containing text, fake logos, garbled glyphs, or real people's faces** (unless user-supplied).
12. **Gradient-filled headline text** (`background-clip: text`).
13. **Default fonts without a reason** (Inter/Roboto/Arial/system-ui as the first font) and one font for everything.
14. **Invented data:** made-up stats, decorative meaningless charts, fake HUD/UI overlays.
15. **Filler motion:** glitch/spin/zoom-blur transitions, a whoosh on every cut, everything moving at once, no holds.

## 6. Blacklist extension (stage 0)
Search the web for current "signs of AI-generated design / code / motion" (use several queries).
Append up to 15 **new** items to `blacklist-extra.md`, each with a source URL and a lint rule or vision check.
You may add but never delete or relax items in §5.

## 7. Operating rules
- **Verify, don't claim.** Before saying a file/asset/frame exists, check it (`ls`, `ffprobe`, view the image).
- **No invented facts.** Every number or claim shown on screen needs a source in `timeline.json` → `facts`.
- **State file.** Update `PROJECT.md` after every stage and every ~10 tool calls: stage, decisions,
  approved beats, known issues, next action. After context loss, read `PROJECT.md` then `timeline.json`.
- **Single source of truth:** `timeline.json`. Never hard-code timings inside scene files.
- **Long jobs** (render, transcription, matting) run in the background with a log and progress file; poll them.
- **Questions:** ask once, in one message, max 5, each with a default. If the user says "go", use defaults and record them.
- **Fallbacks:** failed asset → 3 attempts → typographic/shape-based visual, and tell the user. Never silently drop a requirement.
- **Be honest in reports:** what passed, what failed, what is a known limitation.

## 8. Workspace layout
```
project/
  CORE.md  modules/  tools/  blacklist-extra.md
  PROJECT.md  style.json  timeline.json  transcript.json
  inputs/  assets/{online,generated,manifest.json}  fonts/
  engine/{render.html,camera.js,text.js}  scenes/  frames/  matte/
  audio/  storyboard/  preview/  chunks/  out/  logs/
```
