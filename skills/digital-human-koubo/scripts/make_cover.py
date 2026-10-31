#!/usr/bin/env python3
"""数字人口播封面：cover.json → cover_16x9.jpg / cover_9x16.jpg / cover_3x4.jpg（HTML 排版 + Playwright 截图）。
用法：
  python3 make_cover.py cover.json                 # 按 ratios 出图，写到 cover.json 同目录的 cover/ 下
  python3 make_cover.py cover.json --candidates    # 先从主播视频里抽 12 帧拼成候选图 cover/candidates.jpg，挑一帧填 host.t
cover.json 字段（见 references/cover.md）：
  ratios ["16:9","3:4"] · theme paper|dark · accent_color · kicker · title · accent · sub · tags[≤3] · url
  host {"video": "…/host.mp4", "t": 3.2} 或 {"image": "…jpg"} · props [{"image": "…png", "crop": [x0,y0,x1,y1]}]（≤2 张斜放的证据卡）
  disclosure（默认「内容由 AI 数字人演绎」）
路径都相对 cover.json 所在目录。"""
import base64, html, json, os, subprocess, sys, tempfile
from pathlib import Path

SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "3:4": (1080, 1440)}
HEADLESS = sorted(Path.home().glob("Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-mac-arm64/chrome-headless-shell"))


