#!/usr/bin/env bash
# Build a 32-second vertical motivational reel from this repo's own footage,
# narration ("benjamin voice.mp3") and music bed ("background song.mpeg").
#
# Every step goes through the vendored ffmpeg-skill tools, in SKILL.md's order:
# probe -> cut (lossless) -> fit (9:16) -> join (crossfade) -> audio (voice +
# ducked music) -> loudness (-14 LUFS) -> check -> look.
#
#   bash projects/demo-reel/build.sh                # full build (1080x1920)
#   bash projects/demo-reel/build.sh --fast         # 720x1280 draft (~3x faster)
#   bash projects/demo-reel/build.sh --keep-master  # also keep the pre-export master
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SKILL="$ROOT/tools/ffmpeg-skill/scripts"
OUT="$ROOT/out/demo-reel"
W=1080; H=1920; KEEP_MASTER=0
for arg in "$@"; do
  case "$arg" in
    --fast)        W=720; H=1280 ;;
    --keep-master) KEEP_MASTER=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

export PATH="$ROOT/.tools/bin:$PATH"
if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  echo "ffmpeg/ffprobe not found. Run: bash tools/setup-ffmpeg.sh" >&2
  exit 1
fi
mkdir -p "$OUT"

# 1. Cut each source to a 6.8 s moment (stream copy: no re-encode, instant).
#    start:S and length:6.8 -> five clips, 4 crossfades of 0.5 s = 32.0 s.
cut() { python3 "$SKILL/cut.py" "$1" --start "$2" --duration 6.8 -o "$OUT/cut-$3.mp4" --overwrite --json-brief >/dev/null; }
echo "[1/6] cut"
cut "189813-887078786_medium.mp4"       5.0 1   # sun breaking through forest
cut "24515-343454414_medium.mp4"       10.0 2   # waterfall
cut "3028399-uhd_3840_2160_24fps.mp4"   8.0 3   # aerial road through forest
cut "8233049-uhd_4096_2160_30fps.mp4"  15.0 4   # misty forest from the air
cut "383541_medium.mp4"                 2.0 5   # sunset over water

# 2. Reframe every clip to 9:16 1080x1920 at 30 fps (centre crop).
echo "[2/6] fit 9:16"
for n in 1 2 3 4 5; do
  python3 "$SKILL/fit.py" "$OUT/cut-$n.mp4" --aspect 9:16 --fit crop \
    --width "$W" --height "$H" --fps 30 -o "$OUT/fit-$n.mp4" --overwrite --json-brief >/dev/null
done

# 3. Crossfade the five shots into one silent picture track.
echo "[3/6] join"
python3 "$SKILL/join.py" "$OUT"/fit-{1,2,3,4,5}.mp4 --transition fade --duration 0.5 \
  --width "$W" --height "$H" --fps 30 -o "$OUT/picture.mp4" --overwrite --json-brief >/dev/null

# 4. Swap the clip audio for the narration, then lay the music bed under it with
#    auto-ducking so the voice stays on top.
echo "[4/6] audio"
python3 "$SKILL/audio.py" "$OUT/picture.mp4" --replace "benjamin voice.mp3" \
  -o "$OUT/voiced.mp4" --overwrite --json-brief >/dev/null
python3 "$SKILL/audio.py" "$OUT/voiced.mp4" --music "background song.mpeg" \
  --music-volume -18 --duck --music-fade-out 3 --fade-out 0.8 --stereo \
  -o "$OUT/mixed.mp4" --overwrite --json-brief >/dev/null

# 5. Normalise for streaming (-14 LUFS, -1 dBTP) and deliver.
echo "[5/6] loudness"
python3 "$SKILL/loudness.py" "$OUT/mixed.mp4" -I -14 --tp -1 \
  -o "$OUT/reel-1080x1920.mp4" --overwrite --json-brief >/dev/null

# 6. Deliver for Reels (platform bitrate, under 25 MB) and measure the result.
echo "[6/6] export + check + look"
python3 "$SKILL/export.py" "$OUT/reel-1080x1920.mp4" --preset reels --max-mb 25 \
  -o "$OUT/reel-reels.mp4" --overwrite --json-brief >/dev/null
python3 "$SKILL/check.py" "$OUT/reel-reels.mp4" --platform reels --json > "$OUT/check.json" || true
python3 "$SKILL/look.py" "$OUT/reel-reels.mp4" --tiles 3x2 -o "$OUT/reel-sheet.png" --overwrite --json-brief >/dev/null || true

# Work files: safe to regenerate, and large. Only the deliverable stays.
rm -f "$OUT"/cut-*.mp4 "$OUT"/fit-*.mp4 "$OUT"/picture.mp4 "$OUT"/voiced.mp4 "$OUT"/mixed.mp4
[ "$KEEP_MASTER" = "1" ] || { rm -f "$OUT"/reel-1080x1920.mp4; MASTER_NOTE=" (master discarded; re-run with --keep-master)"; }
python3 - "$OUT" <<'PY'
import json, sys, pathlib
out = pathlib.Path(sys.argv[1])
check = json.loads((out / "check.json").read_text())
rows = check["checks"]
passed = sum(1 for c in rows if c["status"] == "PASS")
import os
print("Done: out/demo-reel/reel-reels.mp4")
if (out / "reel-1080x1920.mp4").exists():
    print("Master: out/demo-reel/reel-1080x1920.mp4 (pre-export, CRF 18)")
print(f"Check: reels — {passed}/{len(rows)} pass, {check['failed']} failed, "
      f"{check['warnings']} warning(s)")
for c in rows:
    if c["status"] != "PASS":
        print(f"  {c['status']}: {c['check']} = {c.get('value')} (expected {c.get('expected')})")
print("Look: out/demo-reel/reel-sheet.png")
PY
