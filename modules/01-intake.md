# 01 — Intake

## Input modes
| User gives | You do |
|-----------|--------|
| Script only | Generate voice-over (TTS) in the script's language, measure real durations, then build the timeline from them. If the user wants a silent/music-only video, derive timing from reading speed. |
| Script + timestamps | Trust timestamps, but if a VO exists, verify them against it and report drift > 0.3 s. |
| VO only | Transcribe with word timestamps. Treat the transcript as the script. |
| Raw talking video only | Extract audio, transcribe, then follow `04-talking-video.md`. |
| Any combination | Priority for timing: VO/video audio > user timestamps > estimated. Priority for wording: user script > transcript. |

## Ask once (one message, max 5 questions, with defaults)
1. Platform / aspect: 16:9 1920x1080 (default), 9:16 1080x1920, 1:1 1080x1080.
2. Target length (default: length of the input audio; script only → ~150 words/min or equivalent).
3. Tone (default: inferred in stage 2).
4. Brand: colours, logo, fonts (default: none, you choose).
5. Music and captions on/off (default: music on, captions on for talking video and 9:16).
Output language = input language unless the user says otherwise.

## Steps
1. `ffprobe` every input; record duration, fps, resolution, audio streams in `PROJECT.md`.
2. Audio: `ffmpeg -i in -vn -ac 1 -ar 16000 audio/vo16k.wav`.
3. Transcribe: faster-whisper, `compute_type="int8"`, `word_timestamps=True`, language auto-detected.
   - Model: `small` for major languages; **`medium` for low-resource languages (e.g. Bengali, Urdu, Tamil)**; small is often wrong there.
   - If the user supplied a script, use the **script as text truth** and ASR only for timing (fuzzy-align words; keep script spelling).
   - Low-resource language or low-confidence segments → show the transcript to the user and wait for confirmation (gate in CORE §4).
4. Save `transcript.json`: `[{"w": "word", "start": 1.23, "end": 1.58, "lang": "bn", "conf": 0.91}, ...]`
   plus sentence groups.
5. Detect language per sentence; if more than one, list them in `PROJECT.md`.
6. If generating VO: confirm the TTS tool supports the language. If not, tell the user instead of using a wrong-accent voice.
   After generating, transcribe it back and compare with the script; re-generate sentences with large mismatch.
7. Install and register fonts for every script detected (see 02, "Fonts"). Verify with `fc-list`.
8. Write `PROJECT.md`: inputs, languages, platform, fps (default 30), resolution, assumptions, stage = 1 done.
