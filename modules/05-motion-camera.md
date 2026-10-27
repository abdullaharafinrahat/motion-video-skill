# 05 — Motion language and the virtual camera (2.5D, CPU-friendly)

Re-read CORE §5 items 5, 6, 8, 15 before designing motion.

## A. Scene contract (engine)
Every scene is plain HTML/CSS/JS. The renderer calls one function per frame:
```js
// engine/render.html
window.renderFrame = async (t) => {      // t in seconds, pure: same t => same pixels
  const beat = beatAt(TIMELINE, t);      // TIMELINE is inlined from timeline.json
  const cam  = cameraAt(beat, t);        // {x, y, z, rot, focus}
  for (const L of beat.layers) applyLayer(L, cam, t);
  await Promise.all([...document.images].map(i => i.decode().catch(()=>{})));
  await document.fonts.ready;
};
```
No CSS animations/transitions, no timers, no `Math.random()` (use `seeded(seed)`), no real clock.
Easing and interpolation are plain functions of progress `p = clamp((t - t0)/(t1 - t0), 0, 1)`.

## B. Camera rig math
Layers sit at depth `z` (0 = focal plane, larger = farther). The camera has `x, y, z, rot, focus`.
```js
function applyLayer(L, cam, t) {
  const f = 1000;
  const d = Math.max(0.05, 1 + (L.z - cam.z) / f);   // cam.z increasing = push-in
  const s = (L.scale ?? 1) / d;
  const px = (L.x - cam.x) / d, py = (L.y - cam.y) / d;
  L.el.style.transform =
    `translate3d(${px}px,${py}px,0) rotate(${(L.rot ?? 0) - cam.rot}deg) scale(${s})`;
  const blur = Math.abs(L.z - cam.focus) * (L.blurK ?? 0.004);   // rack focus
  L.el.style.filter = blur > 0.3 ? `blur(${blur.toFixed(2)}px)` : "none";
}
```
- Parallax comes for free: far layers move less than near layers.
- Keep ≤ 6 layers per beat and use blur on ≤ 2 (CPU cost).
- Handheld shake = sum of 3 sines at fixed incommensurate frequencies × seeded phase, amplitude ≤ 4 px at 1080p.
- Fast moves: approximate motion blur with a directional `blur()` proportional to velocity. Full sub-frame accumulation only for hero moves (it is 4x cost).

## C. Camera move vocabulary (each needs a stated purpose)
| Move | Meaning | Use when |
|------|---------|----------|
| push-in | importance, seriousness, intimacy | key reveal, emotional line |
| pull-out | context, relief, conclusion | end of section, "bigger picture" |
| pan / slide | relationship between two things | comparisons, lists in space |
| drift (≤ 2 % scale per second) | life during holds | only in energy ≥ 3 holds |
| whip pan | fast transition with direction | energy ≥ 4, motivated by the sentence |
| rack focus | shifts attention between depths | subject A → subject B |
| handheld | urgency, rawness | energy ≥ 4, tense moments |
| tilt/roll (≤ 4°) | unease | rare, once or twice |
| hold | let it land | after key lines |
No two consecutive beats may use the same move unless the repetition is the point (note why).

## D. Easing and timing system (define once in `style.json`)
- Max **4 named curves** per project, e.g. `out_expo` (entrances), `in_out_cubic` (camera), `in_quad` (exits), `linear` (drift).
- Duration ranges: entrance 0.35–0.7 s, exit 0.2–0.4 s, camera move 0.8–3 s, stagger 40–90 ms.
- Different element roles get different treatments (title: mask reveal; support text: slide 24 px; shape: scale from anchor; image: wipe or camera arrival).
- Every move ends in a **hold ≥ 0.3 s**. Enter and exit must not overlap on the same element.
- Prefer reveals by clip/mask/translate over opacity-only fades. Text animates per word or line (never per letter for connected scripts).

## E. Layout system
- 12-column grid, margins 6 % of width, baseline unit 8 px at 1080p.
- Safe zones: keep text inside 90 % of the frame. For 9:16, avoid top 10 %, bottom 20 %, right 12 % (platform UI).
- Create hierarchy by scale contrast (≥ 2x between levels), asymmetry, and negative space (blacklist item 10).
- RTL languages: mirror layout; reveals move right → left.

## F. Editing grammar
Hard cut (default), jump cut (talking video), smash cut (silence → loud), whip (energy), iris/mask (topic change),
match cut (shape morphs into the next scene's shape), L/J cut (audio leads or trails picture).
A transition must be motivated by the sentence or the beat; the default is a hard cut.

## G. Data visuals
Use only user-supplied or sourced numbers (`facts` in timeline). Draw by animating the stroke/bars from zero, label directly
(no legends when avoidable), no 3D charts, no decorative charts. If a number cannot be sourced, show the claim as words instead.
