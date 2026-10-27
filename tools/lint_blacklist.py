#!/usr/bin/env python3
"""
Blacklist linter for the motion-video skill.

Usage:  python tools/lint_blacklist.py <project_dir>
Scans:  scenes/ and engine/ (html, css, js, svg), timeline.json, assets/manifest.json
Exit:   0 = clean, 1 = violations. NEVER edit this file to weaken a rule.
Rule IDs match the 15-item blacklist in CORE.md (B01..B15), plus INTENT and LANG.
"""
import colorsys
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

SCENE_EXT = {".html", ".htm", ".css", ".js", ".mjs", ".svg"}
SKIP_PARTS = {"vendor", "node_modules"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}
BAD_FIRST_FONTS = {"inter", "roboto", "arial", "helvetica", "helvetica neue",
                   "system-ui", "-apple-system", "segoe ui", "sans-serif", "serif"}
BANNED_TRANSITIONS = {"glitch", "spin", "zoom_blur", "cube", "page_curl", "shake_cut"}
RTL_LANGS = {"ar", "he", "fa", "ur", "ps", "sd", "yi"}

HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
GRAD = re.compile(r"(?:linear|radial|conic)-gradient\((?:[^()]|\([^()]*\))*\)", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
CARDISH = re.compile(r"(card|panel|tile)", re.I)

KEYWORDS = [
    ("B06", re.compile(r"ken[-_ ]?burns", re.I), "Ken Burns effect"),
    ("B07", re.compile(r"\b(particles?|bokeh|lens[-_ ]?flare|sparkles?|confetti|fireflies)\b", re.I),
     "meaningless decoration (particles/bokeh/flare/sparkle)"),
    ("B08", re.compile(r"\b(elastic|bounce|back\.(?:in|out|inout)|spring)\b", re.I),
     "bounce/elastic/overshoot easing"),
    ("B15", re.compile(r"\b(glitch|zoom[-_ ]?blur)\b", re.I), "filler transition (glitch/zoom-blur)"),
]


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def split_top(s):
    return re.split(r",(?![^(]*\))", s)


def hue_sat_light(hexdigits):
    h = hexdigits
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, s, l


def shadow_blur(decl):
    cleaned = re.sub(r"(rgba?|hsla?)\([^)]*\)", "", decl)
    cleaned = HEX.sub("", cleaned)
    nums = re.findall(r"-?\d+(?:\.\d+)?", cleaned)
    return float(nums[2]) if len(nums) >= 3 else 0.0


class NestChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.lines = [], []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        cls = dict(attrs).get("class") or ""
        is_card = bool(CARDISH.search(cls))
        if is_card and any(self.stack):
            self.lines.append(self.getpos()[0])
        self.stack.append(is_card)

    def handle_endtag(self, tag):
        if tag not in VOID and self.stack:
            self.stack.pop()


def lint_text_file(path, text, hits, eases):
    f = str(path)
    # B01 glow
    for m in re.finditer(r"\b(box-shadow|text-shadow)\s*:\s*([^;}]+)", text, re.I):
        limit = 24 if m.group(1).lower() == "box-shadow" else 10
        for sh in split_top(m.group(2)):
            if shadow_blur(sh) >= limit:
                hits.append(("B01", f, line_of(text, m.start()),
                             f"glow-style {m.group(1)} (blur >= {limit}px)"))
    for m in re.finditer(r"drop-shadow\(((?:[^()]|\([^()]*\))*)\)", text, re.I):
        if shadow_blur(m.group(1)) >= 20:
            hits.append(("B01", f, line_of(text, m.start()), "glow-style drop-shadow"))
    # B02 purple/indigo/pink gradients
    for m in GRAD.finditer(text):
        g = m.group(0)
        hexes = HEX.findall(g)
        hsls = [int(x) for x in re.findall(r"hsla?\(\s*(\d{1,3})", g)]
        purple = False
        for hx in hexes:
            h, s, l = hue_sat_light(hx)
            if 255 <= h <= 335 and s >= 0.35 and 0.15 <= l <= 0.85:
                purple = True
        purple = purple or any(255 <= h <= 335 for h in hsls)
        if purple and (len(hexes) + len(hsls)) >= 2:
            hits.append(("B02", f, line_of(text, m.start()), "purple/indigo/pink gradient"))
    # B03 card in card (HTML only)
    if path.suffix.lower() in {".html", ".htm", ".svg"}:
        nc = NestChecker()
        try:
            nc.feed(text)
        except Exception:
            pass
        for ln in nc.lines:
            hits.append(("B03", f, ln, "card/panel/tile nested inside another card/panel/tile"))
        # LANG
        if re.search(r"<html\b", text, re.I) and not re.search(r"<html[^>]*\blang=", text, re.I):
            hits.append(("LANG", f, 1, "<html> without lang attribute"))
    # B04 glassmorphism
    for m in re.finditer(r"backdrop-filter", text, re.I):
        hits.append(("B04", f, line_of(text, m.start()), "backdrop-filter (glassmorphism)"))
    # B09 emoji
    for m in EMOJI.finditer(text):
        hits.append(("B09", f, line_of(text, m.start()), f"emoji/pictograph '{m.group(0)}'"))
    # B10 three-up grid
    for m in re.finditer(r"repeat\(\s*3\s*,", text, re.I):
        hits.append(("B10", f, line_of(text, m.start()), "three-column grid (3-up feature layout)"))
    # B12 gradient text
    for m in re.finditer(r"background-clip\s*:\s*text", text, re.I):
        hits.append(("B12", f, line_of(text, m.start()), "gradient/clipped headline text"))
    # B13 default fonts
    for m in re.finditer(r"font-family\s*:\s*([^;}]+)", text, re.I):
        first = split_top(m.group(1))[0].strip().strip("'\"").lower()
        if first in BAD_FIRST_FONTS:
            hits.append(("B13", f, line_of(text, m.start()), f"default font first in stack: {first}"))
    # keyword rules
    for rid, rx, msg in KEYWORDS:
        for m in rx.finditer(text):
            hits.append((rid, f, line_of(text, m.start()), msg))
    for m in re.finditer(r"cubic-bezier\(\s*[-\d.]+\s*,\s*([-\d.]+)\s*,\s*[-\d.]+\s*,\s*([-\d.]+)\s*\)", text):
        y1, y2 = float(m.group(1)), float(m.group(2))
        if y1 < 0 or y1 > 1 or y2 < 0 or y2 > 1:
            hits.append(("B08", f, line_of(text, m.start()), "cubic-bezier with overshoot"))
    # collect easings for B05
    for m in re.finditer(r"""\bease\s*[:=]\s*['"]([^'"]+)['"]""", text):
        eases.append(m.group(1).strip())
    for m in re.finditer(r"cubic-bezier\([^)]*\)", text):
        eases.append(re.sub(r"\s+", "", m.group(0)))


def lint_timeline(tl, hits):
    f = "timeline.json"
    beats = tl.get("beats", [])
    langs = set(tl.get("meta", {}).get("languages", []))
    trans = []
    image_moves = []
    for b in beats:
        bid = b.get("id", "?")
        if not str(b.get("why", "")).strip():
            hits.append(("INTENT", f, 0, f"{bid}: missing 'why'"))
        cam = b.get("camera") or {}
        if cam and not str(cam.get("why", "")).strip() and cam.get("move") not in (None, "hold"):
            hits.append(("INTENT", f, 0, f"{bid}: camera move without 'why'"))
        t = (b.get("transition_out") or {}).get("type")
        if t:
            trans.append(t)
            if t in BANNED_TRANSITIONS:
                hits.append(("B15", f, 0, f"{bid}: banned transition '{t}'"))
        has_img = any(l.get("type") == "image" for l in b.get("layers", []))
        if has_img and cam.get("move"):
            image_moves.append(cam["move"])
        texts = [l.get("text", "") for l in b.get("layers", []) if l.get("type") == "text"]
        if any(re.search(r"\d|[\u09E6-\u09EF\u0966-\u096F\u0660-\u0669]", t_) for t_ in texts) and not b.get("facts"):
            hits.append(("B14", f, 0, f"{bid}: number on screen without 'facts' source"))
        if (b.get("energy") or 0) < 5 and len(b.get("hits", [])) > 3:
            hits.append(("B15", f, 0, f"{bid}: more than 3 SFX hits in one low-energy beat"))
    if len(trans) >= 5:
        top, n = Counter(trans).most_common(1)[0]
        if n / len(trans) > 0.8 and top != "hard_cut":
            hits.append(("B15", f, 0, f"transition '{top}' used on {n}/{len(trans)} beats"))
    if len(image_moves) >= 4:
        top, n = Counter(image_moves).most_common(1)[0]
        if n / len(image_moves) >= 0.6:
            hits.append(("B06", f, 0, f"same camera move '{top}' on {n}/{len(image_moves)} image beats"))
    if langs & RTL_LANGS:
        hits.append(("INFO", f, 0, "RTL language: confirm dir=rtl and mirrored reveals in scenes"))


def lint_manifest(items, hits):
    f = "assets/manifest.json"
    for a in items:
        aid = a.get("id", "?")
        if (a.get("relevance") or 0) < 4:
            hits.append(("ASSET", f, 0, f"{aid}: relevance < 4"))
        if a.get("source") == "online":
            for k in ("source_url", "license"):
                if not a.get(k):
                    hits.append(("ASSET", f, 0, f"{aid}: online asset missing {k}"))
        if a.get("source") == "generated":
            if a.get("text_in_image") is not False:
                hits.append(("B11", f, 0, f"{aid}: generated asset not confirmed text-free"))
            if a.get("has_real_face") is not False:
                hits.append(("B11", f, 0, f"{aid}: generated asset not confirmed free of real faces"))


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    hits, eases = [], []
    for d in ("scenes", "engine"):
        base = root / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in SCENE_EXT and not (set(p.parts) & SKIP_PARTS):
                try:
                    lint_text_file(p, p.read_text(encoding="utf-8", errors="ignore"), hits, eases)
                except Exception as e:
                    hits.append(("ERROR", str(p), 0, f"could not lint: {e}"))
    if len(eases) >= 8:
        top, n = Counter(eases).most_common(1)[0]
        if n / len(eases) > 0.7:
            hits.append(("B05", "scenes/", 0, f"easing '{top}' is {n}/{len(eases)} of all easings"))
    tl = root / "timeline.json"
    if tl.exists():
        try:
            lint_timeline(json.loads(tl.read_text(encoding="utf-8")), hits)
        except Exception as e:
            hits.append(("ERROR", "timeline.json", 0, f"invalid JSON: {e}"))
    mf = root / "assets" / "manifest.json"
    if mf.exists():
        try:
            lint_manifest(json.loads(mf.read_text(encoding="utf-8")), hits)
        except Exception as e:
            hits.append(("ERROR", "assets/manifest.json", 0, f"invalid JSON: {e}"))

    errors = [h for h in hits if h[0] != "INFO"]
    for rid, f, ln, msg in sorted(hits):
        print(f"[{rid}] {f}:{ln}  {msg}")
    print(f"\n{len(errors)} violation(s).")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
