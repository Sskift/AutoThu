#!/usr/bin/env python3
"""Import the current macOS Google Chrome learn.tsinghua.edu.cn session."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def chrome_profile() -> Path:
    base = Path.home() / "Library/Application Support/Google/Chrome"
    state = base / "Local State"
    profile = "Default"
    try:
        profile = json.loads(state.read_text()).get("profile", {}).get("last_used") or profile
    except (OSError, json.JSONDecodeError):
        pass
    db = base / profile / "Cookies"
    if not db.is_file():
        raise RuntimeError(f"找不到 Chrome Cookie 数据库：{db}")
    return db


def safe_storage_key() -> bytes:
    result = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage", "-a", "Chrome"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    password = result.stdout.rstrip("\r\n").encode()
    return PBKDF2HMAC(algorithm=hashes.SHA1(), length=16, salt=b"salti", iterations=1003).derive(password)


def decrypt(value: bytes, key: bytes) -> str:
    if value.startswith(b"v10"):
        value = value[3:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(b" " * 16))
        decryptor = cipher.decryptor()
        plain = decryptor.update(value) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return (unpadder.update(plain) + unpadder.finalize()).decode("utf-8")
    if value.startswith(b"v11"):
        raise RuntimeError("当前 Chrome Cookie 使用了此脚本尚不支持的 v11 加密格式")
    raise RuntimeError("Chrome Cookie 加密格式未知")


def browser_login_cookies() -> dict[str, str]:
    """Open a temporary Chrome profile for a user-completed SSO login."""
    try:
        from selenium import webdriver
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as exc:
        raise RuntimeError("Mac 浏览器登录需要 Selenium；请重新安装 AutoThu 依赖。") from exc

    options = webdriver.ChromeOptions()
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://learn.tsinghua.edu.cn/f/login")
        print("已打开独立 Chrome 登录窗口。请在窗口中登录网络学堂并完成双因素验证。")
        WebDriverWait(driver, 600, poll_frequency=1).until(
            lambda d: "learn.tsinghua.edu.cn" in d.current_url
            and ("退出" in d.find_element("tag name", "body").text
                 or "课程搜索" in d.find_element("tag name", "body").text)
        )
        return {
            item["name"]: item["value"]
            for item in driver.get_cookies()
            if item.get("name") in {"JSESSIONID", "XSRF-TOKEN"}
            and "learn.tsinghua.edu.cn" in item.get("domain", "")
        }
    finally:
        driver.quit()


def save_session(target: Path, cookies: dict[str, str]) -> None:
    from thu_learn_client import ThuLearnClient

    missing = {"JSESSIONID", "XSRF-TOKEN"} - cookies.keys()
    if missing:
        raise RuntimeError("登录后没有找到必要的网络学堂会话 Cookie。")
    probe = ThuLearnClient()
    for name, value in cookies.items():
        probe.session.cookies.set(name, value, domain="learn.tsinghua.edu.cn", path="/")
    probe.session.headers["X-XSRF-TOKEN"] = cookies["XSRF-TOKEN"]
    if not probe.ping():
        raise RuntimeError("网络学堂验证失败，会话可能未完成或已过期。")

    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"cookies": cookies}, ensure_ascii=False, indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=".session-", dir=target.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, target)
        os.chmod(target, 0o600)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def main() -> int:
    target = Path(os.environ.get("AUTOTHU_SESSION", Path.home() / ".config/autothu/session.json")).expanduser()
    try:
        try:
            key = safe_storage_key()
            db = chrome_profile()
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                rows = con.execute(
                    "SELECT name, encrypted_value FROM cookies "
                    "WHERE host_key IN (?, ?) AND name IN (?, ?)",
                    ("learn.tsinghua.edu.cn", ".learn.tsinghua.edu.cn", "JSESSIONID", "XSRF-TOKEN"),
                ).fetchall()
            finally:
                con.close()
            cookies = {name: decrypt(encrypted, key) for name, encrypted in rows}
            save_session(target, cookies)
        except Exception as import_error:
            print(f"无法导入现有 Chrome 会话（{import_error}）。改用独立登录窗口。")
            cookies = browser_login_cookies()
            save_session(target, cookies)
        print(f"登录成功，AutoThu 会话已保存：{target}")
        return 0
    except subprocess.CalledProcessError:
        print("Chrome 安全存储读取失败；可以在独立登录窗口重新登录。", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"登录失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
