<div align="center">

# Digital Human Koubo · AI 数字人口播

**一张照片 + 一句话 → 一条带数字人出镜的口播成片。**
写稿、对口型的 AI 主播、修音、字幕、头部博主级包装，全部交给你的 AI Agent 自动完成。

[English](README.md) · **简体中文**

[![License: MIT](https://img.shields.io/badge/license-MIT-black.svg)](LICENSE)
![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-orange)
[![Renoise MCP](https://img.shields.io/badge/video-Renoise%20MCP-ff7a1a)](https://renoise.ai/mcp?utm_medium=xcom&utm_source=official)
![Remotion](https://img.shields.io/badge/edit-Remotion%204-0b84f3)

<img src="docs/images/cover.jpg" width="820" alt="一张照片 + 一句话，27 秒直播带货广告">

</div>

> 这条 27 秒的直播间广告里，主播不存在。脸、声音、直播间、花字、价格动画，全是 AI 做的。
> 输入只有一句话：「用这个数字人做一条 30 秒直播间广告，卖 WorkBuddy 上手课，10 节课 99 元，原价 999。」
> 总共花了 **482 [Renoise](https://renoise.ai/mcp?utm_medium=xcom&utm_source=official) 积分**。

---

## 示例

点 GIF 或「播放」看完整视频。下面每一条都是用这个仓库做出来的。

| | | |
|:---:|:---:|:---:|
| <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/workbuddy-live-ad.mp4"><img src="docs/gifs/workbuddy-live-ad.gif" width="230"></a> | <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/renoise-koubo-huazi.mp4"><img src="docs/gifs/renoise-koubo-huazi.gif" width="230"></a> | <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/text-behind.mp4"><img src="docs/gifs/text-behind.gif" width="300"></a> |
| **直播间带货广告** · 9:16 · 27 秒<br>风格 B + 景深价格 ¥999→¥99<br>[▶ 播放](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/workbuddy-live-ad.mp4) | **产品推荐口播** · 9:16 · 89 秒<br>花字、动态表情、画中画<br>[▶ 播放](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/renoise-koubo-huazi.mp4) | **文字在人身后（景深字）** · 5 秒<br>Vision 人像抠图，三层合成<br>[▶ 播放](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/text-behind.mp4) |

| | |
|:---:|:---:|
| <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/tutorial-ep2.mp4"><img src="docs/gifs/tutorial-ep2.gif" width="400"></a> | <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/tutorial-digital-human-upgrade.mp4"><img src="docs/gifs/tutorial-digital-human-upgrade.gif" width="400"></a> |
| **保姆级教程** · 16:9 · 4 分 36 秒<br>数字人亲自讲「我是怎么被做出来的」（风格 D）<br>[▶ 播放](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/tutorial-ep2.mp4) | **数字人升级版** · 16:9 · 5 分 55 秒<br>两位主播、六种语言、四个场景、猫狗角色（风格 E）<br>[▶ 播放](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/tutorial-digital-human-upgrade.mp4) |
| <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/memt-launch.mp4"><img src="docs/gifs/memt-launch.gif" width="400"></a> | <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/xiaolin-style-explainer.mp4"><img src="docs/gifs/xiaolin-style-explainer.gif" width="400"></a> |
| **发布解读** · 16:9 · 39 秒<br>主播在侧边，右侧代码动效（风格 C）<br>[▶ 播放](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/memt-launch.mp4) | **财经 / 科技解说** · 16:9 · 2 分 21 秒<br>图表、文件标黄、章节卡（风格 A）<br>[▶ 播放](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/xiaolin-style-explainer.mp4) |

<div align="center">
<a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/packaging-gallery.mp4"><img src="docs/gifs/packaging-gallery.gif" width="560"></a><br>
<b>包装组件图鉴</b> · 48 个组件 · 2 分 40 秒 · <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/packaging-gallery.mp4">▶ 播放</a>
</div>

> 示例里的主播全部是 AI 数字人，每条片子都标了「内容由 AI 数字人演绎」。男主播是作者用本人照片做的数字分身。

---

## 能做什么

- **一张照片做出固定的数字人**：脸、服装、声音描述、提示词模板都存在 `persona.json`，每条片子都是同一个人。想进什么场景（直播间、门店、教室、京都街头），先用 GPT Image 合成开场画面，再让她开口。
- **对口型的口播片段**：稿子切成 ≤ 15 秒一段，通过 **[Renoise MCP](https://renoise.ai/mcp?utm_medium=xcom&utm_source=official)** 用 **Grok Video 1.5** 生成。也写了 Wan 3.0、OmniHuman（用你自己的录音驱动口型）的用法。
- **先报价，再花钱**：每次生成前，Agent 先报「段数 · 秒数 · 积分 · 余额」，你点头才开始；先拍第 1 段给你看，满意再批量。
- **两道质检**：每段用 whisper 回听、和稿子比对；每段抽 4 帧检查（Grok 偶尔会自己往画面里烧字幕，有就重拍那段）。
- **声音统一**：1/3 倍频程频谱匹配 + 去齿音 + 同一个小房间混响 + 响度统一，30 段分开生成的口播听起来像一次录完（实测齿音段间差 13.2 dB → 5.9 dB）。
- **按内容推荐剪辑风格**：Agent 先诊断内容，推荐 2 种风格并附预览图，一次问完（风格 · 比例时长 · 花字强度 · 主播）。
- **48 个包装组件**：逐帧拆了 25 支头部博主视频（MrBeast、Mark Rober、Ryan Trahan、MKBHD、影视飓风、何同学、Johnny Harris、Vox、Kurzgesagt、回形针、半佛仙人、差评、毕导）。每种风格自带默认包装，想加减直接说。
- **景深字**：大字 / 数字放在背景和人之间（macOS Vision 人像分割 → 透明视频 → 三层合成）。
- **封面即首帧**：每条片子默认出封面（16:9 / 9:16 / 3:4：主播帧 + 钩子大字 + 证据卡），并接成成片第一帧停 0.5 秒。平台默认拿首帧当封面，不用再单独上传。
- **多语言**：英、日、韩、法、西、阿拉伯语实测，whisper 回听准确率 94–100%。
- **多种 Agent 都能用**：标准 `SKILL.md` Agent Skill + 脚本，只要能装 Skill、能接远程 MCP、能在本机跑命令，就能驱动整条流程。

## 工作流程

```
你的内容 ──► 0. 环境检查（Renoise MCP / ffmpeg / whisper，已经有的直接跳过）
              1. 诊断内容 → 5 种风格里推荐 2 种 → 一次问完 → brief.json
              2. 写稿 script.json（每段 ≤15 秒，中文约 5.4 字/秒）
              3. 报价 → 等你确认 → 先拍第 1 段 → 你看过 → 批量
              4. 分片下载（防 CDN 截断）→ whisper 回听 → 抽帧检查
              5. 声音统一（频谱匹配 + 去齿音 + 同一房间混响）
              6. 逐字时间轴（tl.json）
              7. Remotion 剪辑：风格模板 + 默认包装（+ 你点名的手法）
              8. 渲染 → 看过渡中间帧 → 响度（-14 / -16 LUFS）
              9. 封面：挑主播帧 → 16:9 / 9:16 / 3:4 → 接成首帧（停 0.5 秒）
```

<p align="center"><img src="docs/images/ad-breakdown.jpg" width="820" alt="直播间广告 5 段，每段用的包装"></p>

---

## 支持哪些 Agent

这个 Skill 是一个带 `SKILL.md`（开放的 Agent Skills 格式）的文件夹，加上 Python / Shell / Remotion 脚本。要跑通**完整**流程，Agent 需要三样能力：

1. **能装 Agent Skills**（技能目录或上传技能包）；
2. **能接远程 MCP 服务器**（Renoise：Streamable HTTP，浏览器登录授权，不用复制 API key）；
3. **能在你电脑上执行命令**（ffmpeg、Python、Node，用来下载、质检、剪辑）。

| Agent | 装 Skill | 接 Renoise MCP | 本机执行命令 | 状态 |
|---|---|---|---|---|
| **Claude Code** | `~/.claude/skills/` | `/plugin`（见下文） | ✅ | ✅ 已实测，这个仓库就是用它做的 |
| **Codex**（CLI / 桌面） | `~/.codex/skills/` | `codex mcp add` | ✅ | ✅ 预期可用（同一套脚本） |
| **OpenClaw** | 放进 OpenClaw 的技能目录（见其文档） | `openclaw plugins install` | ✅ | ⚙️ 应可用 |
| **WorkBuddy** | 技能 → 导入文件夹 / 压缩包 | 连接器 → 添加自定义 MCP | ✅ 桌面端 Agent | ⚙️ 应可用，菜单名以 App 当前版本为准 |
| **豆包** · **千问办公** · **纳米Work** 等 Agent 产品 | 产品支持 Agent Skills 就导入 | 支持自定义 / 远程 MCP 就添加 | 剪辑需要 | ⚙️ 满足上面三样能力即可，具体入口以各产品文档为准 |
| **Claude 桌面端 / claude.ai** | 设置里上传技能包 | 连接器 → Add custom connector | ⚠️ 只有沙盒 | 写稿、设计场景、报价、生成都能做；本机剪辑需要能跑命令的 Agent |

> 如果你的 Agent 只能「MCP + 聊天」、不能跑本机命令，也可以先用它**写稿、报价、生成**片段；剪辑这几步再交给 Claude Code / Codex，或者照 [`SKILL.md`](skills/digital-human-koubo/SKILL.md) 里的命令手动跑。

---

## 安装

### 1 · 下载代码

```bash
git clone https://github.com/andyhuo520/digital-human-koubo.git
cd digital-human-koubo
```

### 2 · 把两个 Skill 装进你的 Agent

仓库里有两个 Skill：`digital-human-koubo`（主 Skill）和 `finance-explainer`（风格 A「财经 / 科技解说」的引擎）。

**Claude Code**
```bash
mkdir -p ~/.claude/skills && cp -R skills/digital-human-koubo skills/finance-explainer ~/.claude/skills/
```
**Codex**
```bash
mkdir -p ~/.codex/skills && cp -R skills/digital-human-koubo skills/finance-explainer ~/.codex/skills/
```
**WorkBuddy / OpenClaw / 其他 Agent**：把两个文件夹打成压缩包，在产品的「技能」页面导入，或者复制进它的技能目录（以产品文档为准）：
```bash
cd skills && zip -r ../digital-human-skills.zip digital-human-koubo finance-explainer && cd ..
```

### 3 · 接入 Renoise MCP（AI 视频 / 图片生成）

先去 **[renoise.ai](https://renoise.ai/mcp?utm_medium=xcom&utm_source=official)** 注册账号。登录都在浏览器里完成，不用复制任何 API key。

| Agent | 怎么接 |
|---|---|
| Claude Code | `/plugin marketplace add ArcoCodes/renoise-plugins-official`，再 `/plugin install renoise@renoise-plugins-official` |
| Codex | `codex mcp add renoise --url https://renoise.ai/api/public/mcp`，再 `codex mcp login renoise` |
| OpenClaw | `openclaw plugins install renoise --marketplace ArcoCodes/renoise-plugins-official` |
| Claude 桌面端 / claude.ai | 设置 → 连接器 → **Add custom connector** → 名称 `Renoise`，地址 `https://renoise.ai/api/public/mcp` |
| WorkBuddy、Cursor、Windsurf、Cline、豆包、千问、纳米Work…… | 添加远程 MCP 服务器，地址 `https://renoise.ai/api/public/mcp`（常见配置：`{"mcpServers":{"renoise":{"url":"https://renoise.ai/api/public/mcp"}}}`） |

官方最新装法：**[renoise.ai/plugin](https://renoise.ai/plugin)**。装好后问 Agent 一句「查一下我的 Renoise 余额」，能查到就连上了。

### 4 · 本机工具（下载、质检、剪辑要用）

| 工具 | macOS | Windows | Linux |
|---|---|---|---|
| ffmpeg | `brew install ffmpeg` | `winget install Gyan.FFmpeg` | `sudo apt install ffmpeg` |
| Python 3 + numpy + Pillow | `brew install python` 后 `python3 -m pip install numpy pillow` | `winget install Python.Python.3.12` | `sudo apt install python3-pip` |
| Playwright + Chromium（封面排版） | `python3 -m pip install playwright && python3 -m playwright install chromium` | 同左 | 同左 |
| Node.js 18+（Remotion） | `brew install node` | `winget install OpenJS.NodeJS.LTS` | `nvm install --lts` |
| whisper.cpp（`whisper-cli`） | `brew install whisper-cpp` | [Releases 下载](https://github.com/ggerganov/whisper.cpp/releases) | [源码编译](https://github.com/ggerganov/whisper.cpp) |
| whisper 模型 | 下载 [`ggml-medium-q5_0.bin`](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium-q5_0.bin) 放到 `~/models/`（或 `export WHISPER_MODEL=模型路径`） | 同左 | 同左 |

一条命令检查：已经装好的打勾跳过，缺什么列出多种装法：
```bash
bash ~/.claude/skills/digital-human-koubo/scripts/doctor.sh
```

**景深字**（文字在人身后）用的是 Apple Vision，需要 **macOS**；其余功能跨平台。

### 5 · 音效与占位配乐

仓库**不带任何第三方音频**。用代码合成一套原创音效（30 个）和一条占位配乐（无版权）：
```bash
python3 ~/.claude/skills/digital-human-koubo/scripts/make_assets.py
```
`new_edit.sh` 每次起新工程也会自动跑。想要更好的配乐，把你有授权的曲子放到 `<工程>/public/music/bgm.mp3` 覆盖即可。

### 6 ·（可选）小米 MiMo 语音：音色设计 / 声音克隆

默认用 Grok 自带的声音（口型最准）。想要设计一个新音色、用你自己的克隆声音，或者做纯旁白视频，Skill 会调用 **小米 MiMo TTS**：

1. 去 **[platform.xiaomimimo.com](https://platform.xiaomimimo.com/)** 注册并创建 API Key。写这份文档时小米的 TTS 模型是限时免费的，具体以官网当前价格为准。
2. 把 Key 放进环境变量，或写到 `~/.config/ai-teardown/mimo.env`：
   ```bash
   mkdir -p ~/.config/ai-teardown && cat > ~/.config/ai-teardown/mimo.env <<'EOF'
   MIMO_API_KEY=你的key
   MIMO_BASE_URL=https://api.xiaomimimo.com/v1
   EOF
   chmod 600 ~/.config/ai-teardown/mimo.env
   ```
3. 只克隆**你本人**的声音，或明确授权给你的声音。

> 注意：Grok 的口型跟的是它自己生成的声音。事后换成别的声音，口型会差约 100 毫秒（画中画看不出，全屏特写看得出）。想用自己的录音又要口型准，换「音频驱动口型」的模型，比如 OmniHuman（Skill 里有写法）。

---

## 快速开始

直接用大白话跟 Agent 说：

```text
用我的数字人 Skill 讲这段：……（粘贴你的内容）
用这个数字人做一条 30 秒直播间广告：WorkBuddy 上手课，10 节课 99 元，原价 999。
做一条 3 分钟的小林式解说：硅谷银行为什么会暴雷。
讲到这几个国家的时候加地图航线 / 把「¥99」放在她身后 / 开场加个预告闪回。
把包装组件图鉴发我看看
```

接下来会发生：
1. 环境检查：已经装好的直接跳过。
2. 一行诊断 + 推荐 2 种风格（附预览图），一次问完。
3. 稿子 + 场景设计 + **积分报价** → 你确认 → 先拍第 1 段 → 你确认 → 批量。
4. 质检、修音，按风格默认包装剪辑 → 出成片 MP4。

---

## 做你自己的数字人

1. 选一张照片：正脸、光线均匀、头发不挡脸、嘴闭着。**只用你本人或明确授权的照片。**
2. 让 Agent 生成四视图（正面、两个侧面、背面）：GPT Image 2.5，2k，约 23 积分，保证换角度不变脸。
3. 同一张图、同一句台词做多模型对比（Grok Video 1.5 vs Wan 3.0，各 8 秒），选一个。
4. 把参考图上传到 Renoise，把 `material:<id>` 写进 `skills/digital-human-koubo/persona.json`（`renoise.reference_material`；第二位主播写在 `other_hosts.me`）。

详细步骤见 [`references/new-avatar.md`](skills/digital-human-koubo/references/new-avatar.md)。仓库里的 `material:` ID 属于作者的账号，你的账号用不了，这是正常的。

<p align="center"><img src="docs/images/scene-composite.jpg" width="720" alt="参考照 → 合成直播间"></p>

---

## 五种剪辑风格

<p align="center"><img src="docs/images/five-styles.jpg" width="820" alt="五种剪辑风格"></p>

| 风格 | 比例 | 时长 | 适合 | 模板 |
|---|---|---|---|---|
| **A** 小林式解说（财经 / 科技事件） | 16:9 | 3–20 分钟 | 事件、数据、「为什么」 | `finance-explainer` 引擎 |
| **B** 网红花字口播 | 9:16 | 30–120 秒 | 安利、带货、种草、吐槽 | `templates/huazi-916`（数据驱动） |
| **C** 发布解读 | 16:9 | 30–90 秒 | 新品、新模型发布 | `templates/reference/launch-169` |
| **D** 保姆级教程 | 16:9 | 3–8 分钟 | 几步做出 XX、工具上手 | `templates/reference/tutorial-169` |
| **E** 多主播 · 多语言 · 多场景 | 16:9 | 3–7 分钟 | 能力展示、出海 | `templates/reference/multihost-169` |

风格 B 有三档花字强度：**克制 / 标准 / 热闹**。

<p align="center"><img src="docs/images/huazi-presets.jpg" width="820" alt="三档花字强度"></p>

风格 A 只学解说频道的**结构和剪辑语法**，不用真实创作者的脸、声音、布景和原话。

---

## 48 个包装组件

逐帧拆了 25 支视频（镜头切分、开场逐拍、屏幕文字、声音），完整报告在 [`references/research/`](skills/digital-human-koubo/references/research/)。

<p align="center"><img src="docs/images/creator-pacing.jpg" width="720" alt="25 支头部博主视频每分钟切数"></p>

**从研究里提炼的规则**（[`packaging-playbook.md`](skills/digital-human-koubo/references/packaging-playbook.md)）：
- 切数可以低，刺激不能断：前 30 秒每 3–5 秒要有一个新东西出现。
- 前 3 秒直接给命题或动作，不问好、不放 Logo。
- BGM 从头铺到尾；音效只给事件（中文口播头部每分钟 1–3 个）；揭晓前刻意静音 0.6–1.0 秒。
- 单机位数字人最便宜的节奏来源：按句子边界跳切推近（1.0× / 1.18× / 1.32×）。

<p align="center"><img src="docs/images/packaging-gallery.jpg" width="820" alt="包装组件图鉴"></p>

| 分组 | 组件 |
|---|---|
| 开场 / 钩子 | TeaserColdOpen 预告闪回 · ColdOpenFreeze 定格片名卡 · SearchTyping 搜索框打字 · NumberSpike 数字钉子 · SlamText 砸字 · WordStack 逐词堆叠 · TornStrip 撕纸标题 · **TextBehind 景深字** |
| 证据 / 数据 | EvidenceCard 证据截图 · DocFocus 文档聚焦 · SourceDoc 官方文档 · ZoomFocus 截图聚焦 · Counter 数字滚动 · Odometer 里程表 · GlassPanel 玻璃面板 · SpecCard 参数卡 · LineDraw 折线图 · BarCompare 对比条 · ReviewCards 评论卡 · ArchiveCards 档案卡 · MapRoute 地图航线 · CompareWipe 前后对比 · PaperCollage 纸张拼贴 |
| 标注 / 人物 | HandDraw 手绘圈注 · CalloutPill 指针胶囊 · LeaderLabel 引线标注 · TypedNameTag 打字名牌 · LowerThird 人名条 · NamePlate 名牌语录 · SourceTag 出处角标 · FreezeFrame 定格「等等！」 |
| 节奏 / 互动 | PunchInHost 跳切推近 · KeywordStack 关键词三连 · RetentionCaption 留存大字幕 · TiltLine 倾斜金句 · Aside 括号旁白 · Danmaku 弹幕 · ReactionPop 反应贴纸 · MemeWindow 梗图窗 · PollPop 投票 · GlitchInterstitial 故障插屏 · HostFloaters 悬浮窗 · ProgressChapters 进度条 · ProgressTracker 步骤追踪 · ChapterCard 章节卡 · RecapBoard 复盘板 · Countdown 倒计时 · GhostWord 鬼影大字 |

每个组件都在 `pack` 列表里按名字调用，时间写成「段:词」（如 `"3:积分"`），9:16 自动适配：

```json
"pack": [
  { "use": "NumberSpike", "at": "1:不到十块钱", "until": "1:end", "text": "¥9.9/节", "label": "一节课" },
  { "use": "Danmaku", "items": [{ "t": "真的假的？", "at": "1:" }, { "t": "AI 还能帮我干活？", "at": "1:教你", "hot": true }] },
  { "use": "TextBehind", "src": "main.mp4", "cutout": "main_cut_s4.webm", "cutoutFrom": 17.2, "at": "4:", "until": "4:end",
    "mode": "count", "lines": [{ "t": "¥99", "font": "en", "color": "#FFE14D", "size": 0.17 }], "count": { "from": 999, "to": 99, "prefix": "¥" } }
]
```
参数说明：[`references/packaging.md`](skills/digital-human-koubo/references/packaging.md)。渲染前先检查：`python3 scripts/check_edit.py <工程>/src`。

### 景深字：文字在人身后

<p align="center"><img src="docs/images/text-behind-layers.jpg" width="760" alt="原视频 → Vision 遮罩 → 原视频 + 大字 + 人像"></p>

```bash
python3 scripts/cutout_video.py public/main.mp4 public/main_cut_s4.webm --from 17.2 --to 22.4   # 只抠用到的那几秒
```
适合**中景、头顶留白**的画面。自拍特写里人占了约 89% 的画面，字会被挡住，脚本在超过 60% 时会提醒。把这类段落标成 `"shot": "depth"`，生成时就会出中景。

<p align="center"><img src="docs/images/closeup-vs-medium.jpg" width="560" alt="特写 89% 挡字，中景 57% 露字"></p>

---

## 成本参考（真实跑过的数）

| 视频 | 生成内容 | 积分 |
|---|---|---|
| 直播间广告 9:16 27 秒 | 1 张场景图 + 5 段 Grok 口播（720p） | **482** |
| 教程第二期 16:9 4 分 36 秒 | 32 段口播（全屏 720p / 画中画 480p）+ 演示素材 | 约 3250 |
| 数字人升级版 16:9 5 分 55 秒 | 30 段新片段 + 7 张场景图，复用 17 段 | 约 3409 |

写文档时的价格：Grok Video 1.5 720p 17 积分/秒、480p 10 积分/秒；GPT Image 2.5 2k 23 积分/张。以 Agent 实时报价为准。

## 目录结构

```
skills/
  digital-human-koubo/            主 Skill
    SKILL.md                      Agent 照着执行的流程
    persona.json                  主播形象、声音描述、提示词模板
    references/                   风格菜单 · 包装组件 · 手法库 · 安装 · 拆解报告
    scripts/                      build_tasks · rangedl · assemble · align · check_edit · cutout_video
                                  voicefx/unify · doctor · new_edit · make_assets
                                  make_cover · cover_first（封面 + 首帧）
    templates/
      huazi-916/                  9:16 数据驱动花字口播模板（edit.json）
      packaging/                  48 个组件 + 图鉴工程
      reference/                  launch-169 · tutorial-169 · multihost-169
    assets/                       风格预览图 · 包装图鉴 · 数字人参考图
  finance-explainer/              风格 A 引擎（episode.json 拍表、检索工具）
docs/                             README 用的图片、GIF 预览、封面帧
```

## 踩过的坑（Skill 里都处理了）

- Grok 横屏口播偶尔**自己烧字幕**，提示词写了也挡不住 → 抽帧检查，重拍那段。
- whisper 会把中文数字写成阿拉伯数字（九百九十九 → 999），准确率会掉，但其实没念错 → 先听再决定重拍。
- Renoise 美国 CDN 并行下载会断成半截 → `rangedl.py` 6 段 Range 续传 + 解码校验。
- Grok 9:16 720p 是 **720×1280**，别拉成别的比例。
- expo 缓动到不了终点（99.9 四舍五入成 100）→ 计数动画结束时强制落在精确值。
- 主播视频轨一定要静音；两条声音差几毫秒叠在一起会刺耳（梳状滤波）。

## 使用红线

- 只用你本人或**明确授权**的脸和声音，不冒充任何真人或创作者。
- 每条片子标「内容由 AI 数字人演绎」，场景和动物片段标「AI 生成」。
- 不编数字、价格、优惠、评价；画面上的示意数据要标「示意」。
- 不用网络梗图、影视剧截图、明星照片；梗图类组件用你自己数字人生成的原创贴纸。
- 积分只在你确认报价之后才花。

## 许可与第三方

- 代码和文档：[MIT](LICENSE) © 2026 Berryxia（andyhuo520）。
- 渲染用的 **[Remotion](https://www.remotion.dev/)** 有自己的许可：个人和 3 人以内的公司免费，更大的公司需要购买[公司授权](https://www.remotion.pro/)。
- 动态表情：[Google Noto Emoji Animation](https://googlefonts.github.io/noto-emoji-animation/)（CC BY 4.0），视频里请署名「Animated emoji: Google Noto」。
- 地图：[world-atlas](https://github.com/topojson/world-atlas)（ISC，数据来自 Natural Earth，公有领域）、[d3-geo](https://github.com/d3/d3-geo)、[topojson-client](https://github.com/topojson/topojson-client)（ISC）。涉及中国边界的正式发布内容，请按国内相关规范另行核对。
- 语音识别：[whisper.cpp](https://github.com/ggerganov/whisper.cpp)（MIT）。生成走 [Renoise](https://renoise.ai/mcp?utm_medium=xcom&utm_source=official)（用你自己的账号和积分）；可选 TTS 用 [小米 MiMo](https://platform.xiaomimimo.com/)。
- WorkBuddy 示例里的课程截图来自作者自己的课程。示例视频是作者的作品，请不要当成自己的作品二次上传。

详见 [THIRD_PARTY.md](THIRD_PARTY.md)。

---

<div align="center">

作者 **Berryxia** · 用 Claude Code 做的 · 有帮助的话点个 ⭐，让更多人看到。

</div>
