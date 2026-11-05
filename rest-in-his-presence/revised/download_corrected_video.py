#!/usr/bin/env python3
"""Download and verify the complete video without additional software."""
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

BASE = 'https://raw.githubusercontent.com/wambetebenjamin/Videos/refs/heads/arena/5f42c165-videos/rest-in-his-presence/revised/chunks/'
CHUNKS = [
    (94371840, '254d743a2083e7f645d26e1c03586a4dea4101763f393a2086dac13d01e7464c'),
    (94371840, '3c40d1ab04098f83c5a0a0ada132bee85e5798ac8c8dda28abeb6ceeef8d78bd'),
    (94371840, 'acd1d1976c31e91f300faf71c975e42691265800de25e89ba6037a2c517d6eab'),
    (94371840, '6f45e63bad542eb5ce78ce93941f06b90a5c1a928abeafec34588668e4756546'),
    (94371840, '3a3334c226c209115a4067bd9e8f59503a2f0cadd47b6290a4254b01e0e026ca'),
    (94371840, 'dba8ad7f1f9721384563a4e7668b23c068704ffeabbe6fc0d954953e9ca8a810'),
    (94371840, 'b57e735cb05e3db0114ac39742535ec31d9f80f93a98aac168d234b62d0b0292'),
    (88014977, '6429414e992276f6c2afd81912b595138fd895aa64d9f4a636065c1902749dc7'),
]
TOTAL_HASH = 'e8be3d473d64152c07a9f533e57ccba7f92bc5c7e22e68c70fdc8dfab5d46f66'
OUTPUT = Path('Rest_in_His_Presence_Corrected.mp4')
TEMP = OUTPUT.with_suffix('.mp4.part')

def main():
    if OUTPUT.exists() or TEMP.exists():
        raise RuntimeError('The output or partial file already exists; move it before downloading again.')
    total = hashlib.sha256()
    try:
        with TEMP.open('xb') as dest:
            for i, (size, expected) in enumerate(CHUNKS):
                print(f'Downloading section {i + 1} of {len(CHUNKS)}...', flush=True)
                digest, count = hashlib.sha256(), 0
                with urllib.request.urlopen(BASE + f'video-{i:02}.bin', timeout=90) as response:
                    while block := response.read(1024 * 1024):
                        count += len(block)
                        if count > size:
                            raise RuntimeError('Section is larger than expected.')
                        digest.update(block); total.update(block); dest.write(block)
                if count != size or digest.hexdigest() != expected:
                    raise RuntimeError(f'Section {i + 1} failed verification.')
        if total.hexdigest() != TOTAL_HASH:
            raise RuntimeError('The video failed final verification.')
        os.replace(TEMP, OUTPUT)
    except Exception:
        TEMP.unlink(missing_ok=True)
        raise
    print(f'Finished: {OUTPUT.resolve()}')

if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError) as error:
        print(f'Download failed: {error}', file=sys.stderr)
        sys.exit(1)
