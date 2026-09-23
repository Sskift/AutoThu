---
name: autothu
description: AutoThu - 自动同步清华网络学堂通知、完成作业、撰写笔记
---

# AutoThu

自动处理清华大学网络学堂（https://learn.tsinghua.edu.cn）相关任务。

## 环境准备

Linux/WSL 使用 Conda 环境 `autothu`；macOS 也可直接使用仓库 `.venv`（`bin/thu-learn` 会自动选择）。

```bash
cd AutoThu
conda env create -f environment.yml   # 首次
conda activate autothu
```

可选验证：

```bash
python scripts/verify_learn.py --doc-only
python scripts/verify_learn.py --session ~/.config/autothu/session.json
```

**macOS 登录**：运行 `thu-learn login`。命令会导入 Chrome 会话；无法导入时会打开独立 Chrome 登录窗口，手动完成认证后写入 session。

**WSL + Windows Edge 登录**（导出 session）：

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& 'C:/Users/lenovo/AppData/Local/Programs/Python/Python313/python.exe' '//wsl.localhost/Ubuntu/home/lenovo/autoTHU/AutoThu/scripts/edge_login_winhost.py'"
```

详见 `sub-skills/tools/thulearn-setup.md`。

## 配置说明

### Agent 全局配置（Claude Code）

**文件**: `~/.claude/settings.json`

```json
{
  "permissions": {
    "allow": ["Skill(update-config)", "Bash(*)"],
    "deny": ["Bash(rm:*)", "Bash(rm -rf:*)"],
    "defaultMode": "bypassPermissions"
  },
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
    "CONDA_DEFAULT_ENV": "autothu"
  }
}
```

执行 Bash 前先：`conda activate autothu`

### 网络学堂凭据

**禁止**在仓库中写入密码。任选其一：

| 方式 | 说明 |
|------|------|
| **session.json（推荐）** | 浏览器登录后导出 Cookie → `~/.config/autothu/session.json` |
| **thulearn2018** | `learn reset` → `~/.config/thulearn2018/user.txt`（旧版直连登录可能已失效） |
| **环境变量** | `THU_USER` / `THU_PASS`（仅本地测试） |

详见 `sub-skills/tools/thulearn-setup.md`。

## 使用方式

| 用户意图示例 | 任务 |
|-------------|------|
| "同步课程通知" / "看看有什么作业" | `tasks/sync-notices.md` |
| "完成某某课第五次作业" | `tasks/do-homework.md` |
| "给某课写笔记" | `tasks/write-notes.md` |

## 执行架构

### 1. 环境检测

与 AutoPku 相同，检测 Claude / Codex / Kimi / 串行：

```python
import os, shutil

if os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"):
    RUNTIME = "claude"
elif os.environ.get("CODEX") == "1":
    RUNTIME = "codex"
elif os.environ.get("KIMI_CODE_CLI") == "1" or shutil.which("kimi"):
    RUNTIME = "kimi"
else:
    RUNTIME = "serial"
```

### 2. 任务路由

```
用户意图 → sub-skills/tasks/<task>.md → runtime/create-agent.md 创建 Agent
```

### 3. 核心依赖

- **CLI**: `thu-learn`（`bin/thu-learn`，见 `README.md`）
- **库**: thulearn2018 + `scripts/thulearn_bridge.py`（session 注入）
- **PDF**: pdfplumber / PyMuPDF（`tools/pdf-reader.md`）

**禁止**调用 `learn download/ddl/submit`（`login()` 已失效）；统一使用 `thu-learn`。

## 登录验证结论（实探测）

| 方式 | 状态 |
|------|------|
| `POST .../login/post/...`（thulearn2018 旧版） | ❌ 「该应用不允许调用登录接口」 |
| `GET .../login/form/...` + SM2 `login/check` | ⚠️ 需正确 SM2 与信任浏览器/双因素 |
| 浏览器登录 + Cookie session | ✅ 推荐，用于后续 API |

## Task / Tool / Runtime 索引

| 类型 | 文件 |
|------|------|
| 同步通知 | `tasks/sync-notices.md` |
| 完成作业 | `tasks/do-homework.md` |
| 撰写笔记 | `tasks/write-notes.md` |
| thulearn 配置 | `tools/thulearn-setup.md` |
| 数据解析 | `tools/data-parser.md` |
| PDF | `tools/pdf-reader.md` |
| Agent 模板 | `tools/agent-helpers.md` |
| 环境检测 | `runtime/_detect.md` |
| 创建 Agent | `runtime/create-agent.md` |
| Claude/Codex/Kimi | `runtime/*-team.md` |

## 安全规则

- 不回显密码
- 不自动选择作业、不未经确认提交
- `session.json` / `user.txt` 不得提交到 git

## 输出目录

默认工作根目录：`test/`（可在 `learn config` 或任务中覆盖）

```
test/
├── 通知摘要汇总.md
├── {课程名}/
│   ├── 作业/
│   ├── 通知/
│   ├── 资料/
│   └── 通知摘要.md
```
