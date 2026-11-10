"""Real curl/ffmpeg regressions against a loopback HTTP fixture.

Run: python -m unittest discover -s skills/digital-human-koubo/scripts -p test_rangedl.py -v
"""
import hashlib
import http.server
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest


@unittest.skipUnless(shutil.which('curl') and shutil.which('ffmpeg'), 'curl and ffmpeg required')
class RangeDownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = tempfile.TemporaryDirectory(prefix='dh-range-fixture-')
        cls.addClassCleanup(fixture.cleanup)
        source = Path(fixture.name) / 'source.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        'color=c=blue:s=64x64:r=10', '-t', '1', '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(source)], check=True)
        cls.payload = source.read_bytes()
        cls.script = Path(__file__).with_name('rangedl.py').resolve()

    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix='dh-range-中文 ')
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        payload = self.payload
        self.requests = requests = []
        lock = threading.Lock()
        resumed = set()
        step = (len(payload) + 5) // 6
        initial_starts = set(range(0, len(payload), step))

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_HEAD(self):
                self.send_response(403 if self.path == '/head-error' else 200)
                if self.path != '/no-length':
                    self.send_header('Content-Length', '0' if self.path == '/empty' else str(len(payload)))
                self.end_headers()

            def do_GET(self):
                value = self.headers.get('Range', '')
                with lock:
                    requests.append((self.path, value))
                match = re.fullmatch(r'bytes=(\d+)-(\d+)', value)
                if not match:
                    self.send_error(400)
                    return
                a, b = map(int, match.groups())
                if a > b or b >= len(payload):
                    self.send_error(416)
                    return
                body = payload[a:b + 1]
                status = 206
                content_range = f'bytes {a}-{b}/{len(payload)}'
                if self.path == '/ignored':
                    status, body = 200, payload
                elif self.path == '/forbidden':
                    status, body = 403, b'AccessDenied' * len(payload)
                elif self.path == '/wrong-start':
                    content_range = f'bytes {a + 1}-{b}/{len(payload)}'
                elif self.path == '/wrong-total':
                    content_range = f'bytes {a}-{b}/{len(payload) + 1}'
                elif self.path == '/oversized':
                    body += b'not part of the requested range'
                elif self.path == '/short':
                    body = body[:max(1, len(body) // 2)]
                elif self.path == '/corrupt':
                    body = b'x' * len(body)
                self.send_response(status)
                if self.path != '/missing-range':
                    self.send_header('Content-Range', content_range)
                if self.path != '/no-get-length':
                    self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                with lock:
                    truncate = self.path == '/resume' and a in initial_starts and a not in resumed
                    if truncate:
                        resumed.add(a)
                if truncate:
                    body = body[:max(1, len(body) // 2)]
                self.wfile.write(body)

        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.close_server, thread)

    def close_server(self, thread):
        self.server.shutdown()
        self.server.server_close()
        thread.join()

    def run_jobs(self, jobs, *, injected_failure=None):
        (self.root / 'urls.txt').write_text(''.join(
            f'{tid} http://127.0.0.1:{self.server.server_port}/{mode}\n'
            for tid, mode in jobs), encoding='utf-8')
        command = [sys.executable, '-B', str(self.script)]
        if injected_failure:
            # Isolate return-code contracts that a real encoder/connection cannot
            # reliably be made to produce on every platform.
            bootstrap = """
import runpy, subprocess, sys
from unittest.mock import patch
real_run = subprocess.run
mode = sys.argv[2]
def run(args, **kwargs):
    if mode == 'curl' and args[0] == 'curl' and '-r' in args:
        return subprocess.CompletedProcess(args, 7, b'', b'connection failed')
    if args[0] == 'ffmpeg':
        if mode == 'decoder-exit':
            return subprocess.CompletedProcess(args, 1, '', '')
        if mode == 'decoder-stderr':
            return subprocess.CompletedProcess(args, 0, '', 'corrupt packet')
    result = real_run(args, **kwargs)
    if mode == 'curl-after-complete' and args[0] == 'curl' and '-r' in args:
        return subprocess.CompletedProcess(args, 18, result.stdout, result.stderr)
    return result
with patch('subprocess.run', side_effect=run):
    runpy.run_path(sys.argv[1], run_name='__main__')
"""
            command = [sys.executable, '-B', '-c', bootstrap, str(self.script), injected_failure]
        return subprocess.run(command, cwd=self.root,
                              env=dict(os.environ, PYTHONIOENCODING='utf-8',
                                       NO_PROXY='127.0.0.1,localhost'),
                              capture_output=True, text=True, encoding='utf-8', timeout=40)

    def assert_good(self, result, tid='clip.mp4'):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = (self.root / ('renoise-' + tid)).read_bytes()
        self.assertEqual(hashlib.sha256(output).digest(), hashlib.sha256(self.payload).digest())
        self.assertIn('True OK', result.stdout)
        self.assertEqual(list(self.root.glob('.p*')), [])
        self.assertEqual(list(self.root.glob('.rangedl-*')), [])

    def assert_rejected(self, mode):
        result = self.run_jobs([('clip.mp4', mode)])
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.root / 'renoise-clip.mp4').exists())
        self.assertEqual(list(self.root.glob('.p*')), [], 'Rejected response bytes must not enter parts')
        self.assertNotIn('True OK', result.stdout)
        self.assertEqual(list(self.root.glob('.rangedl-*')), [])

    def test_valid_206_is_byte_identical(self):
        self.assert_good(self.run_jobs([('clip.mp4', 'good')]))

    def test_ignored_range_is_rejected(self):
        self.assert_rejected('ignored')

    def test_http_error_body_is_rejected(self):
        self.assert_rejected('forbidden')

    def test_wrong_range_start_is_rejected(self):
        self.assert_rejected('wrong-start')

    def test_wrong_total_is_rejected(self):
        self.assert_rejected('wrong-total')

    def test_missing_content_range_is_rejected(self):
        self.assert_rejected('missing-range')

    def test_oversized_body_is_rejected(self):
        self.assert_rejected('oversized')

    def test_clean_but_short_response_is_rejected(self):
        self.assert_rejected('short')

    def test_head_http_error_is_rejected(self):
        self.assert_rejected('head-error')
        self.assertEqual(self.requests, [])

    def test_missing_head_length_is_rejected(self):
        self.assert_rejected('no-length')
        self.assertEqual(self.requests, [])

    def test_empty_object_is_rejected(self):
        self.assert_rejected('empty')
        self.assertEqual(self.requests, [])

    def test_get_without_content_length_uses_range_and_exact_size(self):
        self.assert_good(self.run_jobs([('clip.mp4', 'no-get-length')]))

    def test_interrupted_206_resumes_at_verified_prefix(self):
        self.assert_good(self.run_jobs([('clip.mp4', 'resume')]))
        step = (len(self.payload) + 5) // 6
        for a in range(0, len(self.payload), step):
            b = min(len(self.payload) - 1, a + step - 1)
            resumed_at = a + max(1, (b - a + 1) // 2)
            self.assertIn(('/resume', f'bytes={resumed_at}-{b}'), self.requests)

    def test_corrupt_media_does_not_replace_existing_output(self):
        final = self.root / 'renoise-clip.mp4'
        original = b'existing output must survive failed verification'
        final.write_bytes(original)
        result = self.run_jobs([('clip.mp4', 'corrupt')])
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(final.read_bytes(), original)
        self.assertTrue(list(self.root.glob('.p*')), 'Failed verification should retain parts')
        self.assertEqual(list(self.root.glob('.rangedl-*')), [])

    def test_batch_keeps_success_but_exits_nonzero_for_any_failure(self):
        result = self.run_jobs([('good.mp4', 'good'), ('bad.mp4', 'ignored')])
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / 'renoise-good.mp4').read_bytes(), self.payload)
        self.assertFalse((self.root / 'renoise-bad.mp4').exists())
        self.assertIn('good.mp4', result.stdout)
        self.assertIn('bad.mp4', result.stderr)

    def test_nonzero_curl_result_cannot_publish_complete_bytes(self):
        result = self.run_jobs([('clip.mp4', 'good')], injected_failure='curl-after-complete')
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Range transfer failed (curl 18)', result.stderr)
        self.assertFalse((self.root / 'renoise-clip.mp4').exists())
        self.assertEqual(list(self.root.glob('.p*')), [])

    def test_curl_retry_exhaustion_never_merges_output(self):
        result = self.run_jobs([('clip.mp4', 'good')], injected_failure='curl')
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('exhausted 30 attempts', result.stderr)
        self.assertEqual(self.requests, [])
        self.assertFalse((self.root / 'renoise-clip.mp4').exists())
        self.assertEqual(list(self.root.glob('.rangedl-*')), [])

    def test_decoder_return_code_and_error_output_both_gate_publication(self):
        original = b'existing file'
        final = self.root / 'renoise-clip.mp4'
        for mode in ['decoder-exit', 'decoder-stderr']:
            with self.subTest(mode=mode):
                final.write_bytes(original)
                result = self.run_jobs([('clip.mp4', 'good')], injected_failure=mode)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('Decode validation failed', result.stderr)
                self.assertEqual(final.read_bytes(), original)
                self.assertTrue(list(self.root.glob('.p*')))
                self.assertEqual(list(self.root.glob('.rangedl-*')), [])

    def test_duplicate_job_ids_are_rejected_before_download(self):
        result = self.run_jobs([('same.mp4', 'good'), ('same.mp4', 'ignored')])
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.requests, [])
        self.assertFalse((self.root / 'renoise-same.mp4').exists())


if __name__ == '__main__':
    unittest.main()
