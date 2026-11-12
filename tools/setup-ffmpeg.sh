#!/usr/bin/env bash
# Fetch ffmpeg + ffprobe into .tools/bin so the vendored ffmpeg-skill can run.
#
# Why this script and not `apt install ffmpeg`: this sandbox only reaches the npm
# and PyPI registries, so the binaries are pulled from npm packages that ship a
# static build inside the tarball. On a normal machine, prefer your distro
# package (it gets security updates) and just `export PATH=/usr/bin:$PATH`.
#
#   bash tools/setup-ffmpeg.sh            # install into .tools/bin
#   bash tools/setup-ffmpeg.sh --check    # report what is available, download nothing
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/.tools/bin"
FFMPEG_PKG="https://registry.npmjs.org/@ffmpeg-installer/linux-x64/-/linux-x64-4.1.0.tgz"
# imageio-ffmpeg ships a full static FFmpeg 7 build inside its wheel.
PYPI_WHEEL="https://pypi.org/pypi/imageio-ffmpeg/json"
FFPROBE_PKG="https://registry.npmjs.org/@ffprobe-installer/linux-x64/-/linux-x64-5.2.0.tgz"

check() {
  local ok=0
  for tool in ffmpeg ffprobe; do
    if command -v "$tool" >/dev/null 2>&1; then
      printf '%-8s %s\n' "$tool" "$(command -v "$tool")"
    else
      printf '%-8s missing\n' "$tool"; ok=1
    fi
  done
  return $ok
}

if [ "${1:-}" = "--check" ]; then
  PATH="$BIN:$PATH" check
  exit $?
fi

if [ -x "$BIN/ffmpeg" ] && [ -x "$BIN/ffprobe" ]; then
  echo "already installed in .tools/bin — nothing to do"
  PATH="$BIN:$PATH" check
  exit 0
fi

mkdir -p "$BIN" /tmp/ffsetup
cd /tmp/ffsetup

if ! [ -x "$BIN/ffmpeg" ]; then
  echo "fetching ffmpeg (static 7.x from the imageio-ffmpeg wheel)…"
  python3 - "$PYPI_WHEEL" "$BIN/ffmpeg" <<'PY'
import json, sys, urllib.request, zipfile, io, os
meta = json.load(urllib.request.urlopen(sys.argv[1], timeout=60))
url = next(u["url"] for u in meta["urls"]
           if "manylinux2014_x86_64" in u["filename"] or "manylinux_2_17_x86_64" in u["filename"])
print("  ", url.rsplit("/", 1)[-1])
data = urllib.request.urlopen(url, timeout=300).read()
with zipfile.ZipFile(io.BytesIO(data)) as z:
    member = next(n for n in z.namelist() if "/binaries/ffmpeg-linux" in n)
    with open(sys.argv[2], "wb") as fh:
        fh.write(z.read(member))
os.chmod(sys.argv[2], 0o755)
PY
fi

if ! [ -x "$BIN/ffprobe" ]; then
  echo "fetching ffprobe (static build from the @ffprobe-installer npm tarball)…"
  curl -sSL --max-time 300 -o ffprobe.tgz "$FFPROBE_PKG"
  tar xzf ffprobe.tgz package/ffprobe
  mv package/ffprobe "$BIN/ffprobe"
  chmod +x "$BIN/ffprobe"
fi

cd "$ROOT"
PATH="$BIN:$PATH" check
echo
echo "add to your shell:  export PATH=\"$BIN:\$PATH\""
echo "or let the wrappers do it:  tools/media probe <file>"
echo
echo "note: this static FFmpeg build has no drawtext filter, so overlay.py --text,"
echo "graphics.py templates and look.py timecode stamps are unavailable here."
echo "caption.py (libass/ASS), cut/join/fit/audio/loudness/check/look all work."
