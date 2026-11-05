#!/usr/bin/env python3
"""Download and verify the complete video without additional software."""
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

BASE = 'https://raw.githubusercontent.com/wambetebenjamin/Videos/refs/heads/arena/5f42c165-videos/rest-in-his-presence/chunks/'
CHUNKS = [
    (94371840, 'c46d38b22ff6852a06b5e380549652d951f68cd93d2e3e8717a102b4087eecfc'),
    (94371840, 'b3bc0d588c618b3e363400841cb7a9897cb49153494771c08ab1555324b9a1fc'),
    (94371840, '4c28cfd8de4df855b8d19e8a1ddc1d294bdca3c9d2608221002a66c24c88b80b'),
    (94371840, '9c363e60ad7c8a7290d408fab2bcd759bd5840d9d6d44132292fc5f26ac2ccef'),
    (94371840, '296d88999eba5ff6d3b4b1fd7a9cca37b42ed013e8509432a1981d3186e839b9'),
    (94371840, '090744f3f4dbd55a886a1a25d8b4442510d1943b6542d27f4428cbaf25e1d29c'),
    (94371840, '125a30c0522cc2e1450366c7710e3b1e47f28674143b730c37ddd713bcbcf857'),
    (88366389, '70d316434acdbfdb6ccb8d74f7d925a213d75b8fd6313f41eb9e135fcb83406d'),
]
TOTAL_HASH = '3ee737ba0787c9866b50e0fd2e3b7db5008d10a4c0d5a31bea07519ddf3ee0fc'
OUTPUT = Path('Rest_in_His_Presence_Full_HD.mp4')
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
