#!/bin/bash
# 本机环境检查：有的打 ✓ 跳过，缺的才列装法（先列本机系统的，再列其他方式）。不自动安装。
# 用法：bash doctor.sh        退出码 0 = 齐了，1 = 有缺的
OS=$(uname -s); case "$OS" in Darwin) SYS=mac;; Linux) SYS=linux;; MINGW*|MSYS*|CYGWIN*) SYS=win;; *) SYS=other;; esac
MISS=0; OUT=""
ok(){ printf "  ✓ %s\n" "$1"; }
need(){ # need 名称 用途 mac装法 win装法 linux装法 其他装法
  MISS=1; printf "  ✗ %s（%s）\n" "$1" "$2"
  case $SYS in mac) first="$3";; win) first="$4";; linux) first="$5";; *) first="$6";; esac
  printf "      推荐：%s\n" "$first"
  for kv in "macOS|$3" "Windows|$4" "Linux|$5" "其他|$6"; do n=${kv%%|*}; v=${kv#*|}; [ "$v" = "$first" ] || [ -z "$v" ] || printf "      %s：%s\n" "$n" "$v"; done
}
echo "数字人口播 · 本机环境检查（$OS）"
command -v ffmpeg >/dev/null && ok "ffmpeg $(ffmpeg -version | head -1 | awk '{print $3}')" || need "ffmpeg" "抽帧、拼接、响度" "brew install ffmpeg" "winget install Gyan.FFmpeg  或  choco install ffmpeg" "sudo apt install ffmpeg  （或 dnf / pacman）" "ffmpeg.org 下载安装包"
PY=$(command -v python3.14 || command -v python3 || command -v python)
if [ -n "$PY" ]; then
  ok "Python $($PY -c 'import sys;print(sys.version.split()[0])')"
  for m in numpy:numpy PIL:pillow; do mod=${m%%:*}; pkg=${m#*:}
    $PY -c "import $mod" 2>/dev/null && ok "$pkg" || need "$pkg" "声音统一 / 预览图" "$PY -m pip install $pkg" "$PY -m pip install $pkg" "$PY -m pip install $pkg" "conda install $pkg"
  done
  PWI="$PY -m pip install playwright && $PY -m playwright install chromium"
  $PY -c "import playwright" 2>/dev/null && ok "playwright" || need "playwright + chromium" "封面排版截图（make_cover.py）" "$PWI" "$PWI" "$PWI" "$PWI"
else need "Python 3" "回听、对齐、声音统一脚本" "brew install python" "winget install Python.Python.3.12" "sudo apt install python3 python3-pip" "python.org 下载，或装 Anaconda / Miniconda"; fi
if command -v node >/dev/null; then
  v=$(node -v | tr -d v | cut -d. -f1); [ "$v" -ge 18 ] && ok "Node $(node -v)" || need "Node 18 以上（现在是 $(node -v)）" "Remotion 剪辑" "brew upgrade node" "winget upgrade OpenJS.NodeJS.LTS" "nvm install --lts" "nodejs.org 下载 LTS"
else need "Node 18+" "Remotion 剪辑" "brew install node" "winget install OpenJS.NodeJS.LTS" "sudo apt install nodejs npm  或  nvm install --lts" "nodejs.org 下载 LTS"; fi
if command -v whisper-cli >/dev/null; then
  ok "whisper-cli"
  M=$(ls "${WHISPER_MODEL:-/nonexistent}" ~/Library/Application\ Support/Murmur/models/ggml-medium*.bin ~/models/ggml-medium*.bin ~/.cache/whisper/ggml-medium*.bin 2>/dev/null | head -1)
  [ -n "$M" ] && ok "whisper 模型 $(basename "$M")" || need "whisper 模型 ggml-medium-q5_0.bin" "逐段回听、逐字对齐" "下载到 ~/models/：curl -L -o ~/models/ggml-medium-q5_0.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium-q5_0.bin" "浏览器打开 huggingface.co/ggerganov/whisper.cpp 下载 ggml-medium-q5_0.bin 放到 %USERPROFILE%\\models\\" "同 macOS 的 curl 命令" "放在任意位置后 export WHISPER_MODEL=模型路径"
else need "whisper-cli（whisper.cpp）" "逐段回听、逐字对齐" "brew install whisper-cpp" "github.com/ggerganov/whisper.cpp → Releases 下载 Windows 版" "git clone https://github.com/ggerganov/whisper.cpp && cd whisper.cpp && cmake -B build && cmake --build build -j" "源码编译，见 whisper.cpp README"; fi
echo
if [ $MISS = 0 ]; then echo "本机环境齐了，不用装任何东西。"; else echo "装好上面 ✗ 的项（任选一种方式），再跑一次 bash doctor.sh 确认。"; fi
exit $MISS
