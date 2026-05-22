# AutoThu

清华大学网络学堂（[learn.tsinghua.edu.cn](https://learn.tsinghua.edu.cn)）学业自动化 Skill，结构对标 [AutoPku](../AutoPku)。

**核心工具**：`thu-learn` CLI（用 `session.json` 驱动，不依赖已失效的 `learn login`）。

---

## 一、环境准备（首次）

### 1.1 创建 conda 环境

```bash
cd /home/lenovo/autoTHU/AutoThu
bash scripts/setup_conda.sh
```

或手动：

```bash
conda env create -f environment.yml
conda activate autothu
```

### 1.2 将 `thu-learn` 加入 PATH（推荐）

```bash
# 写入 ~/.bashrc 或每次手动：
export PATH="/home/lenovo/autoTHU/AutoThu/bin:$PATH"
```

验证：

```bash
conda activate autothu
thu-learn --help
```

### 1.3 环境变量（可选）

| 变量 | 含义 | 默认值 |
|------|------|--------|
| `AUTOTHU_SESSION` | 登录会话文件 | `~/.config/autothu/session.json` |
| `AUTOTHU_WORK` | 课件/作业下载根目录 | `~/autoTHU/test` |
| `THU_USER` / `THU_PASS` | Edge 自动填表（勿提交 git） | 无 |

---

## 二、登录（必做，WSL + Windows Edge）

清华已关闭 thulearn2018 的旧版 `login/post` 接口，**不能**再使用 `learn download` 等自带登录。请用 AutoThu 登录流程导出 `session.json`。

### 2.1 一键登录（推荐）

在 WSL 中执行（会弹出 **Windows Edge**；双因素/验证码在窗口内手动完成）：

```bash
conda activate autothu
thu-learn login
```

等价于：

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\lenovo\autoTHU\run_edge_login.ps1"
```

或：

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& 'C:\Users\lenovo\AppData\Local\Programs\Python\Python313\python.exe' '\\wsl.localhost\Ubuntu\home\lenovo\autoTHU\AutoThu\scripts\edge_login_winhost.py'"
```

成功后生成：`~/.config/autothu/session.json`

### 2.2 验证登录

```bash
thu-learn verify
```

期望输出：`OK 学期=2025-2026-2 课程数=N` 及课程列表。

底层亦可：

```bash
python scripts/verify_learn.py --session ~/.config/autothu/session.json
```

### 2.3 手动导出 Cookie（无 Edge 脚本时）

1. 浏览器打开 https://learn.tsinghua.edu.cn/f/login 并登录  
2. 复制 `JSESSIONID`、`XSRF-TOKEN`（域名 `learn.tsinghua.edu.cn`）  
3. 写入 `~/.config/autothu/session.json`：

```json
{
  "username": "你的学号",
  "cookies": {
    "JSESSIONID": "...",
    "XSRF-TOKEN": "..."
  }
}
```

### 2.4 session 过期

症状：`thu-learn verify` 失败，或 API 返回跳转登录页。  
处理：重新执行 `thu-learn login`。

---

## 三、`thu-learn` 命令大全

所有命令默认读取 `~/.config/autothu/session.json`，下载目录默认 `~/autoTHU/test`。可用全局选项覆盖：

```bash
thu-learn --session /path/to/session.json --work-dir ./my_test <子命令>
```

| 命令 | 作用 | 说明 |
|------|------|------|
| `thu-learn login` | Edge 登录并导出 session | 仅 WSL+Windows |
| `thu-learn verify` | 验证 session / 列出课程 | 推荐每次登录后执行 |
| `thu-learn config` | 显示 session、工作目录路径 | |
| `thu-learn courses` | 列出当前学期课程 | `-s 2025-2026-2` 指定学期 |
| `thu-learn ddl` | 未过期作业截止 + 生成 homework 目录 | 会下载作业元数据 |
| `thu-learn download` | 下载课件与作业附件 | 主力同步命令 |
| `thu-learn submit FILE` | 提交作业 PDF | 须在含 `.xszyid` 的目录下 |

### 3.1 列出课程

```bash
thu-learn courses
thu-learn courses -s 2025-2026-2
```

### 3.2 查看作业截止

```bash
thu-learn ddl
thu-learn ddl -i "操作系统,数值分析"
thu-learn ddl -e "射击,滑冰"
```

说明：`-i` / `-e` 逗号分隔课程名，**逗号后不要空格**。

### 3.3 下载课件与作业

```bash
# 当前学期全部课程 → ~/autoTHU/test/{课程名}/
thu-learn download

# 指定目录
thu-learn -o ./test download

# 只下载部分课
thu-learn download -i "操作系统,计算机系统结构"

# 同时拉取你已提交的作业副本（慎用，会覆盖本地）
thu-learn download --download-submission
```

目录结构（与 thulearn2018 一致）：

```
test/
├── 操作系统/
│   ├── file/           # 课件
│   └── homework/       # 作业（含 README.md、.xszyid、附件 PDF）
├── 数值分析/
│   └── ...
```

### 3.4 提交作业

```bash
cd ~/autoTHU/test/操作系统/homework/第五次作业
thu-learn submit ./answer.pdf -m "说明文字"
# 仅文字、无附件：
thu-learn submit -m "说明"
```

必须在含有 `.xszyid` 的作业目录下执行（`download` 会自动生成）。

---

## 四、交给 Agent（Skill）

### 4.1 启动方式

对 Claude Code / Codex / Kimi 说：

```
conda activate autothu，执行 AutoThu/skill.md
```

或：

```
下载本仓库，PATH 加入 AutoThu/bin，先 thu-learn verify，再按 skill 执行任务
```

### 4.2 自然语言示例

| 你说的话 | Agent 应执行 |
|----------|----------------|
| 同步这周网络学堂通知 | `thu-learn download` + 并行生成各课 `通知摘要.md` |
| 看看有什么作业 | `thu-learn ddl` |
| 完成操作系统第五次作业 | 下载 → 解析 PDF → 解答 → 渲染 → **问你确认** → `thu-learn submit` |
| 给操作系统写笔记 | 基于 `file/` 课件撰写笔记并 pandoc 渲染 |

任务细节见 `sub-skills/tasks/*.md`。

### 4.3 Agent 配置（Claude Code 可选）

`~/.claude/settings.json`：

```json
{
  "permissions": {
    "allow": ["Skill(update-config)", "Bash(*)"],
    "deny": ["Bash(rm:*)", "Bash(rm -rf:*)"],
    "defaultMode": "bypassPermissions"
  },
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

执行 Bash 前先：`conda activate autothu`

---

## 五、辅助脚本（开发/调试）

| 脚本 | 用途 |
|------|------|
| `scripts/setup_conda.sh` | 创建 conda 环境 `autothu` |
| `scripts/thu_learn_cli.py` | `thu-learn` 的实现 |
| `scripts/thulearn_bridge.py` | session 注入 thulearn2018 |
| `scripts/thu_learn_client.py` | 纯 HTTP 客户端（课程 API） |
| `scripts/verify_learn.py` | 验证 session / 打印 API 端点 |
| `scripts/edge_login_winhost.py` | Windows 侧 Edge CDP 登录 |
| `scripts/run_edge_login.ps1` | 启动 Edge + 登录（Windows） |
| `scripts/probe_login.py` | SSO 登录链探测 |

---

## 六、目录结构

```
AutoThu/
├── README.md              # 本文档（使用说明）
├── skill.md               # Agent 主入口
├── environment.yml        # conda: autothu
├── bin/thu-learn          # CLI 包装脚本
├── scripts/               # Python / PowerShell 工具
└── sub-skills/
    ├── tasks/             # sync-notices, do-homework, write-notes
    ├── tools/             # thulearn-setup, pdf-reader, ...
    └── runtime/           # Claude/Codex/Kimi Agent 适配
```

---

## 七、与旧版 `learn` 命令的关系

| 旧命令（thulearn2018） | AutoThu 替代 |
|------------------------|--------------|
| `learn reset` | 凭据仍可用于 Edge 填表；登录用 `thu-learn login` |
| `learn config` | `thu-learn config` |
| `learn ddl` | `thu-learn ddl` |
| `learn download` | `thu-learn download` |
| `learn submit` | `thu-learn submit` |

**不要**再依赖 `learn login()`，会失败。

---

## 八、技术说明

| 项目 | 结论 |
|------|------|
| 平台 | https://learn.tsinghua.edu.cn |
| 旧 SSO POST | 已禁用 |
| 登录 | Windows Edge + CDP → `session.json` |
| API | 与 [thulearn2018](https://github.com/euxcet/thulearn2018) 一致，需 `XSRF-TOKEN` + `JSESSIONID` |
| WSL 访问 Edge CDP | 不可直连 `127.0.0.1:9222`，须 Windows Python 控制 |

---

## 九、安全

- **禁止**将密码、`session.json` 提交到 git（已写入 `.gitignore`）
- 作业提交前 Agent **必须**经你二次确认
- 禁止自动选择「最新一次」作业

---

## 十、常见问题

**Q: `thu-learn verify` 失败？**  
A: 运行 `thu-learn login`，在 Edge 中完成双因素。

**Q: WSL 里 `learn download` 报错 XSRF-TOKEN？**  
A: 改用 `thu-learn download`。

**Q: 下载路径想改？**  
A: `thu-learn -o /你的路径 download`，或 `export AUTOTHU_WORK=/你的路径`。

**Q: 如何只同步一门课？**  
A: `thu-learn download -i "操作系统"`。

**Q: Edge 脚本在哪？**  
A: `scripts/edge_login_winhost.py`，Windows 副本 `C:\Users\lenovo\autoTHU\run_edge_login.ps1`。

---

## License

MIT
