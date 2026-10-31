#!/usr/bin/env python3
"""人声链 + BGM 循环避让 + 音效 → 母带 -16 LUFS；可选变速导出成片。
用法：
  python3 lin_mix.py --voice cut/joined.mov --bgm 曲子.mp3 --sfx audio/sfx_bus.wav --out edit/public/mix.wav [--voice-out edit/public/voice.wav] [--male]
  python3 lin_mix.py ... --speed 1.1 --video edit/out/lin.mp4 --final 成片_1.1x.mp4   # 人声和音效 atempo、画面 setpts，BGM 保持原速只裁长度
- 人声链（女声默认）：高通 90 / 220 Hz +1.5 / 420 Hz −2 / 3.2 kHz +2 / 10 kHz +1.5 / 去齿音 / 压缩 3:1 / −17 LUFS；--male 换成 140 Hz +3.5 那条
- BGM：循环（3 秒交叉淡化）到够长，−24 LUFS 打底，sidechain 被人声压（threshold 0.04 ratio 5），结尾 5 秒淡出
- 音效总线 −8 dB；总线 limiter + loudnorm −16 LUFS / −1.5 dBTP
- 不加 --speed 时只出 mix.wav（给 Remotion 的 public/），--video/--final 给了就顺手把 mix 套到渲好的画面上"""
import subprocess, sys, json
a = sys.argv[1:]
if not a: sys.exit(__doc__)
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
voice, bgm, sfx, out = opt('--voice'), opt('--bgm'), opt('--sfx'), opt('--out', 'mix.wav')
sp = float(opt('--speed', 1.0)); vout = opt('--voice-out')
dur = lambda f: float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout)
run = lambda *c: subprocess.run(['ffmpeg', '-v', 'error', '-y', *c], check=True)
chain = ("highpass=f=70,equalizer=f=140:t=o:w=1:g=3.5,equalizer=f=420:t=o:w=1:g=-2,equalizer=f=3200:t=o:w=1:g=3" if '--male' in a else
         "highpass=f=90,equalizer=f=220:t=o:w=1:g=1.5,equalizer=f=420:t=o:w=1:g=-2,equalizer=f=3200:t=o:w=1:g=2,equalizer=f=10000:t=o:w=1:g=1.5,deesser=i=0.35") + \
        ",acompressor=threshold=-22dB:ratio=3:attack=5:release=100:makeup=2,loudnorm=I=-17:TP=-2:LRA=7"
vw = vout or '/tmp/_lin_voice.wav'
run('-i', voice, '-vn', '-af', chain, '-ar', '48000', '-ac', '2', vw)
L = dur(vw) / sp
bl = dur(bgm); n = int(L // max(1, bl - 3)) + 2
ins = sum([['-i', bgm] for _ in range(n)], [])
xf = ''.join(f"[{'a' if i else '0:a'}{i if i else ''}][{i + 1}:a]acrossfade=d=3[a{i + 1}];" for i in range(n - 1)).replace('[a0]', '[0:a]')
run(*ins, '-filter_complex', f"{xf}[a{n - 1}]atrim=0:{L + 1:.2f},afade=t=in:d=1,afade=t=out:st={max(0, L - 5):.2f}:d=5,aresample=48000,loudnorm=I=-24:TP=-3[o]" if n > 1 else f"[0:a]atrim=0:{L + 1:.2f},afade=t=out:st={max(0, L - 5):.2f}:d=5,aresample=48000,loudnorm=I=-24:TP=-3[o]",
    '-map', '[o]', '-ac', '2', '/tmp/_lin_bgm.wav')
tempo = f'atempo={sp},' if sp != 1 else ''
fx = f"[2:a]{tempo}volume=-8dB[fx];" if sfx else ''
mixn = 3 if sfx else 2
run('-i', '/tmp/_lin_bgm.wav', '-i', vw, *(['-i', sfx] if sfx else []), '-filter_complex',
    f"[1:a]{tempo}asplit=2[v][key];[0:a][key]sidechaincompress=threshold=0.04:ratio=5:attack=30:release=400:makeup=1[bg];{fx}"
    f"[v][bg]{'[fx]' if sfx else ''}amix=inputs={mixn}:normalize=0:duration=first,alimiter=limit=0.89:level=false,loudnorm=I=-16:TP=-1.5:LRA=9[m]",
    '-map', '[m]', '-ar', '48000', out)
print('mix', out, round(dur(out), 2), 's')
if opt('--video') and opt('--final'):
    if sp != 1:
        run('-i', opt('--video'), '-i', out, '-filter_complex', f'[0:v]setpts=PTS/{sp},fps=30[v]', '-map', '[v]', '-map', '1:a', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', opt('--final'))
    else:
        run('-i', opt('--video'), '-i', out, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', opt('--final'))
    print('成片', opt('--final'), round(dur(opt('--final')), 2), 's')
