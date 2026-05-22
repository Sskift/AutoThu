---
name: autothu-tool-thulearn-setup
description: 清华网络学堂 thulearn2018 安装、登录与会话配置
---

# thulearn2018 / 网络学堂配置

平台: https://learn.tsinghua.edu.cn

## Conda 环境

```bash
cd AutoThu
conda activate autothu
# 或: conda env create -f environment.yml
```

## 安装 thulearn2018

```bash
conda activate autothu
pip install thulearn2018
learn --help
```

Linux 若遇 `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`:

```bash
export OPENSSL_CONF="$HOME/.config/thulearn2018/openssl.conf"
# 首次运行 learn 会自动创建该配置目录
```

## 登录方式（按优先级）

### 1. Windows Edge + WSL（推荐）

WSL 无法直连 Windows Edge 的 CDP 端口，需在 **Windows 本机** 启动 Edge 并用 Windows Python 连接：

```bash
# 在 WSL 中执行（会弹出 Windows Edge 窗口）
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
  & 'C:\Users\lenovo\AppData\Local\Programs\Python\Python313\python.exe' \\
    '\\wsl.localhost\Ubuntu\home\lenovo\autoTHU\AutoThu\scripts\edge_login_winhost.py'
"

# 或先启动 Edge CDP 再登录（见 scripts/run_edge_login.ps1）
```

脚本会：
1. 启动 Edge（`--remote-debugging-port=9222`，独立用户目录 `%TEMP%\autothu-edge-cdp`）
2. 自动填写学号密码；**验证码/双因素请在 Edge 窗口手动完成**
3. 导出 `~/.config/autothu/session.json`（含 `all_cookies`）

验证：

```bash
conda activate autothu
python scripts/verify_learn.py --session ~/.config/autothu/session.json
```

### 2. 手动复制 Cookie

清华已禁用 thulearn2018 使用的旧版 `login/post` 直连。也可：

1. 浏览器打开 https://learn.tsinghua.edu.cn/f/login
2. 完成统一认证（含双因素/信任浏览器，若提示）
3. 登录成功后，从开发者工具复制 Cookie，保存为：

```json
// ~/.config/autothu/session.json
{
  "username": "学号",
  "cookies": {
    "JSESSIONID": "...",
    "XSRF-TOKEN": "..."
  }
}
```

验证：

```bash
conda activate autothu
python scripts/verify_learn.py --session ~/.config/autothu/session.json
```

Agent 任务中可用 `scripts/thu_learn_client.py` 的 `ThuLearnClient.from_session_file()`。

### 2. thulearn2018 交互配置

```bash
conda activate autothu
learn reset    # 写入 ~/.config/thulearn2018/user.txt 与 path.txt
learn config
```

若 `learn login` 失败并提示无 XSRF-TOKEN，改用方式 1。

### 3. SSO 表单 + SM2（高级）

- 表单 URL: `https://id.tsinghua.edu.cn/do/off/ui/auth/login/form/bb5df85216504820be7bba2b0ae1535b/0`
- 提交 URL: `https://id.tsinghua.edu.cn/do/off/ui/auth/login/check`
- 密码经页面 `#sm2publicKey` 做 SM2 加密后写入 `name=i_pass` 隐藏域
- 需 `fingerPrint` / `fingerGenPrint` 等字段（双因素信任设备）
- 成功后取得 ticket，再 `POST` `https://learn.tsinghua.edu.cn/b/j_spring_security_thauth_roaming_entry{ticket}`

参考: [learn2018-autodown](https://github.com/Trinkle23897/learn2018-autodown) 的 `login_manager.py`（Selenium 交互登录）。

## 常用 thu-learn 命令（替代 learn）

```bash
conda activate autothu
export PATH="/path/to/AutoThu/bin:$PATH"

thu-learn login      # Edge 登录
thu-learn verify
thu-learn ddl
thu-learn ddl -s 2025-2026-2
thu-learn download -o ./test
thu-learn download -i "操作系统"

# 提交（在 homework/某作业 目录下）
cd .../homework/某作业
thu-learn submit ./answer.pdf -m "说明"
```

完整说明见仓库根目录 `README.md`。

## 已验证 API 端点

| 用途 | URL |
|------|-----|
| 首页 / XSRF | `https://learn.tsinghua.edu.cn/` |
| 当前学期 | `.../b/kc/zhjw_v_code_xnxq/getCurrentAndNextSemester` |
| 课程列表 | `.../b/wlxt/kc/v_wlkc_xs_xkb_kcb_extend/student/loadCourseBySemesterId/{学期}/zh` |
| 作业列表 | `.../b/wlxt/kczy/zy/student/zyList{Yjwg\|Wj\|Ypg}?aoData=...` |
| 提交作业 | `.../b/wlxt/kczy/zy/student/tjzy` |

请求需带 Cookie `XSRF-TOKEN`，参数 `_csrf` 同值。

## 踩坑

- 直接 `curl` 未登录会 403
- 课程名含空格时，`learn download -i` 逗号分隔且**逗号后不要空格**
- 提交必须在下载生成的作业目录（含 `.xszyid`）
- WSL 无图形界面时，用本机浏览器登录后拷贝 `session.json` 到服务器
