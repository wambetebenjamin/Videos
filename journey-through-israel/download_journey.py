#!/usr/bin/env python3
"""Download and verify the complete video without additional software."""
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

BASE = 'https://raw.githubusercontent.com/wambetebenjamin/Videos/refs/heads/arena/5f42c165-videos/journey-through-israel/chunks/'
CHUNKS = [
    (94371840, '0c44b433894c3825c476fdec255cfbc96af9bf2badf619c0fa40e00045e7078e'),
    (94371840, '58fdd222d8dc231496f1cfa41bfdd2d38b3b3d266924dc0998e371d223fcb1d0'),
    (94371840, '203267b75dfe43261c31d349ddb70519023501911ff8f6f12dc7c7a7d048931c'),
    (94371840, 'fa9f76a26b586cfdff934f593d33f8fdf19dd5cbfc10d9a0a9beb7be2ee26a12'),
    (94371840, 'd3065c729b718c5ff44f0fc460f391ff1861aec27c694856c9c1c0e3a5ecd084'),
    (94371840, 'dd9ca1cf07323927c0b8b3e0cdaea1a32a2a1e7c36cbf215d298867bb14f0066'),
    (94371840, '2a8ab9776fb4b772c390319e0343df4b6bc1a1d5b945508d837a74ee4f26c2ae'),
    (94371840, 'e3d7c1966c7ec62ba87f0f0f679a6c7b10cef3e3bb5177e32e177d3df3e35dce'),
    (94371840, 'becc0d19ab426d921bf92846525e8fa993a5eee3cc8aebff04910933253ef6bb'),
    (94371840, 'da433c0bde7e150813546053429934433983799fbfe0b4b05b147852a896019c'),
    (30745866, 'b5c7f2e39f5b0884d0b6d2f52f315f97e6ad417faebe014b26f0b02c001dbc3f'),
]
TOTAL_HASH = 'db3d6b8b93a423ec7c89ecb2b5ef2bf493b238f975732508d53ab22bff32d820'
OUTPUT = Path('Journey_Through_Israel.mp4')
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
