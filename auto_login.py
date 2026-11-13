#!/usr/bin/env python3
"""
法信自动登录引导脚本（无 stdin 交互版）：
弹出有头浏览器 -> 用户在官网登录 -> 脚本自动轮询检测登录态 ->
检测到后保存会话 cookie 并做无头复用验证。
"""
import asyncio
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright

USER_DATA_DIR = os.environ.get(
    "FAXIN_USER_DATA_DIR",
    str(Path.home() / ".faxin-mcp" / "browser-data"),
)
FAXIN_BASE = os.environ.get("FAXIN_BASE_URL", "https://www.faxin.cn")


async def probe_logged_in(page):
    """在指定 page 上探测是否已登录（会导航到检索页）。"""
    try:
        probe = f"{FAXIN_BASE}/alllibsearch/SearchResult.aspx?usersearchtype=1&keyword=test"
        await page.goto(probe, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        url = page.url.lower()
        if "login" in url:
            return False
        login_form = await page.evaluate("""() => {
            const txt = document.body ? document.body.innerText : '';
            return Boolean(document.querySelector('form#loginForm, .login-box, input[name=username]'))
                   || txt.includes('请输入账号') || txt.includes('请先登录') || txt.includes('登录法信');
        }""")
        if login_form:
            return False
        return True
    except Exception:
        return None


async def main():
    Path(USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )
    except Exception as e:
        print(f"FAIL_LAUNCH {e}")
        return

    page = browser.pages[0] if browser.pages else await browser.new_page()

    print("OPENING_FAXIN")
    try:
        await page.goto(FAXIN_BASE, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"OPEN_WARN {e}")

    print("WAITING_FOR_USER_LOGIN (auto-detect, up to 12 min)")
    logged_in = False
    deadline = time.time() + 720
    while time.time() < deadline:
        await page.wait_for_timeout(4000)
        try:
            dom_state = await page.evaluate("""() => {
                const t = document.body ? document.body.innerText : '';
                return { hasLogout: t.includes('退出'), hasLogin: t.includes('登录') };
            }""")
        except Exception:
            continue
        if dom_state.get("hasLogout"):
            cookies = await browser.cookies()
            faxin_cnt = len([c for c in cookies if 'faxin' in c.get('domain', '')])
            print(f"DOM_LOGGED_IN cookies={faxin_cnt}")
            logged_in = True
            break

    if not logged_in:
        print("LOGIN_TIMEOUT")
        await browser.close()
        return

    print("VERIFY_VIA_PROBE")
    try:
        p2 = await browser.new_page()
        status = await probe_logged_in(p2)
        await p2.close()
        print(f"PROBE_RESULT={status}")
    except Exception as e:
        print(f"PROBE_ERR {e}")

    cookies = await browser.cookies()
    faxin_cookie_count = len([c for c in cookies if 'faxin' in c.get('domain', '')])
    print(f"SESSION_SAVED cookies={faxin_cookie_count} dir={USER_DATA_DIR}")

    await browser.close()

    print("HEADLESS_REUSE_CHECK")
    try:
        pw2 = await async_playwright().start()
        b2 = await pw2.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )
        p3 = b2.pages[0] if b2.pages else await b2.new_page()
        await p3.goto(FAXIN_BASE + "/index.aspx", wait_until="domcontentloaded", timeout=30000)
        await p3.wait_for_timeout(2500)
        reuse = await probe_logged_in(p3)
        await b2.close()
        print(f"HEADLESS_REUSE={reuse}")
    except Exception as e:
        print(f"REUSE_ERR {e}")

    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())
