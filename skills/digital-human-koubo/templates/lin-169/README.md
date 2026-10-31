# lin-169 · 小林式解说模板（16:9）

起工程：`bash ~/.claude/skills/digital-human-koubo/scripts/new_edit.sh lin-169 <工程>`，流程见 `references/lin-style.md`。

- `src/Lin.tsx`：13 种场景（host / broll / board / rates / curve / fall / assume / formula / big / stickers / bars / formula2 / calc），字段写在每个组件上方的注释里
- `src/scenes.json`、`src/cues.json`：示例数据（72 法则，6 段约 36 秒，时间是手排的），换成本期 lin_scenes.py / lin_subs.py 的输出
- `plan.example.json` + `script.example.json`：示例分镜和对应的口播稿（时间写 `@s03:等于`），`scripts/lin_scenes.py` 把它转成 scenes.json
- `disp.example.txt`：显示稿示例（数字写成阿拉伯数字，断句和念稿一致）
- `public/`：main.mp4（拼好的口播）、mix.wav（lin_mix.py 出的混音）、broll/B01.mp4…、stickers/sticker_0.png…、cut/<段>.webm（景深字抠像）。素材不随模板带。

config（scenes.json 顶层）：`face` 主播脸中心（lin_scenes.py --face 自动量）、`audio` 音轨文件、`disclosure` 右上角 AI 标注（"" 关掉）、`brollTag` B-roll 角标、`colors` 改配色。
