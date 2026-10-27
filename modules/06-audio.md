# 06 — Audio (voice, music, SFX, mix)

## Voice
- Talking video: use the original audio. Optional light clean-up: `highpass=f=80`, gentle `afftdn=nr=8`. Do not over-process.
- Generated VO: pick a voice that fits language, region and tone. Verify by transcribing it back (faster-whisper) and comparing with the script; regenerate mismatched sentences. Record per-sentence durations; they drive the timeline.

## Music
- Choose by energy level: 1 → ambient/slow (60–80 BPM), 2 → light rhythmic (80–100), 3 → mid (100–115), 4 → driving (115–130), 5 → fast (125–150).
- Generate or select a track that matches the mood and the culture of the audience; no vocals under spoken VO.
- Beat grid: `librosa.beat.beat_track` → `audio/beats.json`. For energy ≥ 4, snap cuts and hits to the nearest beat (± 1 frame). For energy ≤ 2, ignore the grid and follow speech pauses.
- Loop/trim with a musical edit (on a bar line) and fade out ≥ 1.5 s.

## SFX (restraint is the rule)
- Place SFX only on meaningful hits listed in `timeline.json` → `beats[].hits[]` (title lands, number counts up, whip, reveal).
- Vary sounds; no whoosh on every cut (blacklist item 15). Each SFX gets a purpose in `why`.
- The SFX onset must fall within ± 1 frame of its visual hit.

## Mix
- Music under voice: about −18 to −22 dB relative to the VO; duck with sidechain:
  `[music][vo]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300`.
- SFX −10 to −16 dB relative to VO; no clipping.
- Final loudness: `loudnorm=I=-14:TP=-1.5:LRA=9` (social/web). Two-pass measure for accuracy.
- Mono-compatibility check: summing to mono must not cancel the VO.
- Output `audio/final_mix.wav` (48 kHz, 24-bit) and mux into the MP4 as AAC 192 kbps.

## Checks
`ffprobe` duration equals video duration ± 1 frame; no silence gap > 1.5 s unless intended; peaks ≤ −1 dBTP; log measured LUFS in `qa-report.md`.
