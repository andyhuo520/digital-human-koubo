#!/usr/bin/env python3
"""逐段回听 → 剪掉段尾空白 → 统一规格 → 拼接。
用法：python3 assemble.py script.json ids.json [--out 成片_完整版.mp4] [--lang zh] [--size 宽x高（默认保持源尺寸）]
- script.json：[{"id","t",...}]（和 build_tasks.py 同一份）；ids.json：{"s1": 363509, ...}（段 id → Renoise taskId）；下载的文件在 gen/renoise-<taskId>.mp4
- 每段：whisper 转写（中性提示，不用 --prompt 原文，免得漏前半句）→ 和文稿比准确率 → 只保留到说完后 0.25 秒
- 输出 cut/<id>.mp4（30fps、48k 立体声）、cut/<id>.json（逐字时间，align.py 用）、cut/qa.json、拼接好的 --out（-16 LUFS）
- 准确率 < 85% 的段打 ⚠，先人工听；真念错就单独重拍那段
- 念错字另用 misread_check.py（不带原文提示逐句转写）查，用 patch_words.py 只换错句；改完 --rejoin 只重新拼接
- 拼接前每段音频补齐/裁到和画面完全等长（PCM .mov 中转），否则几十段拼下来声音会累积落后口型（2026-10 实测 44 段到 4:43 晚 0.38 秒）"""
import json, subprocess, difflib, re, os, sys
from pathlib import Path
a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
S = json.load(open(a[0])); IDS = json.load(open(a[1]))
opt = lambda k, d: a[a.index(k) + 1] if k in a else d
out_name, lang, size = opt('--out', '成片_完整版.mp4'), opt('--lang', 'zh'), opt('--size', '')
REJOIN = '--rejoin' in a
WM = os.environ.get('WHISPER_MODEL') or next((p for p in map(os.path.expanduser, ['~/Library/Application Support/Murmur/models/ggml-medium-q5_0.bin', '~/models/ggml-medium-q5_0.bin', '~/.cache/whisper/ggml-medium-q5_0.bin', '~/models/ggml-medium.bin']) if os.path.exists(p)), '~/models/ggml-medium-q5_0.bin')
clean = lambda s: re.sub(r'[\s，。、：；！？,.:;!?“”]', '', s).lower()
Path('cut').mkdir(exist_ok=True); rep = []
for s in ([] if REJOIN else S):
    sid = s['id']; src = f"gen/renoise-{IDS[sid]}.mp4"; wav = f'cut/{sid}.wav'
    lg = s.get('lang_code', lang)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-ar', '16000', '-ac', '1', wav], check=True)
    cmd = ['whisper-cli', '-m', WM, '-l', lg] + (['--prompt', '以下是普通话的句子。', '-ml', '1'] if lg == 'zh' else []) + ['-oj', '-of', f'cut/{sid}', '-f', wav]
    subprocess.run(cmd, capture_output=True)
    d = [t for t in json.load(open(f'cut/{sid}.json', errors='replace'))['transcription'] if t['text'].strip() and not t['text'].strip().startswith('[')]
    heard = ''.join(t['text'] for t in d)
    st = min(t['offsets']['from'] for t in d) / 1000 if d else 0; en = max(t['offsets']['to'] for t in d) / 1000 if d else 0
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
    w, h = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.split(','))
    sz = size or f'{w - w % 2}x{h - h % 2}'          # 保持源尺寸（Grok 9:16 720p 是 720×1280，别拉成 720×1440）
    acc = difflib.SequenceMatcher(None, clean(s['t']), clean(heard)).ratio()
    keep = min(dur, en + 0.25)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-t', f'{keep:.3f}', '-vf', f'scale={sz.replace("x", ":")}:flags=lanczos,fps=30,format=yuv420p',
                    '-af', f'aresample=48000,afade=t=out:st={max(0, keep - 0.12):.3f}:d=0.12', '-ac', '2', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k', f'cut/{sid}.mp4'], check=True)
    rep.append(dict(id=sid, acc=round(acc, 3), speech=[round(st, 2), round(en, 2)], keep=round(keep, 2), src_dur=round(dur, 2), heard=heard))
    print(f"{'⚠' if acc < 0.85 else ' '}{sid:5s} 准确率 {acc:.0%}  说话 {st:.2f}–{en:.2f}s  保留 {keep:.2f}/{dur:.2f}s  听到：{heard}")
if REJOIN: rep = json.load(open('cut/qa.json'))
else: json.dump(rep, open('cut/qa.json', 'w'), ensure_ascii=False, indent=1)
# 拼接：每段音频 pad/trim 到画面帧数长度（PCM），keep 改成真实画面长度，保证 align.py 的累计时间 = 拼好的画面时间
Path('cut/_join').mkdir(exist_ok=True); Q = {r['id']: r for r in rep}
for s in S:
    f = f"cut/{s['id']}.mp4"
    nfr = int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip())
    vd = nfr / 30
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f, '-map', '0:v', '-map', '0:a', '-c:v', 'copy', '-af', f'aresample=48000,apad,atrim=0:{vd:.5f}', '-c:a', 'pcm_s16le', f"cut/_join/{s['id']}.mov"], check=True)
    Q[s['id']]['keep'] = round(vd, 5)
json.dump(rep, open('cut/qa.json', 'w'), ensure_ascii=False, indent=1)
open('cut/list.txt', 'w').write(''.join(f"file '_join/{s['id']}.mov'\n" for s in S))
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'cut/list.txt', '-c:v', 'copy', '-c:a', 'pcm_s16le', 'cut/joined.mov'], check=True)
sd = lambda f, sel: float(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', sel, '-show_entries', 'stream=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip() or 0)
dv, da = sd('cut/joined.mov', 'v:0'), sd('cut/joined.mov', 'a:0')
print(('✓' if abs(dv - da) < 0.02 else '⚠ 音画不等长') + f' 拼接 画面 {dv:.3f}s / 声音 {da:.3f}s')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'cut/joined.mov', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', 'cut/joined.mp4'], check=True)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'cut/joined.mov', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out_name], check=True)
print('拼接完成', out_name, round(sum(r['keep'] for r in rep), 2), '秒（剪辑用 cut/joined.mov / joined.mp4，未做响度）')
