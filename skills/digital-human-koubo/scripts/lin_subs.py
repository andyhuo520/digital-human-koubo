#!/usr/bin/env python3
"""tl.json → cues.json 底部字幕（按标点断句，一句一条）。
用法：python3 lin_subs.py script.json --tl <工程>/src/tl.json --out <工程>/src/cues.json [--disp disp.txt]
--disp：每段一行的「显示稿」，标点断句数要和 script.json 一致；用来把念法换成写法（「五百万」→「500万」「百分之八」→「8%」）。
不给就直接用 script.json 的 t（段落里的 sub 映射也会套上）。"""
import json, re, sys
a = sys.argv[1:]
if not a: sys.exit(__doc__)
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
S = json.load(open(a[0])); tl = json.load(open(opt('--tl', 'src/tl.json')))
D = [l.strip() for l in open(opt('--disp'))] if opt('--disp') else None
D = [l for l in D if l] if D else None
P = '，。？！：；'; subs = []
for k, seg in enumerate(tl['segs']):
    t = seg['text']; disp = D[k] if D else t
    if not D:
        for x, y in (S[k].get('sub') or {}).items(): disp = disp.replace(x, y)
    ch = {int(i): v for i, v in seg['chars'].items()}
    at = lambda i: (ch[min([j for j in ch if j >= i])] if [j for j in ch if j >= i] else seg['end'])
    cl = [c for c in re.split(f'(?<=[{P}])', t) if c.strip()]; dl = [c for c in re.split(f'(?<=[{P}])', disp) if c.strip()]
    if len(cl) != len(dl): sys.exit(f"{seg['id']}：显示稿断句数 {len(dl)} ≠ 念稿 {len(cl)}\n  念：{t}\n  显：{disp}")
    pos, times = 0, []
    for c in cl: times.append(at(pos)); pos += len(c)
    for i, c in enumerate(dl):
        a0 = max(seg['start'], times[i] - 0.08); b0 = (times[i + 1] - 0.08) if i + 1 < len(times) else seg['end'] - 0.05
        subs.append({'a': round(a0, 2), 'b': round(b0, 2), 't': c.rstrip('，。：；')})
json.dump({'subs': subs, 'total': tl['total']}, open(opt('--out', 'src/cues.json'), 'w'), ensure_ascii=False, indent=0)
print(len(subs), '条字幕')
