---
name: autothu-task-do-homework
description: 完成清华网络学堂作业（解析→解答→渲染→确认→提交）
---

# 任务：完成作业并提交

## 前置

```bash
conda activate autothu
```

## 流程

```
Phase 1: PDF解析 → Phase 2: 解答 → Phase 3: 撰写 → Phase 4: 渲染 →
询问用户 → [确认] → Phase 5: learn submit
```

## 步骤

### 1. 用户确认（必须）

列出该课 `learn ddl` 或 `homework/` 下待交作业，用 `AskUserQuestion` 让用户选择具体一次作业。

二次确认后执行。**禁止**自动选最新作业。

### 2. 下载作业包

```bash
thu-learn download -i "课程名" -o ./test
# 需要已提交副本时: thu-learn download -i "课程名" --download-submission
```

作业目录示例：`test/{课程}/homework/{作业标题}/`，内含 README.md、题目 PDF、`.xszyid`（提交用）。

### 3. PDF 解析

引用 `tools/pdf-reader.md`，在 **conda activate autothu** 下运行 pdfplumber：

```python
# 输出 homework_parsed.json
```

约束：Parser Agent **禁止**直接读 PDF，须用 Python 提取。

### 4. 解答

Solver Agent 读取 `homework_parsed.json` 与 `file/`、`资料/`，输出 `answers.json`。

### 5. 写作类字数检查

Reflection、Essay 等须在渲染前用脚本统计英文字数/字数要求。

### 6. 渲染 PDF

```bash
conda activate autothu
pip show markdown  # 应已安装

# Markdown → HTML(MathJax) → Chrome headless PDF
# Linux: google-chrome --headless --print-to-pdf=...
# 或 pandoc: pandoc answer.md -o answer.pdf --pdf-engine=xelatex
```

### 7. 询问是否提交

```python
AskUserQuestion({
    "questions": [{
        "question": "是否提交到网络学堂？",
        "options": [
            {"label": "提交", "value": "submit"},
            {"label": "仅保存本地", "value": "save_only"}
        ]
    }]
})
```

### 8. 提交

进入含 `.xszyid` 的作业目录：

```bash
conda activate autothu
cd test/{课程}/homework/{作业目录}
thu-learn submit ./answer.pdf -m "AutoThu 提交"
```

## 输出

```
test/{课程}/homework/{作业}/
├── README.md
├── homework_parsed.json
├── answers.json
├── answer.md
└── answer.pdf
```
