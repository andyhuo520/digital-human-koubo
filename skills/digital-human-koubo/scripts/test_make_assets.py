"""Asset CLI regressions; requires numpy and ffmpeg, just like make_assets.py.

Run: python -m unittest discover -s skills/digital-human-koubo/scripts -p test_make_assets.py -v
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave


# Run the real script and ffmpeg, recording the intermediate input before conversion.
_RUN = r"""
import json, os, runpy, subprocess, sys, time
from pathlib import Path
from unittest.mock import patch

real_run = subprocess.run

def convert(args, **kwargs):
    source = Path(args[args.index('-i') + 1])
    assert source.is_file(), source
    with open(os.environ['ASSET_TEST_LOG'], 'a', encoding='utf-8') as log:
        log.write(json.dumps(str(source)) + '\n')
    peer = os.environ.get('ASSET_TEST_PEER')
    if peer:
        deadline = time.monotonic() + 20
        while not Path(peer).exists():
            if time.monotonic() > deadline:
                raise TimeoutError('Other asset process did not reach conversion')
            time.sleep(0.02)
    if os.environ.get('ASSET_TEST_FAIL'):
        args = ['ffmpeg', '-asset-test-intentional-error']
    return real_run(args, **kwargs)

sys.argv = sys.argv[1:]
with patch('subprocess.run', side_effect=convert):
    runpy.run_path(sys.argv[0], run_name='__main__')
"""


@unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg is required')
class MakeAssetsTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix='dh-assets-test-')
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.scratch = self.root / '临时 文件'
        self.scratch.mkdir()
        self.script = Path(__file__).with_name('make_assets.py').resolve()

    def start(self, name, targets, *, script=None, peer=None, fail=False):
        log = self.root / (name + '.jsonl')
        env = dict(os.environ, TMPDIR=str(self.scratch), TEMP=str(self.scratch),
                   TMP=str(self.scratch), PYTHONIOENCODING='utf-8',
                   PYTHONDONTWRITEBYTECODE='1', ASSET_TEST_LOG=str(log))
        if peer:
            env['ASSET_TEST_PEER'] = str(self.root / (peer + '.jsonl'))
        if fail:
            env['ASSET_TEST_FAIL'] = '1'
        child = subprocess.Popen(
            [sys.executable, '-c', _RUN, str(script or self.script), *map(str, targets)],
            cwd=self.root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8',
        )
        self.addCleanup(self.stop, child)
        return child, log

    @staticmethod
    def stop(child):
        if child.poll() is None:
            child.kill()
        child.communicate()

    def finish(self, child, log, *, success=True):
        stdout, stderr = child.communicate(timeout=90)
        if success:
            self.assertEqual(child.returncode, 0, stdout + stderr)
        else:
            self.assertNotEqual(child.returncode, 0, stdout + stderr)
            self.assertIn('CalledProcessError', stderr)
        inputs = [Path(json.loads(line)) for line in log.read_text(encoding='utf-8').splitlines()]
        self.assertTrue(inputs)
        for path in inputs:
            self.assertEqual(path.parent.parent, self.scratch)
            self.assertFalse(path.parent.exists(), 'Intermediate directory leaked')
        return inputs

    def assert_assets(self, public, *, existing_music=None):
        sounds = list((public / 'sfx').glob('*.wav'))
        self.assertEqual(len(sounds), 30)
        for sound in sounds:
            with wave.open(str(sound), 'rb') as audio:
                self.assertEqual((audio.getnchannels(), audio.getsampwidth(), audio.getframerate()),
                                 (2, 2, 48000))
                self.assertGreater(audio.getnframes(), 0)
        music = public / 'music' / 'bgm.mp3'
        if existing_music is not None:
            self.assertEqual(music.read_bytes(), existing_music)
        else:
            result = subprocess.run(
                ['ffmpeg', '-v', 'error', '-i', str(music), '-f', 'null', '-'],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_explicit_project_and_public_paths_preserve_existing_music(self):
        project = self.root / '音频 项目'
        public = self.root / 'existing project' / 'public'
        (public / 'music').mkdir(parents=True)
        original = b'user-provided soundtrack: must not be replaced'
        (public / 'music' / 'bgm.mp3').write_bytes(original)
        inputs = self.finish(*self.start('explicit', [project, public]))
        self.assertEqual(len(inputs), 1)
        self.assert_assets(project / 'public')
        self.assert_assets(public, existing_music=original)
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_default_discovers_both_skills_and_ignores_node_modules(self):
        skills = self.root / 'skills'
        script = skills / 'digital-human-koubo' / 'scripts' / 'make_assets.py'
        script.parent.mkdir(parents=True)
        shutil.copyfile(self.script, script)
        projects = [skills / 'digital-human-koubo' / 'templates' / 'one',
                    skills / 'finance-explainer' / 'templates' / 'two']
        ignored = projects[0] / 'node_modules' / 'dependency'
        for project in [*projects, ignored]:
            project.mkdir(parents=True, exist_ok=True)
            (project / 'package.json').write_text('{}', encoding='utf-8')
        inputs = self.finish(*self.start('default', [], script=script))
        self.assertEqual(len(inputs), 2)
        self.assertEqual(inputs[0], inputs[1])
        for project in projects:
            self.assert_assets(project / 'public')
        self.assertFalse((ignored / 'public').exists())
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_ffmpeg_failure_propagates_and_cleans_intermediate(self):
        self.finish(*self.start('failure', [self.root / 'failed project'], fail=True), success=False)
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_concurrent_runs_use_independent_intermediates(self):
        first = self.start('first', [self.root / 'first project'], peer='second')
        second = self.start('second', [self.root / 'second project'], peer='first')
        first_inputs = self.finish(*first)
        second_inputs = self.finish(*second)
        self.assertNotEqual(first_inputs[0].parent, second_inputs[0].parent)
        self.assert_assets(self.root / 'first project' / 'public')
        self.assert_assets(self.root / 'second project' / 'public')
        self.assertEqual(list(self.scratch.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
