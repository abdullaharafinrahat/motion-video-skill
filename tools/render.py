#!/usr/bin/env python3
"""
Deterministic, chunked, parallel, resumable renderer (CPU).

  python tools/render.py                       # final render of everything
  python tools/render.py --preview             # 480p / 12fps animatic
  python tools/render.py --beats B05-B09 --preview
  python tools/render.py --benchmark           # time 20 frames, print ETA

Run long jobs in the background:
  nohup python tools/render.py > logs/render.log 2>&1 &

Requires: playwright (chromium installed), ffmpeg on PATH.
The page engine/render.html must expose window.renderFrame(t) (see modules/05).
"""
import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"command failed: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r


def content_hash(root, tl, f0, f1, fps, extra):
    """Hash everything that can change the pixels of frames [f0, f1): chunks are reused only if identical."""
    h = hashlib.sha1()
    h.update(json.dumps(tl["meta"], sort_keys=True).encode())
    t0, t1 = f0 / fps, f1 / fps
    for b in tl["beats"]:
        if b["end"] > t0 and b["start"] < t1:
            h.update(json.dumps(b, sort_keys=True, ensure_ascii=False).encode())
    for d in ("engine", "scenes"):
        base = root / d
        if base.exists():
            for p in sorted(base.rglob("*")):
                if p.is_file():
                    h.update(p.read_bytes())
    mf = root / "assets" / "manifest.json"
    if mf.exists():
        h.update(mf.read_bytes())
    h.update(extra.encode())
    return h.hexdigest()[:8]


def beat_range(beats, spec):
    ids = [b["id"] for b in beats]
    a, _, b = spec.partition("-")
    b = b or a
    if a not in ids or b not in ids:
        sys.exit(f"unknown beat in range {spec}; have {ids[0]}..{ids[-1]}")
    ba, bb = beats[ids.index(a)], beats[ids.index(b)]
    return ba["start"], bb["end"]


async def worker(wid, queue, cfg, progress):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--disable-gpu", "--font-render-hinting=none"])
        page = await browser.new_page(
            viewport={"width": cfg["W"], "height": cfg["H"]},
            device_scale_factor=cfg["dsf"])
        page.on("console", lambda m: print(f"[w{wid} console] {m.text}", flush=True)
                if m.type == "error" else None)
        await page.goto(cfg["url"])
        await page.wait_for_function("typeof window.renderFrame === 'function'", timeout=60000)
        while True:
            try:
                idx, f0, f1, name = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            out = cfg["chunks"] / name
            if out.exists() and out.stat().st_size > 0:
                progress["done"] += f1 - f0
                continue
            part = out.with_suffix(".part.mp4")
            ff = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe",
                "-framerate", str(cfg["fps"]), "-i", "-",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",   # yuv420p needs even dimensions
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",   # libx264 needs even dimensions
                "-c:v", "libx264", "-crf", cfg["crf"], "-preset", cfg["preset"],
                "-pix_fmt", "yuv420p", str(part), stdin=asyncio.subprocess.PIPE)
            for f in range(f0, f1):
                t = f / cfg["fps"]          # integer frame index -> time, never accumulated
                await page.evaluate("t => window.renderFrame(t)", t)
                kw = {"type": "png"} if cfg["png"] else {"type": "jpeg", "quality": 92}
                ff.stdin.write(await page.screenshot(**kw))
                progress["done"] += 1
                if progress["done"] % 10 == 0:
                    write_progress(cfg, progress)
            ff.stdin.close()
            await ff.wait()
            part.rename(out)
        await browser.close()


def write_progress(cfg, progress):
    el = time.time() - progress["t0"]
    done, total = progress["done"], progress["total"]
    eta = el / done * (total - done) if done else None
    (cfg["root"] / "logs").mkdir(exist_ok=True)
    (cfg["root"] / "logs" / "progress.json").write_text(json.dumps(
        {"done": done, "total": total, "elapsed_s": round(el, 1),
         "eta_s": None if eta is None else round(eta, 1)}))


