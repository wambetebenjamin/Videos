#!/usr/bin/env python3
"""Download and verify the complete video without additional software."""
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

BASE = 'https://raw.githubusercontent.com/wambetebenjamin/Videos/refs/heads/arena/5f42c165-videos/A_Journey_of_Faith/chunks/'
CHUNKS = [
    (94371840, 'fcac82ee5b75ea0b4393d3fed47503eaeea283668e2f617207ced34686332b4a'),
    (94371840, '25d5a32c7c285d1ad8cc138a2c67166c4246162d517a48da781c74dd7746acea'),
    (94371840, 'ee6e5557f59c564ffa2b75eb6db7d2df3e02afe1555389eff9f7ffbe99359c0b'),
    (94371840, '3c87f4649b07cbb1111ee62aa4655b232c6daf456dce363fbd159f22140ab437'),
    (94371840, '14e4def0288c1c236b46dbc43f5bb8b73c29f502a7af94c6581666945727701e'),
    (94371840, '8c873e48171de3947a60a9666d8c9ddcb039c8f76bc26470d35f11b4abb66716'),
    (94371840, '15b4461750c9f3d49928f4e3c52e671747588203d68714f6efba6143e4a851fe'),
    (94371840, 'f039592a7f7f8231c0aa58ba034a6a55a54607de39d6d69c71787ed04be7d5ae'),
    (94371840, '00bb65404b40cac95a9181e2b3c8e8731dfafba7f9ebac2626f5a06b5489d6c1'),
    (94371840, '06278a955276240e2e4614d5bc6cb290513308be3442b237455be89fd6245df4'),
    (25874506, '9a8e99d172c511700c581eac5fbdc15fd2d19a8036f87d65a75521805efb1c7f'),
]
TOTAL_HASH = 'e28d64890fc87a878dd94bcbd728976b0d23708515c96da4496032ee67b67b29'
OUTPUT = Path('A_Journey_of_Faith.mp4')
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
                with urllib.request.urlopen(BASE + f'part{i:02}.bin', timeout=90) as response:
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
