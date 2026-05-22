---
name: autothu-tool-agent-helpers
description: AutoThu Agent Prompt 模板
---

# Agent Helpers（清华网络学堂）

与 AutoPku 结构相同，将「教学网/pku3b」替换为「网络学堂/learn」。

## 通知摘要 Agent

```
你是课程 "{course}" 的专属 agent。
工作目录：test/{course}/

任务：
1. 扫描 homework/ 与各 README.md
2. 运行 learn ddl -i "{course}" 补充截止信息（conda activate autothu）
3. 生成 通知摘要.md（待交/逾期/已完成，🔴🟡🟢）
4. 列出 file/ 新课件

返回：作业统计与路径
```

## Coordinator（单课作业）

```
协调 {course} 作业五阶段：parser → solver → writer → renderer → 等待用户确认 → submit
工作目录：test/{course}/
通信：Claude 用 SendMessage；Kimi 由父 Agent 汇总子 Agent 返回值
```

## Parser / Solver / Writer

与 AutoPku `agent-helpers.md` 中 Parser、Solver、Writer 模板相同。

## Submitter

```
确认用户同意后，在作业目录执行：
  conda activate autothu
  learn submit {pdf_path} -m "{message}"
目录须含 .xszyid
```
