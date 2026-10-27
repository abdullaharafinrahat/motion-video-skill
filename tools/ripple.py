#!/usr/bin/env python3
"""
Change one beat's duration and ripple the change through the timeline.

  python tools/ripple.py B07 --duration 3.2
  python tools/ripple.py B07 --delta +0.5

Snaps to frames, shifts all later beats, updates meta.duration, and prints what moved.
Beats that contain speech are speech-locked: changing their length desyncs the voice,
so the script warns and you must re-time the audio (or add a hold/pause beat instead).
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("beat")
    p.add_argument("--duration", type=float)
    p.add_argument("--delta", type=float)
    p.add_argument("--project", default=".")
    a = p.parse_args()
    if (a.duration is None) == (a.delta is None):
        sys.exit("give exactly one of --duration or --delta")

    path = Path(a.project) / "timeline.json"
    tl = json.loads(path.read_text(encoding="utf-8"))
    fps = tl["meta"]["fps"]
    snap = lambda x: round(x * fps) / fps
    beats = tl["beats"]
    ids = [b["id"] for b in beats]
    if a.beat not in ids:
        sys.exit(f"unknown beat {a.beat}")
    i = ids.index(a.beat)
    b = beats[i]
    old_len = b["end"] - b["start"]
    new_len = snap(a.duration if a.duration is not None else old_len + a.delta)
    if new_len <= 0:
        sys.exit("duration must be positive")
    delta = new_len - old_len
    if abs(delta) < 1 / fps / 2:
        sys.exit("no change after frame snapping")

    if str(b.get("speech", "")).strip():
        print(f"WARNING: {a.beat} contains speech; re-time the voice-over or insert a pause beat.")
    b["end"] = snap(b["end"] + delta)
    moved = []
    for later in beats[i + 1:]:
        later["start"] = snap(later["start"] + delta)
        later["end"] = snap(later["end"] + delta)
        if later.get("status") == "approved":
            moved.append(f"{later['id']} (approved, shifted)")
        else:
            moved.append(later["id"])
    tl["meta"]["duration"] = snap(tl["meta"]["duration"] + delta)
    path.write_text(json.dumps(tl, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{a.beat}: {old_len:.3f}s -> {new_len:.3f}s ({delta:+.3f}s)")
    print("moved:", ", ".join(moved) if moved else "none")
    print(f"new total duration: {tl['meta']['duration']:.3f}s")
    print("Next: update audio timing, run lint, re-render stills for changed beats.")


if __name__ == "__main__":
    main()
