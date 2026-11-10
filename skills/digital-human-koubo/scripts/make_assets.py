#!/usr/bin/env python3
"""Synthesize every sound effect the templates use, plus a placeholder background track — all generated
from code, so there is no third-party copyright in this repo.
程序合成模板用到的全部音效 + 一条占位配乐（纯代码生成，无第三方版权）。

Usage / 用法:
  python3 scripts/make_assets.py                 # fill every template of this skill + the sibling finance-explainer skill
  python3 scripts/make_assets.py <project>/public # fill one project (new_edit.sh does this automatically)
Replace music/bgm.mp3 with any track you have the rights to (e.g. Mixkit / YouTube Audio Library).
想换更好的配乐：把有授权的曲子放到 public/music/bgm.mp3 覆盖即可。
Requires: numpy, ffmpeg (for the mp3).
"""
import subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np

SR = 48000
rng = np.random.default_rng(42)
t_ = lambda d: np.arange(int(SR * d)) / SR
def env(n, a=0.002, r=0.1):
    x = np.arange(n) / SR
    return np.minimum(1, x / max(a, 1e-4)) * np.exp(-x / max(r, 1e-4))
def lp(x, k):            # simple one-pole low-pass, k in (0,1]
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc += k * (v - acc); y[i] = acc
    return y
def bp_noise(d, lo, hi):  # band-limited noise via FFT mask
    n = int(SR * d); X = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0; y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)
def sweep_noise(d, f0, f1):
    n = int(SR * d); out = np.zeros(n); seg = 2048
    for i in range(0, n, seg):
        c = f0 + (f1 - f0) * i / n; out[i:i + seg] = bp_noise(seg / SR, c * 0.6, c * 1.6)[: len(out[i:i + seg])]
    return out
def tone(f, d, shape="sine"):
    t = t_(d); ph = 2 * np.pi * np.cumsum(np.broadcast_to(f, t.shape)) / SR if np.ndim(f) else 2 * np.pi * f * t
    return np.sin(ph) if shape == "sine" else np.sign(np.sin(ph)) * 0.5
