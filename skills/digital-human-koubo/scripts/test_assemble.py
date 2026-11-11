"""Run with python -m unittest discover -s skills/digital-human-koubo/scripts -p test_assemble.py.

Uses real ffmpeg/ffprobe media I/O. Only whisper-cli is replaced by a local
child-process fixture, so no ASR model or external service is needed.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('assemble.py')
WRAPPER = '''import runpy, subprocess, sys
from pathlib import Path
run = subprocess.run
def dispatch(cmd, *args, **kwargs):
    if cmd[0] == 'whisper-cli':
        cmd = [sys.executable, str(Path(__file__).with_name('whisper.py')), *cmd[1:]]
    return run(cmd, *args, **kwargs)
subprocess.run = dispatch
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
'''
WHISPER = '''import json, os, sys
from pathlib import Path
mode = os.environ['ASSEMBLE_TEST_MODE']
with open('whisper-calls.jsonl', 'a') as log:
    log.write(json.dumps(sys.argv[1:]) + '\\n')
if mode == 'fail':
    sys.stderr.write('fixture transcription failed\\n')
    sys.exit(7)
if mode == 'missing':
    sys.exit(0)
output = Path(sys.argv[sys.argv.index('-of') + 1] + '.json')
transcription = [{'text': '你好' if mode == 'zh' else 'hello', 'offsets': {'from': 0, 'to': 1000}}]
if mode == 'empty':
    transcription = []
if mode == 'noise':
    transcription = [{'text': ' [BLANK_AUDIO] ', 'offsets': {'from': 0, 'to': 1000}}]
output.write_text('{' if mode == 'malformed' else json.dumps({
    'transcription': transcription, 'fixture': 'fresh',
}, ensure_ascii=False), encoding='utf-8')
if mode == 'write_then_fail':
    sys.stderr.write('fixture transcription failed\\n')
    sys.exit(7)
'''


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg and ffprobe required')
class AssembleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media = tempfile.TemporaryDirectory(prefix='dh-assemble-media-')
        cls.addClassCleanup(cls.media.cleanup)
        cls.clip = Path(cls.media.name) / 'clip.mp4'
        subprocess.run([
            'ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=blue:s=160x90:r=30',
            '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '2',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ac', '2', str(cls.clip),
        ], check=True, capture_output=True)

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='dh-assemble-中文 ')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'gen').mkdir()
        (self.root / 'cut').mkdir()
        (self.root / 'script.json').write_text(json.dumps([
            {'id': 's1', 't': 'hello', 'lang_code': 'en'},
        ]))
        (self.root / 'ids.json').write_text('{"s1": 1}')
        (self.root / 'runner.py').write_text(WRAPPER)
        (self.root / 'whisper.py').write_text(WHISPER, encoding='utf-8')
        shutil.copyfile(self.clip, self.root / 'gen/renoise-1.mp4')
        for name in ('cut/s1.mp4', 'final.mp4'):
            shutil.copyfile(self.clip, self.root / name)
        (self.root / 'cut/s1.json').write_text(json.dumps({
            'transcription': [{'text': 'stale', 'offsets': {'from': 0, 'to': 1800}}],
            'fixture': 'old',
        }))
        (self.root / 'cut/qa.json').write_text('[{"id": "s1", "keep": 2}]')
        self.previous = {name: (self.root / name).read_bytes() for name in (
            'cut/s1.mp4', 'cut/s1.json', 'cut/qa.json', 'final.mp4',
        )}

    def run_assemble(self, mode, *args):
        return subprocess.run([
            sys.executable, str(self.root / 'runner.py'), str(SCRIPT),
            'script.json', 'ids.json', '--out', 'final.mp4', *args,
        ], cwd=self.root, env={**os.environ, 'ASSEMBLE_TEST_MODE': mode,
                               'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'},
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)

    def assert_preserved(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        for name, previous in self.previous.items():
            self.assertEqual((self.root / name).read_bytes(), previous, name)
        self.assertEqual(list((self.root / 'cut').glob('whisper-*')), [])

    def test_failed_transcription_preserves_previous_outputs(self):
        for mode in ('fail', 'write_then_fail'):
            with self.subTest(mode=mode):
                result = self.run_assemble(mode)
                self.assert_preserved(result)
                self.assertIn('fixture transcription failed', result.stderr)

    def test_success_without_a_new_transcript_cannot_reuse_stale_json(self):
        self.assert_preserved(self.run_assemble('missing'))

    def test_empty_or_noise_only_transcription_does_not_trim_the_clip(self):
        for mode in ('empty', 'noise'):
            with self.subTest(mode=mode):
                result = self.run_assemble(mode)
                self.assert_preserved(result)
                self.assertIn('no transcribed speech', result.stderr)

    def test_malformed_transcript_does_not_replace_previous_json(self):
        self.assert_preserved(self.run_assemble('malformed'))

    def test_chinese_transcription_keeps_utf8_and_prompt_options(self):
        (self.root / 'script.json').write_text(json.dumps([{'id': 's1', 't': '你好'}]))
        result = self.run_assemble('zh')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        transcript = json.loads((self.root / 'cut/s1.json').read_text(encoding='utf-8'))
        self.assertEqual(transcript['transcription'][0]['text'], '你好')
        qa = json.loads((self.root / 'cut/qa.json').read_text(encoding='utf-8'))
        self.assertEqual(qa[0]['acc'], 1.0)
        self.assertEqual(qa[0]['heard'], '你好')
        args = json.loads((self.root / 'whisper-calls.jsonl').read_text())
        self.assertEqual(args[args.index('-l') + 1], 'zh')
        self.assertEqual(args[args.index('--prompt') + 1], '以下是普通话的句子。')
        self.assertEqual(args[args.index('-ml') + 1], '1')

    def test_fresh_transcript_drives_trimming_and_rejoin_skips_asr(self):
        result = self.run_assemble('ok')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        transcript = json.loads((self.root / 'cut/s1.json').read_text())
        self.assertEqual(transcript['fixture'], 'fresh')
        qa = json.loads((self.root / 'cut/qa.json').read_text())[0]
        self.assertEqual(qa['heard'], 'hello')
        self.assertEqual(qa['speech'], [0.0, 1.0])
        self.assertAlmostEqual(qa['keep'], 1.25, delta=1 / 30)
        duration = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', str(self.root / 'final.mp4'),
        ], check=True, capture_output=True, text=True)
        self.assertAlmostEqual(float(duration.stdout), 1.25, delta=0.05)
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(self.root / 'final.mp4'),
                        '-f', 'null', '-'], check=True, capture_output=True)
        calls = (self.root / 'whisper-calls.jsonl').read_bytes()
        args = json.loads(calls)
        self.assertEqual(args[args.index('-l') + 1], 'en')
        result = self.run_assemble('fail', '--rejoin')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / 'whisper-calls.jsonl').read_bytes(), calls)
        self.assertEqual(list((self.root / 'cut').glob('whisper-*')), [])


if __name__ == '__main__':
    unittest.main()
