#!/usr/bin/env bash
# One-line entry point to the vendored ffmpeg-skill tools.
#
#   tools/media probe clip.mp4                    # measure a file
#   tools/media fit clip.mp4 --aspect 9:16 -o v.mp4
#   tools/media caption talk.mp4 --srt subs.srt -o captioned.mp4
#   tools/media check out.mp4 --platform reels
#   tools/media doctor                            # what this FFmpeg build supports
#
# Tool name = the script name in tools/ffmpeg-skill/scripts/ (without .py):
# probe cut join fit silence scenes caption graphics overlay audio loudness
# check look export render broll grid metadata multicam proxy redact reverse
# sequence speedramp stabilize straighten sync verify waveform freeze insert
# loop pad color crop cropdetect deinterlace denoise background report batch
# sphere export check
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$ROOT/.tools/bin:$PATH"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg not found — run: bash tools/setup-ffmpeg.sh" >&2
  exit 127
fi

if [ $# -eq 0 ]; then
  sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

tool="$1"; shift
case "$tool" in
  doctor|contract) exec python3 "$ROOT/tools/ffmpeg-skill/scripts/_contract.py" "$@" ;;
esac

script="$ROOT/tools/ffmpeg-skill/scripts/$tool.py"
if [ ! -f "$script" ]; then
  echo "no such tool: $tool" >&2
  echo "available: $(cd "$ROOT/tools/ffmpeg-skill/scripts" && ls *.py | grep -v '^_' | sed 's/\.py$//' | tr '\n' ' ')" >&2
  exit 2
fi
exec python3 "$script" "$@"