def norm(x, peak=0.8): return x / (np.abs(x).max() + 1e-9) * peak
def write_wav(p, x):
    x = np.clip(x, -1, 1); st = np.stack([x, x], 1); d = (st * 32767).astype("<i2")
    with wave.open(str(p), "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes())

def sfx():
    S = {}
    n = lambda d: int(SR * d)
    S["click"] = norm(bp_noise(0.04, 2000, 9000) * env(n(0.04), 0.0005, 0.008), 0.7)
    S["tap"] = norm(tone(1800, 0.06) * env(n(0.06), 0.001, 0.015) + 0.3 * bp_noise(0.06, 3000, 8000) * env(n(0.06), 0.0005, 0.006), 0.6)
    S["pop"] = norm(tone(np.linspace(900, 420, n(0.12)), 0.12) * env(n(0.12), 0.002, 0.04), 0.75)
    S["ding"] = norm(sum(a * tone(f, 1.2) for f, a in [(1318.5, 1), (2637, 0.35), (3951, 0.15)]) * env(n(1.2), 0.002, 0.35), 0.6)
    S["done"] = norm(np.concatenate([tone(880, 0.16) * env(n(0.16), 0.003, 0.08), tone(1318.5, 0.6) * env(n(0.6), 0.003, 0.25)]), 0.6)
    S["whoosh"] = norm(sweep_noise(0.55, 300, 4000) * np.hanning(n(0.55)), 0.6)
    for k, (a, b, d) in enumerate([(500, 5000, 0.3), (800, 6000, 0.25), (400, 3500, 0.35)], 1):
        S[f"swish-{k}"] = norm(sweep_noise(d, a, b) * np.hanning(n(d)) ** 1.5, 0.55)
    thump = lambda f0, d: tone(np.linspace(f0, 40, n(d)), d) * env(n(d), 0.001, d / 4)
    S["impact"] = norm(thump(120, 0.7) + 0.35 * bp_noise(0.7, 100, 2500) * env(n(0.7), 0.001, 0.06), 0.9)
    for k, f0 in enumerate([140, 110, 90], 1):
        S[f"slam-{k}"] = norm(thump(f0, 0.5) + 0.5 * bp_noise(0.5, 200, 5000) * env(n(0.5), 0.0005, 0.04), 0.9)
    S["cut"] = norm(bp_noise(0.08, 1500, 12000) * env(n(0.08), 0.0003, 0.012) + 0.4 * thump(200, 0.08), 0.7)
    for k in range(1, 9):
        f = 2500 + 300 * k; d = 0.05
        S[f"key-{k}"] = norm(bp_noise(d, f * 0.7, f * 1.6) * env(n(d), 0.0004, 0.006 + 0.001 * k) + 0.2 * thump(300, d), 0.5)
    S["key-space"] = norm(bp_noise(0.08, 800, 4000) * env(n(0.08), 0.0005, 0.012) + 0.3 * thump(180, 0.08), 0.55)
    for k in range(1, 4):
        S[f"page-{k}"] = norm(sweep_noise(0.35, 1500 + 400 * k, 6000) * np.hanning(n(0.35)) ** 0.7 * (0.6 + 0.4 * rng.random(n(0.35))), 0.5)
    for k in range(1, 3):
        S[f"paper-place-{k}"] = norm(bp_noise(0.18, 300, 3000) * env(n(0.18), 0.002, 0.04 + 0.01 * k) + 0.3 * thump(160, 0.18), 0.6)
    S["processing"] = norm(np.concatenate([tone(f, 0.07) * env(n(0.07), 0.002, 0.02) for f in [880, 1046, 1174, 1318, 1046, 1568, 1318, 1760] * 2]), 0.4)
    S["riser"] = norm(sweep_noise(1.6, 200, 7000) * np.linspace(0, 1, n(1.6)) ** 2 + 0.3 * tone(np.linspace(200, 900, n(1.6)), 1.6) * np.linspace(0, 1, n(1.6)), 0.6)
    return S

def bgm(seconds=95, bpm=112):
    """Upbeat four-on-the-floor loop: kick, offbeat hat, clap, bass, chords (I–V–vi–IV in C)."""
    beat = 60 / bpm; n = int(SR * seconds); mix = np.zeros(n)
    def add(x, at):
        i = int(at * SR); j = min(n, i + len(x))
        if i < n: mix[i:j] += x[: j - i]
    kick = tone(np.linspace(110, 45, int(SR * 0.25)), 0.25) * env(int(SR * 0.25), 0.001, 0.09)
    hat = bp_noise(0.05, 7000, 14000) * env(int(SR * 0.05), 0.0005, 0.012)
    clap = bp_noise(0.18, 900, 4500) * env(int(SR * 0.18), 0.001, 0.05)
    chords = [[261.6, 329.6, 392.0], [196.0, 246.9, 293.7], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6]]
    roots = [65.4, 49.0, 55.0, 43.7]
    k = 0; t = 0.0
    while t < seconds:
        bar = (k // 4) % 4
        add(0.9 * kick, t); add(0.25 * hat, t + beat / 2)
        if k % 2 == 1: add(0.35 * clap, t)
        bass = tone(roots[bar] * 2, beat * 0.9) * env(int(SR * beat * 0.9), 0.005, beat * 0.5)
        add(0.35 * bass, t + beat / 2)
        if k % 4 == 0:
            d = beat * 4; pad = sum(tone(f, d) + 0.5 * tone(f * 2.003, d) for f in chords[bar]) * env(int(SR * d), 0.08, d * 0.8)
            add(0.08 * pad, t)
        k += 1; t += beat
    fade = np.ones(n); fl = int(SR * 2); fade[:fl] = np.linspace(0, 1, fl); fade[-fl:] = np.linspace(1, 0, fl)
    return norm(lp(mix, 0.6) * fade, 0.7)

def fill(pub: Path, S, music_wav: Path):
    (pub / "sfx").mkdir(parents=True, exist_ok=True); (pub / "music").mkdir(parents=True, exist_ok=True)
    for name, x in S.items(): write_wav(pub / "sfx" / f"{name}.wav", x)
    mp3 = pub / "music" / "bgm.mp3"
    if not mp3.exists():
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(music_wav), "-b:a", "192k", str(mp3)], check=True)
    print(f"✓ {pub}  ({len(S)} sfx{' + placeholder bgm.mp3' if mp3.exists() else ''})")

if __name__ == "__main__":
    skill = Path(__file__).resolve().parent.parent
    S = sfx()
    targets = [Path(a) for a in sys.argv[1:]] or [p.parent for p in list(skill.glob("templates/**/package.json")) + list((skill.parent / "finance-explainer").glob("templates/**/package.json")) if "node_modules" not in p.parts]
    with tempfile.TemporaryDirectory(prefix="dh-bgm-") as temp_dir:
        tmp = Path(temp_dir) / "bgm.wav"
        write_wav(tmp, bgm())
        for tdir in targets:
            fill(tdir if tdir.name == "public" else tdir / "public", S, tmp)
