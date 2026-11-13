#!/usr/bin/env python3
"""01_search_fetch.py — 法信检索结果抓取（通用版）。
用法: python 01_search_fetch.py --cid <结果页cid> --out <目录>
  或: python 01_search_fetch.py --url <完整结果页URL> --out <目录>
翻页抓取全部结果的 uniqid(法信码) 和卡片文本，保存 results_all.json。
"""
import argparse, json, os, re, sys, time
from pathlib import Path

USER_DATA_DIR = os.environ.get("FAXIN_USER_DATA_DIR", str(Path.home() / ".faxin-mcp" / "browser-data"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cid", default="", help="法信检索结果页URL中的cid参数")
    ap.add_argument("--url", default="", help="完整结果页URL（含token/cid）")
    ap.add_argument("--out", default=".", help="输出目录")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    if args.url:
        base_url = args.url
    elif args.cid:
        base_url = ("https://wenshu.faxin.cn/wenshu/v2/#/search?from=cpws"
                    f"&cid={args.cid}&backurl=https%3A%2F%2Fwww.faxin.cn%2F")
    else:
        print("必须提供 --cid 或 --url")
        sys.exit(1)

    Path(args.out).mkdir(parents=True, exist_ok=True)
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR, headless=True, channel="chrome",
        viewport={"width": 1600, "height": 1000}, locale="zh-CN")
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(base_url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(9000)

    all_items = []
    last_first = ""
    for pg in range(1, 100):
        cards = page.evaluate("""() => {
            const cs = [...document.querySelectorAll('.result-card')];
            return cs.map((c,i)=>({i, u: c.getAttribute('uniqid')||'',
                                   txt: (c.innerText||'').replace(/\\s+/g,' ')}));
        }""")
        if not cards:
            print(f"page {pg}: no cards, stop")
            break
        for c in cards:
            c["page"] = pg
            all_items.append(c)
        print(f"page {pg}: {len(cards)} cards, total {len(all_items)}")
        first = cards[0]["txt"][:50] if cards else ""
        if first == last_first:
            break
        last_first = first
        ok = page.evaluate("""() => {
            const pag = document.querySelector('.el-pagination');
            if (!pag) return false;
            const n = pag.querySelector('.btn-next');
            if (!n || n.className.includes('disabled')) return false;
            n.click(); return true;
        }""")
        if not ok:
            break
        page.wait_for_timeout(2600)

    # 去重（按文本前120字）
    seen, uniq = set(), []
    for it in all_items:
        k = it["txt"][:120]
        if k in seen:
            continue
        seen.add(k)
        uniq.append(it)

    out = os.path.join(args.out, "results_all.json")
    json.dump(uniq, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"抓取完成: {len(uniq)} 条 -> {out}")
    ctx.close()


if __name__ == "__main__":
    main()
