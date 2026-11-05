#!/usr/bin/env python3
"""Assemble, upload, verify and share the corrected video from a Codespace.

The rclone remote must be named gdrive and configured with Google Drive access.
The Google access token is read only from rclone's local configuration and sent
only to the Google Drive API. Never print the configuration or token.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
REVISION = HERE.parent
DOWNLOADER = REVISION / 'download_corrected_video.py'
CHUNK_DIRECTORY = REVISION / 'chunks'
RECIPIENT = 'chriscoyouthaflame2025@gmail.com'
REMOTE_NAME = 'gdrive'
FOLDER_NAME = 'Abbas Table - Chrisco Youth'
FILENAME = 'Rest_in_His_Presence_Corrected.mp4'
REMOTE_FILE = f'{REMOTE_NAME}:{FOLDER_NAME}/{FILENAME}'


def downloader_metadata():
    spec = importlib.util.spec_from_file_location('video_metadata', DOWNLOADER)
    if spec is None or spec.loader is None:
        raise RuntimeError('Cannot load the video verification information.')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CHUNKS, module.TOTAL_HASH


def digest_file(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def assemble(output):
    chunks, expected_total = downloader_metadata()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        print('Checking the previously assembled video...', flush=True)
        if digest_file(output) == expected_total:
            return output
        raise RuntimeError(f'The existing video did not match. Move or delete {output} before retrying.')
    tmp = output.with_name(output.name + '.assembling')
    if tmp.exists():
        raise RuntimeError(f'A previous partial file exists. Delete {tmp} before retrying.')
    total = hashlib.sha256()
    try:
        with tmp.open('xb') as dest:
            for index, (expected_size, expected_hash) in enumerate(chunks):
                path = CHUNK_DIRECTORY / f'video-{index:02d}.bin'
                print(f'Combining section {index + 1} of {len(chunks)}...', flush=True)
                part_hash, count = hashlib.sha256(), 0
                with path.open('rb') as src:
                    for block in iter(lambda: src.read(1024 * 1024), b''):
                        count += len(block)
                        part_hash.update(block)
                        total.update(block)
                        dest.write(block)
                if count != expected_size or part_hash.hexdigest() != expected_hash:
                    raise RuntimeError(f'Section {index + 1} failed verification.')
        if total.hexdigest() != expected_total:
            raise RuntimeError('The combined video failed verification.')
        os.replace(tmp, output)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return output


def run_rclone(*args, capture=True):
    try:
        result = subprocess.run(['rclone', *args], text=True, capture_output=capture, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError('rclone is not installed. Follow the setup instructions first.') from exc
    if result.returncode:
        # Do not print captured output: rclone config can include credentials.
        raise RuntimeError(f'rclone {args[0]} failed. Check your Drive sign-in and try again.')
    return result.stdout if capture else ''


def get_rclone_token():
    # rclone has just contacted Drive and refreshed an expired token if needed.
    config = json.loads(run_rclone('config', 'dump'))
    remote = config.get(REMOTE_NAME, {})
    if remote.get('type') != 'drive':
        raise RuntimeError('Configure a Google Drive remote named gdrive first.')
    token = remote.get('token')
    if isinstance(token, str):
        token = json.loads(token)
    access_token = token.get('access_token') if isinstance(token, dict) else None
    if not access_token:
        raise RuntimeError('No Google access token was found in the gdrive remote. Sign in with rclone first.')
    return access_token


def drive_request(token, path, *, method='GET', body=None):
    url = 'https://www.googleapis.com/drive/v3/' + path
    data = json.dumps(body).encode('utf-8') if body is not None else None
    request = urllib.request.Request(url, data=data, method=method,
                                     headers={'Authorization': 'Bearer ' + token,
                                              'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not include response bodies or request headers, which can contain sensitive information.
        raise RuntimeError(f'Google Drive sharing failed (HTTP {exc.code}). The uploaded file may still be in your Drive.') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError('Could not contact Google Drive to share the uploaded file.') from exc


def share_with_recipient(token, file_id):
    file_id = urllib.parse.quote(file_id, safe='')
    params = urllib.parse.urlencode({'fields': 'nextPageToken,permissions(id,type,emailAddress,role)',
                                     'pageSize': 100, 'supportsAllDrives': 'true'})
    page = ''
    while True:
        suffix = params + ('&pageToken=' + urllib.parse.quote(page, safe='') if page else '')
        result = drive_request(token, f'files/{file_id}/permissions?{suffix}')
        for permission in result.get('permissions', []):
            if (permission.get('type') == 'user'
                    and permission.get('emailAddress', '').casefold() == RECIPIENT.casefold()):
                print(f'The file is already shared with {RECIPIENT}.', flush=True)
                return
        page = result.get('nextPageToken', '')
        if not page:
            break
    params = urllib.parse.urlencode({'sendNotificationEmail': 'true', 'supportsAllDrives': 'true',
                                     'fields': 'id,type,role,emailAddress'})
    result = drive_request(token, f'files/{file_id}/permissions?{params}', method='POST',
                           body={'type': 'user', 'role': 'reader', 'emailAddress': RECIPIENT})
    if result.get('type') != 'user' or result.get('role') != 'reader':
        raise RuntimeError('Google Drive did not confirm the expected reader permission.')
    print(f'Shared with {RECIPIENT} as a viewer. Google Drive was asked to send a notification.', flush=True)


def upload_and_share(output):
    # All progress is shown to the user. --immutable prevents overwriting a different file.
    print('Checking your Google Drive connection...', flush=True)
    run_rclone('about', REMOTE_NAME + ':')
    print('Creating the destination folder if needed...', flush=True)
    run_rclone('mkdir', f'{REMOTE_NAME}:{FOLDER_NAME}')
    print('Uploading the video. Please keep the Codespace open...', flush=True)
    run_rclone('copyto', str(output), REMOTE_FILE, '--checksum', '--immutable',
               '--progress', '--retries', '8', '--low-level-retries', '10', capture=False)
    print('Verifying the uploaded file...', flush=True)
    metadata = json.loads(run_rclone('lsjson', '--stat', '--hash', REMOTE_FILE))
    if not isinstance(metadata, dict):
        raise RuntimeError('Unexpected file metadata from Google Drive.')
    if metadata.get('Size') != output.stat().st_size:
        raise RuntimeError('The uploaded file size did not match. Nothing was shared.')
    hashes = metadata.get('Hashes') or {}
    remote_md5 = hashes.get('MD5') or hashes.get('md5')
    if not remote_md5 or remote_md5.lower() != digest_file(output, 'md5'):
        raise RuntimeError('The uploaded file could not be verified by MD5. Nothing was shared.')
    file_id = metadata.get('ID') or metadata.get('Id')
    if not file_id:
        raise RuntimeError('The upload succeeded but no Google Drive file ID was returned. Nothing was shared.')
    token = get_rclone_token()
    print('Sharing the verified file...', flush=True)
    share_with_recipient(token, file_id)
    print('Video: https://drive.google.com/file/d/' + urllib.parse.quote(file_id, safe='') + '/view', flush=True)


def main():
    parser = argparse.ArgumentParser(description='Assemble and send the corrected Abba’s Table video.')
    parser.add_argument('--assemble-only', action='store_true', help='Only assemble and verify the video; do not upload or share.')
    parser.add_argument('--output-dir', type=Path, default=Path(tempfile.gettempdir()) / 'abbas-table-video',
                        help='Local working folder (default: a folder in the Codespace temporary directory).')
    args = parser.parse_args()
    output = assemble(args.output_dir / FILENAME)
    print(f'Combined and verified: {output}', flush=True)
    if not args.assemble_only:
        upload_and_share(output)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f'Could not complete the transfer: {error}', file=sys.stderr)
        sys.exit(1)
