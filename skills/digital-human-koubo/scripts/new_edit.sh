#!/bin/bash
# 起一个剪辑工程：bash new_edit.sh <模板> <工程目录>
#   模板：huazi-916（B 网红花字口播，数据驱动）
#         reference/launch-169 · reference/tutorial-169 · reference/multihost-169（C / D / E 参考实现，按段重写 Scene）
#   A 小林式解说用 finance-explainer：bash ~/.claude/skills/finance-explainer/scripts/setup_engine.sh <工程目录>
set -e
TPL="$1"; DST="$2"
[ -z "$TPL" ] || [ -z "$DST" ] && { echo "用法：bash new_edit.sh huazi-916 <工程目录>"; exit 1; }
SRC="$(cd "$(dirname "$0")/.." && pwd)/templates/$TPL"
[ -d "$SRC" ] || { echo "没有模板 $TPL（可用：huazi-916、reference/launch-169、reference/tutorial-169、reference/multihost-169）"; exit 1; }
[ -e "$DST/src" ] && { echo "$DST 里已经有 src/，不覆盖"; exit 1; }
mkdir -p "$DST" && cp -R "$SRC/." "$DST/"
# 参考实现不带素材：音效和配乐从花字模板拿
if [ ! -f "$DST/public/sfx/pop.wav" ]; then mkdir -p "$DST/public" && (cp -R "$(dirname "$SRC")/../huazi-916/public/sfx" "$(dirname "$SRC")/../huazi-916/public/music" "$DST/public/" 2>/dev/null || cp -R "$(dirname "$SRC")/huazi-916/public/sfx" "$(dirname "$SRC")/huazi-916/public/music" "$DST/public/" 2>/dev/null || true); fi
# node_modules：npm 源常 SSL 失败，优先从本机已有的 Remotion 4.0.408 工程克隆（APFS 克隆不占空间）
for c in ${DH_NODE_MODULES_FROM:-} ~/Desktop/packaging-lab ~/Desktop/renoise-koubo/edit ~/Desktop/renoise-academy-ep3/film; do   # 本机已有 Remotion 工程就克隆它的 node_modules（可用 DH_NODE_MODULES_FROM 指定），否则 npm install
  if [ -d "$c/node_modules/remotion" ] && [ -d "$c/node_modules/lottie-web" ] && [ -d "$c/node_modules/d3-geo" ]; then cp -cR "$c/node_modules" "$DST/" 2>/dev/null || cp -R "$c/node_modules" "$DST/"; echo "node_modules ← $c"; break; fi
done
[ -d "$DST/node_modules" ] || (cd "$DST" && npm install)
# 音效 / 占位配乐：仓库里不带第三方音频，缺了就用代码合成一套（无版权）
if [ ! -f "$DST/public/sfx/pop.wav" ] || [ ! -f "$DST/public/music/bgm.mp3" ]; then
  PY=""; for p in python3 python3.14 python3.13 python3.12 python3.11 python; do command -v $p >/dev/null 2>&1 && $p -c "import numpy" 2>/dev/null && PY=$p && break; done
  [ -n "$PY" ] && "$PY" "$(dirname "$0")/make_assets.py" "$DST/public" || echo "⚠ 没找到装了 numpy 的 Python，音效没生成：python3 -m pip install numpy 后跑 python3 $(dirname "$0")/make_assets.py $DST/public"
fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ "$TPL" = "lin-169" ]; then
  echo "✓ $DST 已就绪（小林式）。放入 public/main.mp4（cut/joined.mp4）、public/broll/、public/stickers/、public/cut/*.webm；然后："
  echo "  python3 $ROOT/scripts/lin_subs.py script.json --tl $DST/src/tl.json --out $DST/src/cues.json --disp disp.txt"
  echo "  python3 $ROOT/scripts/lin_scenes.py plan.json --tl $DST/src/tl.json --out $DST/src/scenes.json --face   （plan 写法见 $DST/plan.example.json）"
  echo "  python3 $ROOT/scripts/lin_sfx.py $DST/src/scenes.json --out audio && python3 $ROOT/scripts/lin_mix.py --voice cut/joined.mov --bgm 曲子 --sfx audio/sfx_bus.wav --out $DST/public/mix.wav"
elif [ "$TPL" = "huazi-916" ]; then
  echo "✓ $DST 已就绪。放入 public/main.mp4、public/voice.wav、src/tl.json，改 src/edit.json，然后："
  echo "  python3 $ROOT/scripts/check_edit.py $DST/src"
else
  echo "✓ $DST 已就绪（参考实现）。换 src 里的时间轴，按本期稿子重写 Scene；素材路径看代码里的 staticFile(…)"
fi
