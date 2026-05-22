---
name: autothu-tool-data-parser
description: 解析 learn ddl 输出与 homework README
---

# 网络学堂数据解析

## 解析 learn ddl 文本输出

`learn ddl` 典型列：课程名、作业标题、截止时间、说明。

```python
import re
from datetime import datetime

def parse_ddl_lines(text: str) -> list[dict]:
    """按行解析 learn ddl 表格输出（去除 ANSI）。"""
    rows = []
    for line in text.splitlines():
        line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
        if not line or line.startswith("-"):
            continue
        # 宽松匹配：课程 | 作业 | 日期时间
        m = re.match(r"^(.+?)\s{2,}(.+?)\s{2,}(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", line)
        if m:
            rows.append({
                "course": m.group(1).strip(),
                "assignment": m.group(2).strip(),
                "deadline": m.group(3).strip(),
            })
    return rows
```

## 解析 homework/README.md

thulearn2018 为每份作业生成 `homework/{标题}/README.md`，含截止日期、说明、附件列表。

```python
from pathlib import Path

def read_homework_readme(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    deadline = ""
    for line in text.splitlines():
        if "截止日期" in line or "Deadline" in line:
            deadline = line.split(":", 1)[-1].strip()
    return {"path": str(path), "deadline": deadline, "raw_len": len(text)}
```

## 课程目录名

thulearn 目录名可能含 `(教师名)` 后缀，Agent 处理时用 `test/` 下实际文件夹名，勿臆造。

## JSON API（session 客户端）

```python
from scripts.thu_learn_client import ThuLearnClient

client = ThuLearnClient.from_session_file("~/.config/autothu/session.json")
client.get_current_semester()
courses = client.list_courses()
# 每课 wlkcid 用于作业 API（见 thulearn2018 settings.homeworks_url）
```
