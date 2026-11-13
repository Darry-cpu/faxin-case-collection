#!/usr/bin/env python3
"""00_selfcheck.py — 法信案例收集 Skill 自检程序（小白友好）。
运行: python 00_selfcheck.py
逐项检查环境是否就绪，输出 ✅/❌ 清单和修复指引。
"""
import glob, importlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.environ.get("FAXIN_USER_DATA_DIR", str(Path.home() / ".faxin-mcp" / "browser-data"))
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
DEPENDENCIES = ["playwright", "pypdf", "openpyxl", "lxml"]


def check(ok, name, hint=""):
    mark = "✅" if ok else "❌"
    print(f"{mark} {name}")
    if not ok and hint:
        print(f"      → 修复: {hint}")
    return ok


def main():
    print("=" * 60)
    print("法信案例收集 Skill 自检")
    print("=" * 60)
    all_ok = True

    # 1. Python 版本
    v = sys.version_info
    all_ok &= check(v >= (3, 10), f"Python 版本 {v.major}.{v.minor}.{v.micro}（需 ≥3.10）",
                    "安装 Python 3.12：https://www.python.org/downloads/")

    # 2. 依赖库
    for dep in DEPENDENCIES:
        try:
            importlib.import_module(dep)
            all_ok &= check(True, f"依赖库 {dep}")
        except ImportError:
            all_ok &= check(False, f"依赖库 {dep}",
                            f"运行: {sys.executable} -m pip install {dep}（或使用 MiMo 自带的 MIMO_PYTHON 运行本技能）")

    # 3. 浏览器（Chrome/Edge，真实打印需要）
    chrome_found = next((p for p in CHROME_PATHS if os.path.exists(p)), None)
    all_ok &= check(bool(chrome_found), f"浏览器 {'Chrome/Edge: ' + chrome_found if chrome_found else '未找到 Chrome/Edge'}",
                    "安装 Google Chrome 或 Microsoft Edge")

    # 4. Playwright 浏览器引擎（headless 抓取需要）
    pw_ok = False
    try:
        r = subprocess.run([sys.executable, "-m", "playwright", "--version"],
                           capture_output=True, text=True, timeout=30)
        pw_ok = r.returncode == 0
    except Exception:
        pw_ok = False
    all_ok &= check(pw_ok, "Playwright 引擎",
                    "运行: python -m playwright install chromium")

    # 5. 法信登录会话（新版Chrome cookie 在 Default/Network/Cookies）
    login_ok = os.path.exists(USER_DATA_DIR)
    cookie_files = (glob.glob(os.path.join(USER_DATA_DIR, "Default", "Network", "Cookies")) +
                    glob.glob(os.path.join(USER_DATA_DIR, "Default", "Cookies")))
    all_ok &= check(login_ok and bool(cookie_files), "法信登录会话（~/.faxin-mcp/browser-data）",
                    "先运行 D:\\faxin-mcp\\login.py 或 auto_login.py 完成法信登录")

    # 6. 脚本完整性（scripts/ 子目录）
    scripts = sorted(glob.glob(os.path.join(SKILL_DIR, "scripts", "*.py")))
    script_ok = len(scripts) >= 6
    for s in scripts:
        r = subprocess.run([sys.executable, "-m", "py_compile", s],
                           capture_output=True, timeout=30)
        script_ok &= r.returncode == 0
    all_ok &= check(script_ok, f"脚本完整性（scripts/ 共 {len(scripts)} 个脚本语法通过）",
                    "检查 scripts/ 目录文件是否齐全")

    # 7. 输出目录可写
    out_dir = os.environ.get("FAXIN_OUTPUT_DIR", str(Path.home() / "faxin-case-downloads"))
    out_ok = False
    try:
        os.makedirs(out_dir, exist_ok=True)
        out_ok = os.access(out_dir, os.W_OK)
    except Exception:
        out_ok = False
    all_ok &= check(out_ok, f"输出目录 {out_dir} 可写",
                    "检查磁盘权限，或设置环境变量 FAXIN_OUTPUT_DIR 指定其他目录")

    # 8. 无硬编码关键词检查（保证换关键词可用；跳过自检脚本自身）
    hard_ok = True
    for s in scripts:
        src = open(s, encoding="utf-8").read()
        if "公证遗嘱" in src:
            hard_ok = False
            print(f"      ⚠ {os.path.basename(s)} 含硬编码'公证遗嘱'（应通用化）")
    self_src = open(os.path.abspath(__file__), encoding="utf-8").read()
    all_ok &= check(hard_ok, "无硬编码关键词（换关键词通用）")

    print("=" * 60)
    if all_ok:
        print("🎉 全部就绪！使用方法：")
        print("  1. 打开法信登录并检索（你自己操作），到达结果页后把网址发给 AI")
        print("  2. 让 AI 用本 Skill 抓取→筛选→下载")
    else:
        print("⚠ 有项目未就绪，按上面 ❌ 的修复指引处理后重新运行自检。")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
