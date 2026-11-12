# Vendored: ffmpeg-skill

This directory is a **copy of an upstream project**, not our code. Everything in
`scripts/`, `references/`, `docs/`, `mcp/` and `SKILL.md` is verbatim upstream.

| | |
|---|---|
| Upstream | https://github.com/kajisho5/ffmpeg-skill |
| Version | 3.6.1 |
| Commit | `ba449b0b036a75ab20e79d1658ecc3b158fe2ea6` (2026-11-12) |
| License | MIT — Copyright (c) 2026 kajisho5 (see `LICENSE`) |
| Size | ~2.5 MB, 77 files, Python standard library only |

## What was taken

| Path | Why |
|---|---|
| `scripts/` (47 tools + `_common/`) | the actual editing engine: probe, cut, join, fit, caption, audio, loudness, check, look, export, render |
| `SKILL.md` | the routing table and workflow an agent reads before touching footage |
| `references/` | flags, gotchas, timestamp formats, per-tool detail — the parts that stop an agent guessing |
| `docs/contract.md` | machine-readable description of every tool's arguments and outputs |
| `mcp/server.py` | optional MCP surface, if a client wants the tools over JSON-RPC |

## What was deliberately left out

| Path | Why |
|---|---|
| `evals/` (~200 files, model-graded test corpus) | upstream's own quality harness; nothing to do with our footage |
| `docs/demos/` (~15 MB of before/after GIFs) | marketing; the demo in `projects/demo-reel/` is made from our own clips |
| `brand/`, `assets/`, `.github/` | upstream identity, CI and release automation |
| `bin/install.js`, `package.json` scripts | we do not install into `~/.claude/skills`; the scripts are called in place |
| `demos/footage/` | sample media |

## Running it

```bash
bash tools/setup-ffmpeg.sh                     # once per machine/sandbox: ffmpeg + ffprobe into .tools/bin
python3 tools/ffmpeg-skill/scripts/probe.py clip.mp4 --json
python3 tools/ffmpeg-skill/scripts/_contract.py doctor --json   # what this FFmpeg build supports
```

Or through the wrapper, which puts `.tools/bin` on `PATH` first:

```bash
tools/media probe clip.mp4
tools/media fit clip.mp4 --aspect 9:16 --fit crop -o clip-vertical.mp4
```

## Known limitation in this sandbox

The static FFmpeg build we can fetch here (`ffmpeg 7.0.2-static`) has **no
`drawtext` filter**. Consequences:

- works: `probe cut join fit caption audio loudness check look export render scenes silence grid ...` (captions are rendered through libass/ASS, not drawtext)
- refuses: `overlay.py --text`, `graphics.py` templates, `look.py` timecode stamps

On a machine with a distro FFmpeg (which does ship drawtext), those work too —
just put `/usr/bin` ahead of `.tools/bin` on `PATH`.

## Updating

Re-copy the paths above from a pinned tag, then update the commit in this file:

```bash
git clone --depth 1 --branch v3.6.1 https://github.com/kajisho5/ffmpeg-skill /tmp/ffs
cp -r /tmp/ffs/{scripts,references,SKILL.md,LICENSE} tools/ffmpeg-skill/
```

Keep the version pinned: upstream's README states that `main` moves ahead of the
last release, so a dependent repo should track a tag.