async def main_async(a):
    root = Path(a.project).resolve()
    tl = json.loads((root / "timeline.json").read_text(encoding="utf-8"))
    meta, beats = tl["meta"], tl["beats"]
    W, H = meta["size"]
    fps = 12 if a.preview else meta["fps"]
    dsf = 1.0
    if a.preview:
        dsf = 480 / min(W, H)
    start, end = (0.0, meta["duration"])
    if a.beats:
        start, end = beat_range(beats, a.beats)
    f_start, f_end = round(start * fps), round(end * fps)
    if a.benchmark:
        f_end = min(f_end, f_start + 20)
    tag = "bench" if a.benchmark else ("pv" if a.preview else "fn")
    chunks = root / "chunks"
    chunks.mkdir(exist_ok=True)
    cfg = dict(W=W, H=H, dsf=dsf, fps=fps, tag=tag, chunks=chunks, root=root,
               url=(root / "engine" / "render.html").as_uri(), png=not a.preview,
               crf="28" if a.preview else "12", preset="ultrafast" if a.preview else "veryfast")
    per = max(1, round(a.chunk_seconds * fps))
    queue = asyncio.Queue()
    jobs = []
    extra = f"{W}x{H}@{fps}:{dsf}:{cfg['crf']}:{cfg['preset']}:{cfg['png']}"
    for i, f0 in enumerate(range(f_start, f_end, per)):
        f1 = min(f0 + per, f_end)
        name = f"{tag}_{f0:07d}_{f1:07d}_{content_hash(root, tl, f0, f1, fps, extra)}.mp4"
        jobs.append((i, f0, f1, name))
        queue.put_nowait(jobs[-1])
    for old in chunks.glob(f"{tag}_*.mp4"):          # drop stale chunks of this tag
        if old.name not in {j[3] for j in jobs}:
            old.unlink()
    workers = a.workers or max(1, (os.cpu_count() or 2) - 1)
    workers = min(workers, len(jobs))
    progress = {"done": 0, "total": f_end - f_start, "t0": time.time()}
    print(f"{progress['total']} frames, {len(jobs)} chunks, {workers} workers, {fps} fps", flush=True)
    await asyncio.gather(*[worker(i, queue, cfg, progress) for i in range(workers)])
    write_progress(cfg, progress)
    el = time.time() - progress["t0"]
    if a.benchmark:
        spf = el / max(1, progress["total"])
        total = round(meta["duration"] * meta["fps"])
        print(f"{spf:.2f} s/frame (incl. browser start) -> full video ~{spf * total / 60:.1f} min at {workers} worker(s)")
        for c in chunks.glob("bench_*"):
            c.unlink()
        return

    listing = chunks / f"{tag}_list.txt"
    listing.write_text("".join(f"file '{(chunks / j[3]).as_posix()}'\n" for j in jobs))
    silent = chunks / f"{tag}_silent.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-c", "copy", str(silent)])
    out_dir = root / ("preview" if a.preview else "out")
    out_dir.mkdir(exist_ok=True)
    name = (a.beats or "all") if a.preview else (f"final_{a.beats}" if a.beats else "final")
    out = out_dir / f"{name}.mp4"
    audio = root / "audio" / ("scratch_mix.wav" if a.preview else "final_mix.wav")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent)]
    if audio.exists():
        cmd += ["-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(audio)]
    if a.preview:
        cmd += ["-c:v", "copy"]
    else:
        cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
    if audio.exists():
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-movflags", "+faststart", str(out)]
    run(cmd)
    print(f"done in {el / 60:.1f} min -> {out}", flush=True)
    if not audio.exists():
        print(f"WARNING: {audio.name} not found; output has no audio", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", default=str(ROOT))
    p.add_argument("--preview", action="store_true")
    p.add_argument("--beats", help="e.g. B05 or B05-B09")
    p.add_argument("--workers", type=int)
    p.add_argument("--chunk-seconds", type=float, default=5.0)
    p.add_argument("--benchmark", action="store_true")
    asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    main()
