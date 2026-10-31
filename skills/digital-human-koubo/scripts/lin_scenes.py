#!/usr/bin/env python3
"""小林式剪辑：把人写的分镜 plan.json 换成 Lin.tsx 用的 scenes.json（整片绝对秒）。
用法：python3 lin_scenes.py plan.json --tl <工程>/src/tl.json --out <工程>/src/scenes.json
plan.json = {"config": {...可选：face/audio/disclosure/brollTag/colors}, "scenes": [{"type": ..., "a": "@s01", "b": "@s01:有人说", ...}, ...]}
时间写法（任何字段、任何嵌套里以 @ 开头的字符串都会被换成秒）：
  "@s07"          s07 这段开头
  "@s07:end"      s07 这段结尾
  "@s07:两千"     s07 里第一次出现「两千」那个字的时间（tl.json 逐字时间，按 script.json 的念法写，别写阿拉伯数字）
  "@s07:两千|-0.2" 再提前 0.2 秒（| 后面是偏移秒数）
检查：相邻场景不衔接（>0.05 秒空隙）会报 GAP；broll 默认 circle-bl 小窗。
--face：从 public/main.mp4 第 3 秒量主播脸中心，写进 config.face（换形象/机位后跑一次）。"""
import json, sys, re
from pathlib import Path
a = sys.argv[1:]
if not a: sys.exit(__doc__)
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
plan = json.load(open(a[0])); tl = json.load(open(opt('--tl', 'src/tl.json'))); S = {s['id']: s for s in tl['segs']}

def at(ref):
    m = re.match(r'^@(s\d+)(?::([^|]+))?(?:\|([-+]?\d*\.?\d+))?$', ref)
    if not m: raise SystemExit(f'看不懂的时间写法：{ref}')
    sid, trig, off = m.group(1), m.group(2), float(m.group(3) or 0)
    if sid not in S: raise SystemExit(f'{ref}：tl.json 里没有 {sid}')
    s = S[sid]
    if not trig: t = s['start']
    elif trig == 'end': t = s['end']
    else:
        i = s['text'].find(trig)
        if i < 0: raise SystemExit(f'{ref}：{sid} 的稿子里找不到「{trig}」（稿子：{s["text"]}）')
        ch = {int(k): v for k, v in s['chars'].items()}; ks = [k for k in ch if k >= i]
        t = ch[min(ks)] if ks else s['start']
    return round(t + off, 3)

def walk(x):
    if isinstance(x, str) and x.startswith('@'): return at(x)
    if isinstance(x, list): return [walk(v) for v in x]
    if isinstance(x, dict): return {k: walk(v) for k, v in x.items()}
    return x

scenes = [walk(s) for s in plan['scenes']]
for s in scenes:
    if s['type'] == 'broll': s.setdefault('pip', 'circle-bl')
bad = 0
for x, y in zip(scenes, scenes[1:]):
    if abs(x['b'] - y['a']) > 0.05: print(f"GAP {x['type']} 结束 {x['b']} → {y['type']} 开始 {y['a']}"); bad += 1
cfg = plan.get('config', {})
if '--face' in a:
    import subprocess, tempfile, os
    root = Path(opt('--out', 'src/scenes.json')).resolve().parent.parent
    sw = Path(__file__).with_name('face_center.swift')
    png = tempfile.mktemp(suffix='.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '3', '-i', str(root / 'public/main.mp4'), '-frames:v', '1', '-vf', 'scale=1920:1080', png], check=True)
    out = subprocess.run(['swift', str(sw), png], capture_output=True, text=True).stdout.split()
    if len(out) == 2: cfg['face'] = [int(float(out[0])), int(float(out[1]))]; print('face', cfg['face'])
out = {'total': tl['total'], 'config': cfg, 'scenes': scenes}
json.dump(out, open(opt('--out', 'src/scenes.json'), 'w'), ensure_ascii=False, indent=0)
print(f"{len(scenes)} 个场景 · 总长 {tl['total']} 秒 · {'有 ' + str(bad) + ' 处空隙' if bad else '首尾相接'}")
