#!/usr/bin/env python3
"""按 scenes.json 自动排音效（earshot 音效库），渲成一条 sfx_bus.wav。
用法：python3 lin_sfx.py <工程>/src/scenes.json --out <工程>/audio [--kit kit.json]
- 第一次跑会 earshot kit init --preset calm，并改两个角色：drop = cut_hit/punch（「碰」：景深字、大数字、算例结果），pop = ui_pop/soft（卡片、标签、条形图）
- 规则：每次画面类型切换（主播 / B-roll / 题板）一声 whoosh.short；数字卡、标签 pop；清单打勾、推导行 tick；公式新项、利率卡 land；关键结论 bell
- 档位：drop/bell +7 dB、pop/land +3 dB、whoosh −2 dB（2026-10 实测：不加的话「碰」只比人声+音乐高 5 dB，被埋）
- 输出 sfx_bus.wav（48k 立体声，与成片同长）、sfx_cues.json、cues_earshot.json（给 earshot timeline --cues 复查）
earshot（可选，EARSHOT_PY 指向它的 python，默认 ~/tools/earshot/.venv/bin/python）；没装就用工程 public/sfx（make_assets.py 合成）或 --sfx-dir 指定的目录兜底。"""
import json, os, subprocess, sys
from pathlib import Path
try:
    import numpy as np  # noqa
except ImportError:   # 系统 python 没装 numpy 时，换 earshot 自带的 python 重跑
    _E = os.environ.get('EARSHOT_PY', os.path.expanduser('~/tools/earshot/.venv/bin/python'))
    if os.path.exists(_E) and sys.executable != _E: os.execv(_E, [_E] + sys.argv)
    raise
a = sys.argv[1:]
if not a: sys.exit(__doc__)
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
SR = 48000
P = json.load(open(a[0])); total = P['total']; S = P['scenes']
out = Path(opt('--out', 'audio')); out.mkdir(parents=True, exist_ok=True)
EPY = os.environ.get('EARSHOT_PY', os.path.expanduser('~/tools/earshot/.venv/bin/python'))
kitj = Path(opt('--kit', out / 'kit.json'))
cues = []
def c(t, role, label): cues.append((round(float(t), 3), role, label))
prev = None
for s in S:
    a0, T = s['a'], s['type']; vis = 'host' if T == 'host' else ('broll' if T == 'broll' else 'board')
    if prev is not None and (vis != prev or vis == 'broll'): c(a0, 'whoosh.short', 'cut→' + T)
    prev = vis
    if T == 'host':
        d = s.get('depth')
        if d: c(d.get('at', a0), 'drop', '景深字')
        if s.get('lower'): c(a0 + 0.4, 'pop', 'lower')
        if s.get('lower2'): c(s['lower2']['at'], 'pop', 'lower2')
    elif T == 'broll':
        for i, _ in enumerate(s.get('float') or []): c(a0 + 0.2 + i * 0.3, 'pop', 'float')
        if s.get('card'): c(s['cardAt'], 'pop', 'card')
        if s.get('slam'): c(s['slamAt'], 'drop', 'slam')
        if s.get('banner'): c(s['bannerAt'], 'land', 'banner')
        for i, _ in enumerate(s.get('chips') or []): c(s['chipsAt'] + i * (1.3 if s.get('stagger') else 0.35), 'pop', 'chip')
        for i, t in enumerate(s.get('statAt') or []): c(t, 'drop' if i == 0 else 'land', 'stat')
        if s.get('doc'): c(s['docAt'], 'land.light', 'doc')
    elif T == 'board':
        if s.get('big'): c(a0 + 0.25, 'land', 'big')
        if s.get('choices'): c(a0 + 0.4, 'pop', 'A'); c(s['reveal'], 'pop', 'B')
        for t in s.get('itemsAt') or []: c(t, 'tick', 'item')
        for i, _ in enumerate(s.get('chips') or []): c(s['chipsAt'] + i * 0.45, 'pop', 'chip')
    elif T == 'rates':
        for t in s['cardsAt']: c(t, 'land', 'rate')
    elif T == 'curve': c(s['labelAt'], 'pop', 'label')
    elif T == 'fall':
        for t in s['stepsAt']: c(t, 'pop', 'step')
    elif T == 'assume': c(s['reveal'], 'land', 'box1'); c(s['reveal'] + 1.6, 'land', 'box2'); c(s['resultAt'], 'bell', 'result')
    elif T == 'formula':
        for t in s['linesAt']: c(t, 'tick', 'line')
    elif T == 'big': c(a0 + 0.2, 'land', 'top'); c(s['bottomAt'], 'drop', 'bottom')
    elif T == 'stickers':
        for it in s['items']:
            if it.get('at') is not None: c(it['at'], 'pop', 'sticker')
    elif T == 'bars':
        for t in s['barsAt']: c(t, 'pop', 'bar')
    elif T == 'formula2':
        seen = set()
        for tm in s['terms']:
            if tm['at'] not in seen: seen.add(tm['at']); c(tm['at'], 'land', 'term')
        if s.get('final'): c(a0 + 0.3, 'bell', 'final')
    elif T == 'calc':
        for t in s.get('rowAt') or []: c(t, 'tick', 'row')
        c(s['resAt'], 'drop', 'result'); c(s['resAt'] + 0.05, 'bell', 'result')
        if s.get('extra'): c(s['extraAt'], 'pop', 'extra')
