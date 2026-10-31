#!/usr/bin/env python3
"""只替换念错的短句，保住口型（不整片换音色）。
用法：python3 patch_words.py script.json patch.json [--cut cut] [--ref s24,s41,s05]
patch.json = [{"id": "s11", "g": [2.1, 5.4], "m": [2.0, 5.3]}, ...]
  g = 原片里要换掉的那几句（秒，粗略即可，会吸附到最近的停顿）；m = 克隆音整句里对应的那几句（先不填，跑一次 --synth-only 再看时间）
步骤：
  1. --synth-only：用 --ref 指定的 2–3 段干净原声（合计 ≥15 秒）当参照，MiMo voiceclone 把要修的段整句重配到 cut/revoice/<id>.wav，并打印逐字时间
  2. 填好 m 再跑：克隆句 atempo 拉到和原句一样长（0.85–1.15 之外会警告：句子差太多，口型会飘）→ 响度对齐 → 25 ms 交叉淡化贴回 → 写回 cut/<id>.mp4（画面不动、长度不变）→ 不带提示转写复核
  3. 改完跑 assemble.py --rejoin 重新拼接（会做音画等长校验）
切点选在停顿上：一句话中间切会有接缝；整句换比只换两个字自然（2026-10 实测：只换「城镇」两字转写成「承认」，换整句就对）。"""
import json, os, re, subprocess, sys, base64
from pathlib import Path
import numpy as np
from scipy.io import wavfile
a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
S = {s['id']: s for s in json.load(open(a[0]))}; spec = json.load(open(a[1])); cut = Path(opt('--cut', 'cut')); SR = 48000
rv = cut / 'revoice'; rv.mkdir(exist_ok=True)
WM = os.environ.get('WHISPER_MODEL') or next((p for p in map(os.path.expanduser, ['~/Library/Application Support/Murmur/models/ggml-medium-q5_0.bin', '~/models/ggml-medium-q5_0.bin']) if os.path.exists(p)), None)
def whisper(wav, ml=False):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-ar', '16000', '-ac', '1', '/tmp/_pw16.wav'])
    if ml:
        subprocess.run(['whisper-cli', '-m', WM, '-l', 'zh', '--prompt', '以下是普通话的句子。', '-ml', '1', '-oj', '-of', '/tmp/_pwml', '-f', '/tmp/_pw16.wav'], capture_output=True)
        return ' '.join(f"{t['text'].strip()}@{t['offsets']['from'] / 1000:.2f}" for t in json.load(open('/tmp/_pwml.json', errors='replace'))['transcription'] if t['text'].strip())
    return subprocess.run(['whisper-cli', '-m', WM, '-l', 'zh', '-nt', '-f', '/tmp/_pw16.wav'], capture_output=True, text=True).stdout.strip().replace('\n', '')
if '--synth-only' in a or not all('m' in p for p in spec):
    for d in [Path(__file__).parent, Path(__file__).resolve().parents[2] / 'finance-explainer/scripts', Path.home() / '.claude/skills/finance-explainer/scripts', Path.home() / '.claude/skills/promo-video/scripts']:
        if (d / 'narrate_mimo.py').exists(): sys.path.insert(0, str(d)); break
    import narrate_mimo as N   # MiMo 调用（密钥读 MIMO_API_KEY 或 ~/.config/ai-teardown/mimo.env）
    key, base = N.env()
    refs = (opt('--ref') or '').split(',')
    if not refs[0]: sys.exit('要 --ref：2–3 段念得干净的原片段 id（合计 ≥15 秒）')
    ins = sum([['-i', str(cut / f'{r}.mp4')] for r in refs], [])
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ''.join(f'[{i}:a]' for i in range(len(refs))) + f'concat=n={len(refs)}:v=0:a=1,aresample=24000', '-ac', '1', str(rv / 'ref.wav')], check=True)
    ref = 'data:audio/wav;base64,' + base64.b64encode((rv / 'ref.wav').read_bytes()).decode()
    for p in spec:
        out = rv / f"{p['id']}.wav"
        d = N.call(key, base, {'model': 'mimo-v2.5-tts-voiceclone', 'messages': [{'role': 'assistant', 'content': S[p['id']]['t']}], 'audio': {'format': 'wav', 'voice': ref}})
        out.with_suffix('.raw.wav').write_bytes(base64.b64decode(d['choices'][0]['message']['audio']['data']))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(out.with_suffix('.raw.wav')), '-af', 'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03', '-ar', str(SR), '-ac', '1', str(out)], check=True)
        print(p['id'], '克隆整句：', whisper(str(out)), '\n   逐字：', whisper(str(out), True))
    sys.exit('填好 patch.json 里每条的 m（克隆音里对应句子的起止秒）再跑一次')
