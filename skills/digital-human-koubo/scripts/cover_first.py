#!/usr/bin/env python3
"""把封面图接到成片最前面，当开头帧（平台默认取首帧做封面）。
python3 cover_first.py <成片.mp4> <封面.jpg> <输出.mp4> [--hold 0.5]
封面停 hold 秒后硬切进正片；声音整体往后推 hold 秒，前面补静音。画幅、帧率跟成片一致，封面按画幅铺满居中裁切。"""
import json
import subprocess
import sys


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    a, b = s["r_frame_rate"].split("/")
    return s["width"], s["height"], round(int(a) / int(b))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 3:
        sys.exit(__doc__)
    src, cover, out = args
    hold = float(sys.argv[sys.argv.index("--hold") + 1]) if "--hold" in sys.argv else 0.5
    w, h, fps = probe(src)
    ms = round(hold * 1000)
    fc = (f"[1:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={fps},format=yuv420p,trim=duration={hold}[c];"
          f"[0:v]setsar=1,format=yuv420p[m];[c][m]concat=n=2:v=1:a=0[v];"
          f"[0:a]adelay={ms}:all=1,alimiter=limit=0.79:level=false[a]")   # 重编 AAC 会让峰值抬高 0.5–1 dB，先限到约 -2 dBFS，编码后真峰值 ≤ -1
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-loop", "1", "-framerate", str(fps), "-t", str(hold), "-i", cover,
                    "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    print(f"→ {out}（封面 {hold:g} 秒 + 正片）")


if __name__ == "__main__":
    main()
