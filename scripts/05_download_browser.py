#!/usr/bin/env python3
"""05_download_browser.py — 真实浏览器打印下载（浏览器端）。
轮询 cmd.json（{"uniqid": "..."}）→ 打开详情页 → 点打印按钮 → 写 ready.json。
配合 05_download_step.py 使用。"""
import json, os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.environ.get("FAXIN_USER_DATA_DIR", str(Path.home() / ".faxin-mcp" / "browser-data"))
BASE = os.environ.get("FAXIN_WORK_DIR", os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(BASE, "browser_launch.log")
CMD = os.path.join(BASE, "cmd.json")
READY = os.path.join(BASE, "ready.json")


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")


def main():
    log("=== download browser start ===")
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR, headless=False, channel="chrome",
        viewport={"width": 1600, "height": 1000}, locale="zh-CN")
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    while True:
        try:
            _ = ctx.pages
        except Exception:
            log("context closed")
            break
        if not os.path.exists(CMD):
            time.sleep(2)
            continue
        try:
            with open(CMD, "r", encoding="utf-8") as f:
                task = json.load(f)
            os.remove(CMD)
        except Exception:
            time.sleep(2)
            continue
        uniqid = task.get("uniqid", "")
        if not uniqid:
            continue
        log(f"task: {uniqid}")
        try:
            page.goto("about:blank")
            page.goto(f"https://wenshu.faxin.cn/wenshu/v2/#/detail?uniqid={uniqid}",
                      wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(3000)
            title = page.title()
            btn = page.locator("span.print[title='打印']")
            if btn.count() == 0:
                log(f"print btn missing for {uniqid}")
                with open(READY, "w", encoding="utf-8") as f:
                    json.dump({"ok": False, "uniqid": uniqid, "title": title}, f, ensure_ascii=False)
                continue
            btn.first.click(timeout=10000)
            page.wait_for_timeout(1000)
            with open(READY, "w", encoding="utf-8") as f:
                json.dump({"ok": True, "uniqid": uniqid, "title": title}, f, ensure_ascii=False)
            log(f"ready: {uniqid}")
        except Exception as e:
            log(f"task fail {uniqid}: {str(e)[:80]}")
            with open(READY, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "uniqid": uniqid, "error": str(e)[:80]}, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
