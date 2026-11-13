#!/usr/bin/env python3
"""06_verify.py — 验证打印版 PDF（通用版）：正文含对应案号、无导航栏。"""
import argparse, glob, os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pypdf import PdfReader


def norm(s):
    return re.sub(r"[（）()、\s\-]", "", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="PDF 目录")
    ap.add_argument("--no_nav_check", action="store_true", help="跳过导航检查")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, "*.pdf")))
    ok, bad = [], []
    for f in files:
        base = os.path.basename(f)
        try:
            r = PdfReader(f)
            full = "".join((p.extract_text() or "") for p in r.pages[:10])
            full_n = norm(full)
            m = re.search(r"（(20\d{2})）([^_]+号)", base)
            if m:
                hit = norm(m.group(0)) in full_n
            else:
                title_part = base.split("_")[-1].replace(".pdf", "")[:8]
                hit = bool(title_part) and title_part in full_n
            if hit:
                if not args.no_nav_check and "法信大纲" in full:
                    bad.append((base, "含导航栏"))
                else:
                    ok.append(base)
            else:
                bad.append((base, "正文无案号"))
        except Exception as e:
            bad.append((base, f"读取失败 {e}"))
    print(f"PDF 总数: {len(files)} | 验证通过: {len(ok)} | 失败: {len(bad)}")
    for b in bad:
        print("  BAD:", b[0][:60], "|", b[1])


if __name__ == "__main__":
    main()
