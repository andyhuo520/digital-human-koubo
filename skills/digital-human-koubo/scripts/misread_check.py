#!/usr/bin/env python3
"""查数字人念错字：每段按停顿切成短句，**只带「普通话、简体」这句中性提示（不带原文）**逐句转写，和稿子逐字比。
用法：python3 misread_check.py script.json [--ids s10,s11] [--cut cut] [--out cut/misread.json]
为什么不用 assemble.py 的转写：whisper 带了原文 --prompt 会把念错的字「纠正」回去（2026-10 实测：「通胀」念成 tōng zhèng，带原文转写全对，不带才露出「通证」）。
输出每段：稿子 / 听到的短句 / 可疑字（稿子里的汉字没被听到的，数字和英文字母忽略）。可疑 ≠ 一定念错（同音字、方言腔会误报），用户要听；确认要修的写进 patch.json 给 patch_words.py。"""
import json, os, re, subprocess, sys, difflib
a = sys.argv[1:]
if not a: sys.exit(__doc__)
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
S = json.load(open(a[0])); cut = opt('--cut', 'cut'); ids = set(opt('--ids').split(',')) if opt('--ids') else None
WM = os.environ.get('WHISPER_MODEL') or next((p for p in map(os.path.expanduser, ['~/Library/Application Support/Murmur/models/ggml-medium-q5_0.bin', '~/models/ggml-medium-q5_0.bin', '~/.cache/whisper/ggml-medium-q5_0.bin']) if os.path.exists(p)), None)
T2S = str.maketrans('們說這個裡麼開銷費國來長還沒錢會時後們對嗎讓過買兩萬億號歲學實際資產聽們讀變賺樂頭點為發見體條經義遠業應與夠單從當進現產間關門問題風險銀行條證寶貝數據統計報告億幾萬塊元萬', '们说这个里么开销费国来长还没钱会时后们对吗让过买两万亿号岁学实际资产听们读变赚乐头点为发见体条经义远业应与够单从当进现产间关门问题风险银行条证宝贝数据统计报告亿几万块元万')
HAN = re.compile('[^' + chr(0x4e00) + '-' + chr(0x9fff) + ']')
NUMC = '零〇一二三四五六七八九十百千万亿点两'
han = lambda s: HAN.sub('', s.translate(T2S).replace('百分之', ''))
hanx = lambda s: ''.join(ch for ch in han(s) if ch not in NUMC)   # 数字两边写法不同（五百万 / 500万），比对时去掉
rep = []
for s in S:
    sid = s['id']
    if ids and sid not in ids: continue
    src = f'{cut}/{sid}.mp4'; wav = f'/tmp/_mr_{sid}.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ar', '16000', '-ac', '1', wav], check=True)
    o = subprocess.run(['ffmpeg', '-i', wav, '-af', 'silencedetect=n=-32dB:d=0.18', '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', o)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', o)]
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav], capture_output=True, text=True).stdout)
    cuts = [0.0] + [(x + y) / 2 for x, y in zip(st, en) if x > 0.2 and y < dur - 0.1] + [dur]
    heard = []
    for x, y in zip(cuts, cuts[1:]):
        if y - x < 0.4: continue
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{x:.2f}', '-to', f'{y:.2f}', '-i', wav, '/tmp/_mr_w.wav'])
        r = subprocess.run(['whisper-cli', '-m', WM, '-l', 'zh', '--prompt', '以下是普通话，用简体中文。', '-nt', '-f', '/tmp/_mr_w.wav'], capture_output=True, text=True).stdout.strip().replace('\n', '')
        heard.append({'t': [round(x, 2), round(y, 2)], 'heard': r})
    A, B = hanx(s['t']), hanx(''.join(h['heard'] for h in heard))
    miss = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if op in ('replace', 'delete'): miss.append(f"{A[i1:i2]}→{B[j1:j2] or '∅'}")
    rep.append({'id': sid, 'text': s['t'], 'clauses': heard, 'suspect': miss})
    print(f"{'⚠' if miss else ' '} {sid} {' '.join(miss)}\n     " + ' '.join(f"[{h['t'][0]}-{h['t'][1]}]{h['heard']}" for h in heard))
json.dump(rep, open(opt('--out', f'{cut}/misread.json'), 'w'), ensure_ascii=False, indent=1)
