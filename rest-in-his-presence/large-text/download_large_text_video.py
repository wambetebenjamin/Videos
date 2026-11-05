#!/usr/bin/env python3
"""Download and verify the complete video without additional software."""
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

BASE = 'https://raw.githubusercontent.com/wambetebenjamin/Videos/refs/heads/arena/5f42c165-videos/rest-in-his-presence/large-text/chunks/'
CHUNKS = [
    (94371840, '46a104ef5b66da8e87219919a7bddf53de6e79153112008ded25cf264e1a9c0a'),
    (94371840, 'e49c6e9b981b4158ac9ce7aecb13d200746e814c7ae04bc2f977e1402ec6c763'),
    (94371840, '5542ee37853373a6984cc74f121f2048ec78cebb22e068e74ee8d32a2293f663'),
    (94371840, 'dff2b914a69e015357df75ba91360e2cf69efbb3388ce490d83216eacbfb6bec'),
    (94371840, '2686f166f7ff75f7e9b497cdeece56ac3e9cd57069579db34e11bec936c3b8cb'),
    (94371840, '189610ca1f19615567d04cfc9e88016d66be88b88d1eb837a56724b49f221177'),
    (94371840, '00acc4ef19887d0310dfc67c67ec7e5a3a084776360197e76f92cc601b661571'),
    (88425238, 'd51663887be48ca435d8d0350f86b586e688913ce81bdc3844792d6ce2d1d2f9'),
]
TOTAL_HASH = '153be34021e7411abc0b337fc3f48e12180e5cc1b0dc154b59d3fd5572962e5f'
OUTPUT = Path('Rest_in_His_Presence_Large_Text.mp4')
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
