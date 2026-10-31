# A · 小林式解说：剪辑手法与流水线

数据驱动的 Remotion 模板 `templates/lin-169`。第一次实战（2026-10）：一期个人理财讲解，44 段口播、5 分 50 秒、42 个场景。模板里的 `plan.example.json` 是一个 6 段的小示例。

**只学结构和剪辑手法**：不用真实创作者的脸、声音、布景、栏目名和原句（见 SKILL.md 红线）。参考片只用来拆节奏。

## 一、画面语法（从参考片逐帧拆出来的）

| 手法 | 什么时候用 | 模板里的场景类型 |
|---|---|---|
| 景深字：金色大字在主播身后 | 开场命题、关键数字、结尾金句。一期 3–4 次 | `host` + `depth` |
| 紫色题板 + 主播小窗 | 提问（「想一想」）、定义、假设、结论 | `board` |
| B-roll 实拍空镜 + 主播圆窗 + 数据卡 | 讲到生活场景、机构、行业时（超市、银行、医院、家庭） | `broll` + card / stat / chips / banner / doc / slam / float |
| 大数字卡 | 两三个利率、比例并排比 | `rates` |
| 先 ?% 后揭晓 | 「重要假设」：先挂问号，念到时翻牌 | `assume` |
| 推导逐行出现 | 列方程 | `formula` |
| 结论砸下 | 一个算式的结果（「72 ÷ 年化」→「≈ 12 年」） | `big` |
| 公式逐项长出 | 多项公式（A + B×C + D），当前讲的那项高亮，下挂 3D 图标 | `formula2`（`final:1` 全亮） |
| 算例填数 | 把例子的数字一个个填进公式，结果砸下 | `calc` |
| 条形图、瀑布图、曲线 | 地区对比、扣费、长期趋势（曲线标「示意」） | `bars` / `fall` / `curve` |
| 3D 贴纸四宫格 | 列出几大项（比如育儿 / 医疗 / 买房 / 养老） | `stickers` |

**节奏**（参考片实测，实战照做）：
- 画面每 6–9 秒换一次类型（主播 / 题板 / B-roll 交替）。
- 主播全屏累计不超过全片 20%（实战那期 71 秒 / 350 秒）。
- 每个数字出现时屏幕上必须有它。
- 题板和 B-roll 时主播一直在小窗里。小窗只有四个位置：`circle-tl` / `circle-bl` / `rect-l` / `rect-r`。`rect-r` 时面板自动靠左，不会被挡住（实战时踩过公式最后一项被盖住的坑）。

## 二、流水线（A 风格专用部分，其余同 SKILL.md）

1. **写稿**：同 SKILL.md 第 1 步。数字在稿子里写念法（「百分之二点五」），另写一份 `disp.txt` 显示稿（「2.5%」），每段一行，标点断句数要和念稿一样。
2. **拍 + 拼**：`build_tasks.py` → Grok → `assemble.py`。拼接已经保证音画等长，不用另外处理。
3. **查念错**：`python3 scripts/misread_check.py script.json`。按停顿切句，不带原文逐句转写。
   - 不能信 assemble.py 带原文提示的准确率：它会把念错的字「纠正」回去，比如「通胀」念成 tōng zhèng 照样判 100%。
   - 可疑字要让人听一下确认，同音字会误报。
4. **修念错（0 积分、保口型）**：`patch_words.py script.json patch.json --ref s05,s24,s41 --synth-only` → 填 m → 再跑 → `assemble.py --rejoin`。
   - 只把那一句换成 MiMo 克隆音，长度拉到和原句一样。
   - **不要整片换音色**：口型是跟 Grok 原声走的，整片换完到处对不上，用户一眼看出来。
   - **不要先提 OmniHuman 重做口型**：全片约 5,000 积分，用户明确说没必要。
5. **对齐**：`align.py` → `lin_subs.py script.json --disp disp.txt` → `src/cues.json`。
6. **分镜**：写 `plan.json`（格式见 lin_scenes.py 文件头，时间写「@s07:两千」），跑 `lin_scenes.py plan.json --tl src/tl.json --out src/scenes.json --face`。
   - `--face` 自动量主播脸中心，供小窗裁切用。
   - 报 GAP 就是场景没接上。
7. **素材**：
   - 景深字：`cutout_video.py cut/<段>.mp4 public/cut/<段>.webm`（Vision 抠像，本地）。
   - B-roll：放 `public/broll/B01.mp4…`。
   - 贴纸：放 `public/stickers/`。
