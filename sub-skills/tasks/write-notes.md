---
name: autothu-task-write-notes
description: 从网络学堂/本地课件撰写精简笔记
---

# 任务：撰写课程笔记

流程与 AutoPku 相同，差异：

- 课件来源：`test/{课程}/file/`（`learn download`）或用户指定 `lectures/`
- 输出：`notes/` + `pdf/{课程}课程笔记.pdf`
- 渲染：`pandoc` + `callout.lua`（见 AutoPku `write-notes.md` 的 PDF 渲染章节，可直接复用）

## 前置询问（必须）

使用 `AskUserQuestion` 询问：课件范围、详细程度、是否生成 Anki 等。

## Agent

- **Coordinator**：并行调度每份 PDF 的 Writer
- **Writer**：引用 `pdf-reader.md`，提取定义/定理/证明，去除轶事与废话

## Conda

```bash
conda activate autothu
pip install pymupdf pdfplumber  # 已在 environment.yml
```
