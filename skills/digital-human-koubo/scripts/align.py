#!/usr/bin/env python3
"""逐字时间轴：把 assemble.py 的 cut/<id>.json（whisper 逐字）和文稿对齐，输出剪辑模板用的 tl.json。
用法：python3 align.py script.json [--out edit/src/tl.json]
tl.json = {"total": 秒, "segs": [{"i","id","start","end","text","chars":{"字符下标": 秒}}]}（chars 是整片绝对时间）
字幕和念法不一样时，在 script.json 那段加 "sub": {"SKILL 点 M D": "SKILL.md"}：对齐按念法，字幕显示右边的写法，时间跟着换。"""
import json, difflib, sys
from pathlib import Path
a = sys.argv[1:]
if not a: sys.exit(__doc__)
S = json.load(open(a[0])); Q = {r['id']: r for r in json.load(open('cut/qa.json'))}
out = a[a.index('--out') + 1] if '--out' in a else 'edit/src/tl.json'
PUNCT = set('，。、：；！？,.:;!? “”「」')
T0 = 0.0; segs = []
for i, s in enumerate(S, 1):
    sid, text = s['id'], s['t']; keep = Q[sid]['keep']
    tk = []
    for t in json.load(open(f'cut/{sid}.json', errors='replace'))['transcription']:
        a0, a1 = t['offsets']['from'] / 1000, t['offsets']['to'] / 1000; tx = t['text'].strip()
        if not tx or tx.startswith('['): continue
        for k, ch in enumerate(tx):
            if ch not in PUNCT: tk.append((ch.lower(), a0 + (a1 - a0) * k / len(tx)))
    clean = [(j, ch.lower()) for j, ch in enumerate(text) if ch not in PUNCT]
    A = ''.join(c for _, c in clean); B = ''.join(c for c, _ in tk)
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False); st = [None] * len(clean)
    for bl in sm.get_matching_blocks():
        for k in range(bl.size): st[bl.a + k] = tk[bl.b + k][1]
    known = [k for k, v in enumerate(st) if v is not None]
    for k in range(len(st)):
        if st[k] is None:
            lo = max([j for j in known if j < k], default=None); hi = min([j for j in known if j > k], default=None)
            st[k] = 0.0 if lo is None and hi is None else (st[hi] if lo is None else (st[lo] + 0.18 * (k - lo) if hi is None else st[lo] + (st[hi] - st[lo]) * (k - lo) / (hi - lo)))
    cov = sum(bl.size for bl in sm.get_matching_blocks()) / max(1, len(A))
    ch = {j: T0 + st[k] for k, (j, _) in enumerate(clean)}
    for say, show in s.get('sub', {}).items():        # 念法 → 字幕写法，这几个字的时间在原跨度里均分
        p0 = text.find(say)
        if p0 < 0: print(f'   ⚠ {sid} 找不到 sub「{say}」'); continue
        span = [ch[j] for j in range(p0, p0 + len(say)) if j in ch]; a0, a1 = (span[0], span[-1]) if span else (T0, T0)
        d = len(show) - len(say)
        ch = {**{j: v for j, v in ch.items() if j < p0}, **{j + d: v for j, v in ch.items() if j >= p0 + len(say)},
              **{p0 + k: a0 + (a1 - a0) * k / max(1, len(show) - 1) for k, c in enumerate(show) if c not in PUNCT}}
        text = text[:p0] + show + text[p0 + len(say):]
    segs.append(dict(i=i, id=sid, start=round(T0, 3), end=round(T0 + keep, 3), text=text, chars={str(j): round(v, 3) for j, v in sorted(ch.items())}))
    print(f'{i:2d} {sid:5s} 对齐 {cov:.0%}  {T0:.2f}–{T0 + keep:.2f}')
    T0 += keep
Path(out).parent.mkdir(parents=True, exist_ok=True)
json.dump(dict(total=round(T0, 3), segs=segs), open(out, 'w'), ensure_ascii=False, indent=0)
print('total', round(T0, 2), '→', out)
