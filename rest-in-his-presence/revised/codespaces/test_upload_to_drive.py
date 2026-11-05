import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('uploader', HERE / 'upload_to_drive.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)

class TestUploader(unittest.TestCase):
    def test_assemble_verifies_and_reuses(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            chunks = root / 'chunks'
            chunks.mkdir()
            parts = [b'first part', b'second part']
            metadata = [(len(b), hashlib.sha256(b).hexdigest()) for b in parts]
            for i, part in enumerate(parts):
                (chunks / f'video-{i:02d}.bin').write_bytes(part)
            total_hash = hashlib.sha256(b''.join(parts)).hexdigest()
            output = root / 'combined.mp4'
            with patch.object(u, 'CHUNK_DIRECTORY', chunks), patch.object(u, 'downloader_metadata', return_value=(metadata, total_hash)):
                u.assemble(output)
                self.assertEqual(output.read_bytes(), b''.join(parts))
                u.assemble(output)
                output.unlink()
                (chunks / 'video-01.bin').write_bytes(b'corrupt')
                with self.assertRaises(RuntimeError):
                    u.assemble(output)
                self.assertFalse(output.exists())
                self.assertFalse(output.with_name(output.name + '.assembling').exists())

    def test_creates_viewer_permission_only_when_missing(self):
        calls = []
        def request(token, path, *, method='GET', body=None):
            calls.append((method, path, body))
            if method == 'GET':
                return {'permissions': [{'type': 'user', 'emailAddress': 'someone@example.com', 'role': 'reader'}]}
            return {'type': 'user', 'role': 'reader', 'id': 'new'}
        with patch.object(u, 'drive_request', side_effect=request):
            u.share_with_recipient('private-token', 'file-id')
        self.assertEqual(calls[-1][0], 'POST')
        self.assertEqual(calls[-1][2], {'type': 'user', 'role': 'reader', 'emailAddress': u.RECIPIENT})
        self.assertIn('sendNotificationEmail=true', calls[-1][1])

    def test_does_not_duplicate_existing_permission(self):
        with patch.object(u, 'drive_request', return_value={'permissions': [
            {'type': 'user', 'role': 'reader', 'emailAddress': u.RECIPIENT.upper()}]}) as request:
            u.share_with_recipient('private-token', 'file-id')
        self.assertEqual(request.call_count, 1)

    def test_does_not_share_when_upload_hash_is_wrong(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'video.mp4'
            output.write_bytes(b'data')
            def rclone(*args, **kwargs):
                if args[0] == 'lsjson':
                    return json.dumps({'Size': 4, 'Hashes': {'MD5': 'wrong'}, 'ID': '123'})
                return ''
            with patch.object(u, 'run_rclone', side_effect=rclone), patch.object(u, 'share_with_recipient') as share:
                with self.assertRaises(RuntimeError):
                    u.upload_and_share(output)
                share.assert_not_called()

    def test_verified_upload_shares_and_uses_target_file(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'video.mp4'
            output.write_bytes(b'data')
            calls = []
            def rclone(*args, **kwargs):
                calls.append(args)
                if args[0] == 'lsjson':
                    return json.dumps({'Size': 4, 'Hashes': {'MD5': hashlib.md5(b'data').hexdigest()}, 'ID': 'id123'})
                return ''
            with patch.object(u, 'run_rclone', side_effect=rclone), patch.object(u, 'get_rclone_token', return_value='private-token'), patch.object(u, 'share_with_recipient') as share:
                u.upload_and_share(output)
                share.assert_called_once_with('private-token', 'id123')
            copy = next(c for c in calls if c[0] == 'copyto')
            self.assertEqual(copy[2], u.REMOTE_FILE)
            self.assertIn('--immutable', copy)

    def test_reads_token_without_logging_it(self):
        config = {'gdrive': {'type': 'drive', 'token': json.dumps({'access_token': 'private-token'})}}
        with patch.object(u, 'run_rclone', return_value=json.dumps(config)):
            self.assertEqual(u.get_rclone_token(), 'private-token')

if __name__ == '__main__':
    unittest.main()
