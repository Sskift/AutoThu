#!/usr/bin/env python3
"""
清华网络学堂 HTTP 客户端（基于已验证的 thulearn2018 API 端点）。

登录说明（2025+）：
- 旧端点 id.tsinghua POST .../login/post/... 已返回「该应用不允许调用登录接口」
- 推荐：浏览器登录后导入 session.json，或使用 learn reset + 信任浏览器
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests

# 与 thulearn2018/settings.py 一致（源码验证）
BASE = "https://learn.tsinghua.edu.cn/"
LOGIN_ID_LEGACY = (
    "https://id.tsinghua.edu.cn/do/off/ui/auth/login/post/"
    "bb5df85216504820be7bba2b0ae1535b/0?/login.do"
)
LOGIN_FORM = (
    "https://id.tsinghua.edu.cn/do/off/ui/auth/login/form/"
    "bb5df85216504820be7bba2b0ae1535b/0"
)
LOGIN_ROAMING = BASE + "b/j_spring_security_thauth_roaming_entry"
SEMESTER_URL = BASE + "b/kc/zhjw_v_code_xnxq/getCurrentAndNextSemester"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Connection": "keep-alive",
}


def lessons_url(semester_id: str) -> str:
    return (
        BASE
        + "b/wlxt/kc/v_wlkc_xs_xkb_kcb_extend/student/loadCourseBySemesterId/"
        + semester_id
        + "/zh"
    )


def homeworks_url(lesson_id: str) -> list[str]:
    form = f'aoData=[{{"name":"wlkcid","value":"{lesson_id}"}}]'
    types = ["Yjwg", "Wj", "Ypg"]
    return [BASE + f"b/wlxt/kczy/zy/student/zyList{x}?{form}" for x in types]


class ThuLearnClient:
    """带 XSRF 的 requests 会话封装。"""

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.verify = False
        self.semester_id: str | None = None

    @classmethod
    def from_session_file(cls, path: str | Path) -> "ThuLearnClient":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        client = cls()
        xsrf = None

        if data.get("all_cookies"):
            for c in data["all_cookies"]:
                dom = c.get("domain") or ""
                if "tsinghua.edu.cn" not in dom:
                    continue
                client.session.cookies.set(
                    c["name"],
                    c["value"],
                    domain=dom,
                    path=c.get("path", "/"),
                )
                if c["name"] == "XSRF-TOKEN" and "learn" in dom:
                    xsrf = c["value"]
        else:
            cookies = data.get("cookies") or data
            for name, value in cookies.items():
                if isinstance(value, dict):
                    continue
                client.session.cookies.set(
                    name, value, domain="learn.tsinghua.edu.cn", path="/"
                )
                if name == "XSRF-TOKEN":
                    xsrf = value

        if xsrf:
            client.session.headers["X-XSRF-TOKEN"] = xsrf
        return client

    def _csrf_params(self) -> dict[str, str]:
        token = self.session.cookies.get("XSRF-TOKEN") or self.session.cookies.get(
            "xsrf-token"
        )
        if not token:
            raise KeyError(
                "缺少 XSRF-TOKEN：请先访问 learn 首页或完成 SSO 登录后再调用 API"
            )
        return {"_csrf": token}

    def get_json(self, url: str, params: dict | None = None) -> Any:
        p = dict(params or {})
        p.update(self._csrf_params())
        r = self.session.get(url, params=p, timeout=60)
        r.raise_for_status()
        return r.json()

    def post_json(self, url: str, data: dict | None = None) -> Any:
        r = self.session.post(
            url, data=data or {}, params=self._csrf_params(), timeout=60
        )
        r.raise_for_status()
        return r.json()

    def warmup(self) -> None:
        """获取 JSESSIONID 与 XSRF-TOKEN。"""
        self.session.get(BASE, timeout=30)

    def get_current_semester(self) -> str:
        data = self.get_json(SEMESTER_URL)
        self.semester_id = data["result"]["id"]
        return self.semester_id

    def list_courses(self, semester_id: str | None = None) -> list[dict]:
        sid = semester_id or self.semester_id or self.get_current_semester()
        # thulearn2018 使用 POST（非 GET）
        data = self.post_json(lessons_url(sid), data={})
        return data.get("resultList") or []

    def ping(self) -> bool:
        try:
            self.get_current_semester()
            return True
        except Exception:
            return False


def save_session_template(path: Path) -> None:
    """写入 session 文件格式说明模板。"""
    template = {
        "username": "学号",
        "cookies": {
            "JSESSIONID": "从浏览器导出",
            "XSRF-TOKEN": "从浏览器导出",
        },
        "note": "在 learn.tsinghua.edu.cn 登录后，用浏览器开发者工具复制 Cookie",
    }
    path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
