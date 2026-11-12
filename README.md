# Videos

Footage, narration and music for short-form motivational video — plus the tooling
to edit it without leaving this repository.

**Contents:** 49 clips (17 min of stock B-roll: forest, waterfalls, ridgelines,
oceans, aerials), 3 audio files (2:04 voiceover, 0:32 voice take, 3:56 music bed),
2 stills, and 3 designed pieces (`intro and outro designs.mp4`, `template video 1.mp4`,
`motivational videos.mp4`). Exact durations, resolutions and frame rates of every
file: **[ASSETS.md](ASSETS.md)** — regenerate with `python3 tools/inventory.py`.

---

## What was cloned, and why

From [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) (MIT, v3.6.1)
we took **the parts that do work**, not the whole repo:

| Cloned | Why it earns its place here |
|---|---|
| `scripts/` — 47 FFmpeg tools, stdlib only | probe, cut, join, reframe, captions, audio, loudness, check, export. This is the editing engine we did not have |
| `SKILL.md` | the workflow contract: measure → edit losslessly → check → verify → look. It is what stops an agent from guessing a frame rate |
| `references/` | flags, timestamps, gotchas (safe zones, keyframe cuts, HDR, fonts) |
| `docs/contract.md`, `mcp/server.py` | machine-readable tool contract; optional MCP surface |

Left out on purpose: `evals/` (upstream's graded test corpus, ~200 files), `docs/demos/`
(15 MB of marketing GIFs), `brand/`, `.github/`. None of it edits footage.

See **[tools/ffmpeg-skill/VENDORED.md](tools/ffmpeg-skill/VENDORED.md)** for the pinned
commit, the licence and the update procedure.

### Why this one and not another

- **Local, offline, no API keys.** Nothing is uploaded; the tools are `argparse` +
  `subprocess` around `ffmpeg`.
- **It reports numbers.** `--json` on every tool, then `check.py` measures the finished
  file against the platform spec. "Done" is a measurement, not an assertion.
- **It refuses to guess.** If something is unsupported it fails loudly with the fix
  instead of producing a plausible-looking wrong file.
- **It is the hands, not the brain.** It cuts and measures; it does not decide what the
  video should say.

---

## Quick start

```bash
bash tools/setup-ffmpeg.sh          # ffmpeg + ffprobe into .tools/bin (once)
tools/media doctor                  # what this FFmpeg build supports

tools/media probe "383541_medium.mp4"
tools/media fit "383541_medium.mp4" --aspect 9:16 --fit crop --width 1080 --height 1920 -o out/sunset-vertical.mp4
tools/media check out/sunset-vertical.mp4 --platform reels
tools/media look  out/sunset-vertical.mp4 --tiles 3x2 -o out/sunset-sheet.png
```

`tools/media <tool>` forwards to `tools/ffmpeg-skill/scripts/<tool>.py`; run any tool
with `--help` for its flags. Shared flags: `--dry-run` (plan only), `--json`,
`--overwrite`, `--timeout`.

### Jobs this library is actually good for

```bash
# 1. Pick a moment from a long clip, losslessly, then vertical for Reels
tools/media cut "26637-360259342_medium.mp4" --start 20 --duration 6 -o out/pick.mp4
tools/media fit out/pick.mp4 --aspect 9:16 --fit crop --width 1080 --height 1920 -o out/pick-v.mp4

# 2. Stitch shots with crossfades at one delivery spec
tools/media join a.mp4 b.mp4 c.mp4 --transition fade --duration 0.5 --width 1080 --height 1920 --fps 30 -o out/seq.mp4

# 3. Narrate over it: swap in the voice take, lay the music bed under it, ducked
tools/media audio out/seq.mp4 --replace "benjamin voice.mp3" -o out/voiced.mp4
tools/media audio out/voiced.mp4 --music "background song.mpeg" --music-volume -18 --duck --music-fade-out 3 -o out/mixed.mp4

# 4. Burn captions from a script or an SRT
tools/media caption out/mixed.mp4 --srt subs.srt --animate pop --position bottom -o out/captioned.mp4

# 5. Normalise and deliver
tools/media loudness out/captioned.mp4 -I -14 --tp -1 -o out/master.mp4
tools/media export out/master.mp4 --preset reels --max-mb 25 -o out/reel.mp4
tools/media check out/reel.mp4 --platform reels
```

For three or more steps on the same edit, describe them once in a `render.py`
project (`tools/media render project.json --init`) and re-render only the stages
that changed with `--cache DIR`.

---

## Demo: a 32 s vertical reel from this footage

`projects/demo-reel/build.sh` runs the whole chain on the repo's own material —
sunlight in forest → waterfall → aerial road → misty forest → sunset, over the voice
take and the music bed:

```bash
bash projects/demo-reel/build.sh        # ~5 min on 2 cores; --fast for 720x1280
```

Result (`out/demo-reel/`):

```
Done: reel-reels.mp4 — 32.93 s, 1080x1920, 30 fps, H.264, AAC stereo, -14.2 LUFS, 24.1 MiB
Steps: cut 6.8 s x5 (stream copy) -> fit 9:16 crop -> join fade 0.5 -> replace voice
       -> music -18 dB ducked -> loudness -14 -> export reels
Check: reels — 12/13 pass, 0 failed, 1 warning (no subtitle track)
Look:  out/demo-reel/reel-sheet.png
```

The one warning is real: the reel has no captions, because there is no transcript of
the voice take in the repo. That is the next thing to fix, not a bug in the tools.

---

## Known limits in this environment

- The FFmpeg we can fetch here is a static **7.0.2 without `drawtext`**. Captions
  (libass/ASS) work; `overlay.py --text`, `graphics.py` lower-thirds and `look.py`
  timecode stamps do not. On a machine with a distro FFmpeg, put `/usr/bin` ahead of
  `.tools/bin` and they work. See `VENDORED.md`.
- No speech-to-text engine is installed, so `caption.py --transcribe` and
  `silence.py --filler --transcribe` refuse. Install `faster-whisper` (or parakeet)
  locally, or pass an SRT/word timings you already have.
- `.tools/bin` (~160 MB of binaries) and `out/` are git-ignored: they are reproducible
  from `tools/setup-ffmpeg.sh` and `projects/demo-reel/build.sh`.

## Still worth cloning from that ecosystem

Upstream is one repo in a family; these are the ones that would extend *this* work
rather than duplicate it:

| Repo | Would give us |
|---|---|
| [transcription-skill](https://github.com/kajisho5/transcription-skill) | the missing transcripts → real captions, karaoke, filler-word removal |
| [media-analysis-skill](https://github.com/kajisho5/media-analysis-skill) | shot tagging and clip selection across 49 sources instead of by eye |
| [remotion-ffmpeg-skill](https://github.com/kajisho5/remotion-ffmpeg-skill) | motion-graphic layers (animated captions, peak-driven motion) over these clips |
| [qc-skill](https://github.com/kajisho5/qc-skill) | approval gates on a deliverable before it is published |

## Repository layout

```
*.mp4, *.mpeg, *.mp3, *.jpg     the footage and audio (sources — never overwritten)
ASSETS.md                       generated inventory: every file, measured
tools/media(.sh)                one-line entry point to the tools
tools/setup-ffmpeg.sh           fetch ffmpeg + ffprobe into .tools/bin
tools/inventory.py              regenerate ASSETS.md
tools/ffmpeg-skill/             vendored MIT skill (see VENDORED.md)
projects/demo-reel/build.sh     the worked example, end to end
out/demo-reel/                  the rendered reel, its contact sheet and check.json
```
