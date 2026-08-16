# Beau Art Style Skills

一组用于“图片转艺术画风”的 Codex 技能：先生成可审看的预览，再根据自然语言反馈逐轮调整，直到定稿。

## 技能

- `beau-art-style-transfer`：将照片、截图或其他图片转换成水墨、油画、版画、插画等艺术画风；支持主体保真、可选风格参考图、去水印和画幅约束。
- `beau-art-style-transfer-evolver`：复盘生成结果，把可泛化的反馈整理成最小规则提案和回归用例；只有明确确认后才写回主技能。

## 使用方式

安装后，直接上传图片并说明目标画风，例如：

> 把这张照片转成水墨淡彩，保留主体，先给我看一张预览。

之后可以用自然语言继续反馈：

> 墨色再淡一点，但主体轮廓不要变。

## 安装

将 `dist/` 中对应的 `.skill` 文件安装到 Codex，或将同名技能目录放入 `$CODEX_HOME/skills/`。

## 目录

```text
beau-art-style-skills/
├── beau-art-style-transfer/
├── beau-art-style-transfer-evolver/
└── dist/
    ├── beau-art-style-transfer.skill
    └── beau-art-style-transfer-evolver.skill
```