def sil(f):
    o = subprocess.run(['ffmpeg', '-i', f, '-af', 'silencedetect=n=-34dB:d=0.05', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return [(x + y) / 2 for x, y in zip([float(v) for v in re.findall(r'silence_start: ([\d.]+)', o)], [float(v) for v in re.findall(r'silence_end: ([\d.]+)', o)])]
snap = lambda t, mids: min([m for m in mids if abs(m - t) <= 0.28], key=lambda m: abs(m - t), default=t)
def L(f):
    sr, x = wavfile.read(f); x = x.astype(np.float64) / 32768.0; return x if x.ndim == 1 else x.mean(1)
rms = lambda x: np.sqrt(np.mean(x ** 2) + 1e-12)
by = {}
for p in spec: by.setdefault(p['id'], []).append(p)
for sid, ps in by.items():
    src = cut / f'{sid}.mp4'; bak = cut / f'{sid}.orig.mp4'
    if not bak.exists(): bak.write_bytes(src.read_bytes())
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(bak), '-ac', '1', '-ar', str(SR), '/tmp/_pw_g.wav'], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(rv / f'{sid}.wav'), '-ac', '1', '-ar', str(SR), '/tmp/_pw_m.wav'], check=True)
    g = L('/tmp/_pw_g.wav'); y = g.copy(); m = L('/tmp/_pw_m.wav'); gm, mm = sil('/tmp/_pw_g.wav'), sil('/tmp/_pw_m.wav')
    for p in sorted(ps, key=lambda p: -p['g'][0]):
        ga, gb = snap(p['g'][0], gm), min(snap(p['g'][1], gm), len(g) / SR); ma, mb = snap(p['m'][0], mm), min(snap(p['m'][1], mm), len(m) / SR)
        tempo = (mb - ma) / (gb - ga)
        if not 0.85 <= tempo <= 1.15: print(f'⚠ {sid} 伸缩 {tempo:.2f}：克隆句和原句长度差太多，口型会飘，考虑换一次克隆或调切点')
        wavfile.write('/tmp/_pw_in.wav', SR, (m[int(ma * SR):int(mb * SR)] * 32767).astype(np.int16))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', '/tmp/_pw_in.wav', '-af', f'atempo={tempo:.4f}', '-ar', str(SR), '/tmp/_pw_out.wav'], check=True)
        seg = L('/tmp/_pw_out.wav'); n = int((gb - ga) * SR); seg = np.pad(seg, (0, max(0, n - len(seg))))[:n]
        seg *= rms(g[int(ga * SR):int(gb * SR)]) / rms(seg)
        f = int(0.025 * SR); w = np.ones(n); w[:f] = np.linspace(0, 1, f); w[-f:] = np.linspace(1, 0, f)
        a0 = int(ga * SR); y[a0:a0 + n] = y[a0:a0 + n] * (1 - w) + seg * w
        print(f'{sid} 换 {ga:.2f}–{gb:.2f}s（克隆 {ma:.2f}–{mb:.2f}，伸缩 {tempo:.3f}）')
    wavfile.write('/tmp/_pw_fixed.wav', SR, (np.clip(y, -1, 1) * 32767).astype(np.int16))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(bak), '-i', '/tmp/_pw_fixed.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-ac', '2', '-c:a', 'aac', '-b:a', '192k', '-shortest', str(src)], check=True)
    print(f'   复核（不带提示）：{whisper("/tmp/_pw_fixed.wav")}')
print('改完跑：python3 assemble.py script.json ids.json --rejoin')