cues.sort()
TRIM = {'drop': 7, 'bell': 7, 'pop': 3, 'land': 3, 'whoosh.short': -2}
bus = np.zeros((int((total + 3) * SR), 2))
def put(x, start):
    st = int(max(0, start) * SR); n = min(len(x), len(bus) - st)
    if n > 0: bus[st:st + n] += x[:n]
def load(f):   # 任意音频 → 48k 立体声 float（只靠 ffmpeg + numpy）
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(f), '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
if Path(EPY).exists():
    if not kitj.exists():
        subprocess.run([EPY, '-m', 'earshot', 'kit', 'init', '--preset', 'calm', '-o', str(kitj)], check=True)
        k = json.load(open(kitj))
        k['roles']['drop'] = {'sound': 'cut_hit/punch', 'takes': 3, 'align': 'onset', 'level_db': -4.0, 'note': '碰：景深字、大数字、算例结果'}
        k['roles']['pop'] = {'sound': 'ui_pop/soft', 'takes': 4, 'align': 'onset', 'level_db': -4.0, 'note': '卡片、标签、条形图'}
        k.get('off', {}).pop('drop', None); json.dump(k, open(kitj, 'w'), ensure_ascii=False, indent=1)
    subprocess.run([EPY, '-m', 'earshot', 'kit', 'render', str(kitj), '--out', str(out / 'kit')], check=True, capture_output=True)
    lock = json.load(open(out / 'kit' / 'kit.lock.json'))['roles']; idx = {}
    for t, role, _ in cues:
        r = lock[role]; takes = r['takes']; i = idx.get(role, 0); idx[role] = i + 1
        if role == 'bell': takes = [x for x in takes if x['file'] in ('bell_C6.wav', 'bell_E5.wav', 'bell_G5.wav')] or takes
        tk = takes[i % len(takes)]
        x = load(str(out / 'kit' / tk['file'])) * 10 ** ((float(r['level_db'] or 0) + TRIM.get(role, 0)) / 20)
        put(x, t + (r.get('offset_ms') or 0) / 1000 - tk[(r.get('align') or 'onset') + '_s'])
else:
    # 没装 earshot：用工程 public/sfx（new_edit.sh 调 make_assets.py 合成的那套），再不行用 promo-video 的
    cands = [Path(opt('--sfx-dir')) if opt('--sfx-dir') else None, Path(a[0]).resolve().parent.parent / 'public' / 'sfx', Path.home() / '.claude/skills/promo-video/assets/sfx']
    F = next((d for d in cands if d and (d / 'pop.wav').exists()), None)
    if not F: raise SystemExit('没装 earshot，也找不到音效目录：用 --sfx-dir 指定（要有 pop.wav whoosh.wav impact.wav tap.wav click.wav ding.wav）')
    M = {'whoosh.short': ('whoosh.wav', -14), 'drop': ('impact.wav', -4), 'pop': ('pop.wav', -8), 'land': ('tap.wav', -6), 'land.light': ('tap.wav', -10), 'tick': ('click.wav', -10), 'bell': ('ding.wav', -8)}
    print(f'没找到 earshot，用 {F} 的音效兜底')
    load_any = load
    cache = {}
    for t, role, _ in cues:
        f, g = M[role]
        if f not in cache: cache[f] = load_any(F / f) if (F / f).exists() else load_any(F / 'pop.wav')
        put(cache[f] * 10 ** (g / 20), t)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', str(out / 'sfx_bus.wav')], input=bus.astype(np.float32).tobytes(), check=True)
json.dump([{'t': t, 'role': r, 'label': l} for t, r, l in cues], open(out / 'sfx_cues.json', 'w'), ensure_ascii=False, indent=0)
json.dump([{'t': t, 'label': f'{r}:{l}'} for t, r, l in cues], open(out / 'cues_earshot.json', 'w'), ensure_ascii=False)
from collections import Counter
print(len(cues), '个音效', dict(Counter(r for _, r, _ in cues)), '→', out / 'sfx_bus.wav')