8. **声音**：
   - 音效：`lin_sfx.py src/scenes.json --out audio`。
   - 混音：`lin_mix.py --voice cut/joined.mov --bgm 曲子 --sfx audio/sfx_bus.wav --out public/mix.wav`。
9. **渲染 + 导出**：
   - `npx remotion render src/index.ts Lin out/lin.mp4`。
   - 要 1.1 倍：`lin_mix.py ... --speed 1.1 --video out/lin.mp4 --final 成片_1.1x.mp4`（人声、音效、画面一起加速，BGM 原速）。
10. **质检**：
    - 每个场景抽开头 +0.15 秒和中点两帧拼图，看动画中途帧、小窗遮挡、空板。
    - `earshot timeline mix.wav --cues audio/cues_earshot.json` 看音效有没有被埋。
    - 成片和源片在开头、中段、结尾各取一处，对声音互相关、对画面帧匹配：声音 <10 ms、画面 ±1 帧。

## 三、B-roll（Renoise，花积分前先报价）

- **模型**：Wan 3.0，720p，5 秒，每段 60 积分（账户有限免活动时可能更少）。一期 10–12 段，约 720 积分。
- **提示词公式**：`Cinematic <镜头运动> of <具体场景+人物动作>, <光线>, shallow depth of field, documentary B-roll. No readable text, no logos, no watermark.`
  - 写中国场景（Chinese city street / red yuan banknotes）。
  - 人物写普通路人，不写名人。
- **角标**：画面角上自动加「AI 生成画面」（config.brollTag，设成 "" 可关）。
- **时长**：场景比 5 秒长时自动放慢到最低 0.55 倍，再加 1.02→1.12 慢推。场景超过 9 秒就拆成两个 B-roll 或插一块题板。
- **贴纸**：GPT Image 2.5 一张 2×2 四宫格（2k，23 积分），本地切成四张、从四角洪泛去掉白底，放 `public/stickers/sticker_0..3.png`。

## 四、声音

- **音效库**：earshot（可选，`EARSHOT_PY` 指向它的 python）；没装时 lin_sfx.py 用工程 `public/sfx`（make_assets.py 合成）兜底。
  - lin_sfx.py 首次会 `kit init --preset calm`，再把 drop 改成 cut_hit/punch（「碰」）、pop 改成 ui_pop/soft。
  - 规则表见脚本文件头。一期约 120 个音效。
- **音量**：要高出背景（人声 + 音乐）8–10 dB 才听得清。
  - 第一版只高 5 dB，用户说「碰」听不到。
  - 现在的档位：drop / bell +7 dB、pop / land +3 dB、whoosh −2 dB。
  - 复查用 `earshot timeline` 的 event_prominence_db。
- **BGM**：`earshot rank "<描述>" <曲库目录> --top 6` 挑曲。
  - 首次要拉模型，10 分钟以上，放后台跑。
  - 财经讲解选 light jazz / lo-fi（实战用的是 Mixkit「Upbeat Jazz」，免费可商用）。
  - 循环、sidechain 让人声、结尾淡出都由 lin_mix.py 做。
- **人声**：女声链 220 Hz +1.5 / 420 Hz −2 / 3.2 kHz +2 / 10 kHz +1.5 / 去齿音 / 3:1 压缩。总线 limiter，整片 −16 LUFS。

## 五、踩过的坑

- **拼接音画漂移**：44 段直接 `concat -c copy` 再解码音频，到 4:43 声音落后口型 0.38 秒（用户发现）。assemble.py 已修：每段音频 pad/trim 到画面帧长，keep 写真实画面长度。
- **带原文提示的转写会掩盖念错**：见第二节第 3 步。
- **只换两个字**：接缝处转写成别的词（「城镇」→「承认」）。换整句、切在停顿上才自然。
- **小窗挡内容**：`rect-r` 盖住公式最后一项。模板已让面板自动避开小窗。改布局后抽中点帧看一眼。
- **Remotion 循环里用 hook**：图表的每一行要单独拆成组件（FallBar / BarRow / Term），别在 map 里调 useK。
- **右上角 AI 标注**：默认显示「内容由 AI 数字人演绎」。用户要去掉时设 `config.disclosure: ""`，并提醒发布时在平台上勾选 AI 生成声明。
