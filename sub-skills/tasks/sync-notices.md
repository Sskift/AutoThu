---
name: autothu-task-sync-notices
description: 同步清华网络学堂课程通知与作业
---

# 任务：同步课程通知

## 前置

```bash
conda activate autothu
```

确认已登录（`session.json` 或 `learn` 可用）。见 `tools/thulearn-setup.md`。

## 执行步骤

### 1. 验证 session

```bash
conda activate autothu
thu-learn verify
```

### 2. 拉取作业截止与 homework 元数据

```bash
thu-learn ddl -o ./test
# 或只处理部分课: thu-learn ddl -i "操作系统,数值分析" -o ./test
```

### 3. 下载附件与课件

```bash
thu-learn download -o ./test
# 或: thu-learn download -i "操作系统" -o ./test
```

**不要**使用 `learn download`（内置 `login()` 已失效）。

按课程生成：

```
test/{课程名}/
├── file/          # 课件
├── homework/      # 作业（含 README.md 说明）
```

### 3. 并行 Agent 生成摘要

为每门课程创建 agent（引用 `runtime/create-agent.md`）：

```python
agent_configs = []
for course_name in course_dirs:
    agent_configs.append({
        "name": f"{course_name}-agent",
        "task": f"""
你是课程 "{course_name}" 的专属 agent。
工作目录：test/{course_name}/

任务：
1. 阅读 homework/ 下各作业 README.md
2. 统计待交/已交/逾期（解析截止日期 jzsjStr）
3. 生成 test/{course_name}/通知摘要.md
4. 紧急度：🔴 <1天 🟡 <7天 🟢 正常

返回：作业数、待交数、已下载文件列表
"""
    })
```

### 4. 汇总报告

写入 `test/通知摘要汇总.md`（全局统计 + 各课链接）。

## 输出

- `test/通知摘要汇总.md`
- `test/{课程}/通知摘要.md`
- `test/{课程}/homework/`、`file/`