def frame(video, t, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", str(out)], check=True)


def data_uri(path, crop=None):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if crop: im = im.crop(tuple(crop))
    tmp = Path(tempfile.mkdtemp()) / "x.jpg"; im.save(tmp, quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(tmp.read_bytes()).decode()


def candidates(spec, root, outdir):
    from PIL import Image, ImageDraw
    v = root / spec["host"]["video"]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(v)], capture_output=True, text=True).stdout)
    ts = [round(dur * (i + 0.5) / 12, 2) for i in range(12)]
    tiles = []
    for t in ts:
        p = outdir / f"_c_{t}.jpg"; frame(v, t, p)
        im = Image.open(p); im.thumbnail((300, 540)); tiles.append((t, im)); p.unlink()
    W, H = tiles[0][1].size
    sheet = Image.new("RGB", (6 * (W + 8), 2 * (H + 8)), "white")
    for i, (t, im) in enumerate(tiles):
        x, y = (i % 6) * (W + 8), (i // 6) * (H + 8); sheet.paste(im, (x, y))
        ImageDraw.Draw(sheet).text((x + 6, y + 6), f"t={t}", fill=(255, 0, 0))
    sheet.save(outdir / "candidates.jpg"); print("候选帧 →", outdir / "candidates.jpg", "（挑笑着、眼睛睁开、手势自然的一帧，写进 host.t）")


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:%(W)dpx;height:%(H)dpx;overflow:hidden;font-family:"PingFang SC","Hiragino Sans GB",sans-serif;background:%(bg)s;color:%(ink)s;position:relative}
.dots{position:absolute;inset:0;background-image:radial-gradient(%(dot)s 2px,transparent 2px);background-size:30px 30px}
.kicker{font-size:%(k)dpx;font-weight:700;color:%(mute)s;letter-spacing:3px;white-space:nowrap}
.title{font-weight:900;line-height:1.08;white-space:nowrap;letter-spacing:2px}
.accent{color:%(acc)s}
.sub{font-weight:800;white-space:nowrap}
.tags{display:flex;gap:18px;flex-wrap:nowrap}
.tag{font-weight:800;color:#fff;background:%(ink)s;border-radius:16px;padding:10px 24px;white-space:nowrap}
.url{font-family:"SF Mono",Menlo,monospace;font-weight:600;color:%(mute)s;white-space:nowrap}
.host{position:absolute;overflow:hidden;border-radius:36px;box-shadow:0 40px 90px rgba(15,20,25,.28);background:#cfd0d3}
.host img{width:100%%;height:100%%;object-fit:cover;object-position:50%% 20%%;display:block}
.prop{position:absolute;border-radius:22px;overflow:hidden;border:8px solid #fff;box-shadow:0 30px 70px rgba(15,20,25,.3);background:#fff}
.prop img{width:100%%;display:block}
.disc{position:absolute;right:28px;bottom:16px;font-size:22px;color:%(mute)s}
"""

FIT = """
for (const el of document.querySelectorAll('[data-max]')) {
  const max = +el.dataset.max; let fs = parseFloat(getComputedStyle(el).fontSize);
  while (el.scrollWidth > max && fs > 20) { fs -= 2; el.style.fontSize = fs + 'px'; }
}
"""


def page(spec, ratio, host_uri, props):
    W, H = SIZES[ratio]
    dark = spec.get("theme") == "dark"
    pal = dict(W=W, H=H, bg="#0f1419" if dark else "radial-gradient(ellipse at 30% 20%,#fdfdfd 0%,#f4f5f6 50%,#e6e8eb 100%)",
               ink="#ffffff" if dark else "#0f1419", mute="#8b98a5" if dark else "#536471",
               dot="rgba(255,255,255,.06)" if dark else "rgba(15,20,25,.08)", acc=spec.get("accent_color", "#f4212e"), k=34)
    e = lambda s: html.escape(s or "")
    tags = "".join(f'<div class="tag" style="font-size:{40 if ratio != "9:16" else 44}px">{e(x)}</div>' for x in spec.get("tags", [])[:3])
    disc = e(spec.get("disclosure", "内容由 AI 数字人演绎"))
    if ratio == "16:9":
        tx, tw = 110, 880
        text = f"""<div style="position:absolute;left:{tx}px;top:190px;width:{tw}px;display:flex;flex-direction:column;gap:30px">
          <div class="kicker" data-max="{tw}">{e(spec.get('kicker'))}</div>
          <div class="title" style="font-size:132px" data-max="{tw}">{e(spec['title'])}</div>
          <div class="title accent" style="font-size:168px;margin-top:-6px" data-max="{tw}">{e(spec.get('accent'))}</div>
          <div class="sub" style="font-size:48px;margin-top:6px" data-max="{tw + 40}">{e(spec.get('sub'))}</div>
          <div class="tags" style="margin-top:8px">{tags}</div>
          <div class="url" style="font-size:40px;margin-top:14px" data-max="{tw}">{e(spec.get('url'))}</div></div>"""
        hostbox = (1300, 50, 540, 980)
        propbox = [(1010, 560, 520, -6), (1000, 150, 500, 5)]
    elif ratio == "3:4":
        tw = 960
        text = f"""<div style="position:absolute;left:60px;top:70px;width:{tw}px;display:flex;flex-direction:column;gap:18px">
          <div class="kicker" data-max="{tw}">{e(spec.get('kicker'))}</div>
          <div class="title" style="font-size:118px" data-max="{tw}">{e(spec['title'])}</div>
          <div class="title accent" style="font-size:140px" data-max="{tw}">{e(spec.get('accent'))}</div>
          <div class="sub" style="font-size:44px" data-max="{tw}">{e(spec.get('sub'))}</div></div>
          <div style="position:absolute;left:60px;bottom:120px;display:flex;flex-direction:column;gap:22px;width:560px">
          <div class="tags" style="flex-wrap:wrap">{tags}</div><div class="url" style="font-size:30px" data-max="560">{e(spec.get('url'))}</div></div>"""
        hostbox = (640, 560, 400, 820)
        propbox = [(80, 640, 560, -5)]
    else:  # 9:16：主播铺满，下方暗渐变压大字
        tw = 960
        text = f"""<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(15,20,25,0) 38%,rgba(15,20,25,.82) 66%,rgba(15,20,25,.95) 100%)"></div>
          <div style="position:absolute;left:60px;bottom:150px;width:{tw}px;display:flex;flex-direction:column;gap:22px;color:#fff">
          <div class="kicker" style="color:#c9d1d9" data-max="{tw}">{e(spec.get('kicker'))}</div>
          <div class="title" style="font-size:124px" data-max="{tw}">{e(spec['title'])}</div>
          <div class="title" style="font-size:140px;color:#ffd400" data-max="{tw}">{e(spec.get('accent'))}</div>
          <div class="sub" style="font-size:46px" data-max="{tw}">{e(spec.get('sub'))}</div>
          <div class="tags">{tags.replace('class="tag"', 'class="tag" style="background:#fff;color:#0f1419;font-size:40px"')}</div></div>"""
        hostbox = (0, 0, W, H)
        propbox = [(600, 420, 440, 6)]
    hx, hy, hw, hh = hostbox
    hstyle = f"left:{hx}px;top:{hy}px;width:{hw}px;height:{hh}px" + (";border-radius:0;box-shadow:none" if ratio == "9:16" else "")
    ptags = "".join(f'<div class="prop" style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({r}deg)"><img src="{u}"></div>'
                    for (x, y, w, r), u in zip(propbox, props))
    behind = ratio != "9:16"   # 横版 / 3:4：证据卡压在主播卡后面；竖版：卡片浮在主播上
    body = (ptags + f'<div class="host" style="{hstyle}"><img src="{host_uri}"></div>' if behind else f'<div class="host" style="{hstyle}"><img src="{host_uri}"></div>' + ptags)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS % pal}</style></head><body>
      {'' if ratio == '9:16' else '<div class="dots"></div>'}{body}{text}<div class="disc" style="{'color:#c9d1d9' if ratio == '9:16' else ''}">{disc}</div>
      <script>{FIT}</script></body></html>"""


def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    spec_path = Path(a[0]).resolve(); root = spec_path.parent
    spec = json.loads(spec_path.read_text())
    outdir = root / spec.get("out_dir", "cover"); outdir.mkdir(exist_ok=True)
    if "--candidates" in a:
        return candidates(spec, root, outdir)
    h = spec["host"]
    if "image" in h: host_uri = data_uri(root / h["image"])
    else:
        p = outdir / "host_frame.png"; frame(root / h["video"], h.get("t", 1.0), p); host_uri = data_uri(p)
    props = [data_uri(root / p["image"], p.get("crop")) for p in spec.get("props", [])[:2]]
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        kw = {"executable_path": str(HEADLESS[-1])} if HEADLESS else {}
        br = pw.chromium.launch(**kw)
        for ratio in spec.get("ratios", ["16:9"]):
            W, H = SIZES[ratio]
            pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            pg.set_content(page(spec, ratio, host_uri, props)); pg.wait_for_timeout(300)
            out = outdir / f"cover_{ratio.replace(':', 'x')}.jpg"
            pg.screenshot(path=str(out), type="jpeg", quality=93); pg.close()
            from PIL import Image
            th = Image.open(out); th.thumbnail((540, 960)); th.save(outdir / f"thumb_{ratio.replace(':', 'x')}.jpg")
            print("封面 →", out, "（缩略图 thumb_*.jpg：540 宽时标题还要读得清）")
        br.close()


if __name__ == "__main__":
    main()
