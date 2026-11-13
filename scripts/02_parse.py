#!/usr/bin/env python3
"""02_parse.py — 解析法信卡片文本为结构化字段（通用版）。"""
import argparse, json, os, re, sys


def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def parse_card(txt):
    r = {"title": "", "cause": "", "court": "", "date": "", "case_no": "",
         "procedure": "", "result": "", "hit": ""}
    m = re.search(r"（(20\d{2})）([^（]{1,20}?民[^（]{0,12}?第?[0-9一二三四五六七八九十百千]+号)", txt)
    if m:
        r["case_no"] = m.group(0)
    m = re.search(r"同案智推\s*(?:word\s*)?(?:pdf\s*)?(.*?)(?=案情特征|（20\d{2})", txt)
    if m:
        r["title"] = clean(m.group(1))
    dates = re.findall(r"20\d{2}-\d{2}-\d{2}", txt)
    if r["case_no"]:
        bd = re.findall(r"20\d{2}-\d{2}-\d{2}", txt[: txt.find(r["case_no"])])
        if bd:
            r["date"] = bd[-1]
    if not r["date"] and dates:
        r["date"] = dates[0]
    if r["case_no"]:
        cs = re.findall(r"[\u4e00-\u9fa5]{2,25}?(?:中级人民法院|人民法院|法院)", txt[: txt.find(r["case_no"])])
        if cs:
            r["court"] = cs[-1]
    m = re.search(r"(一审|二审|再审|特别程序|督促程序)", txt)
    if m:
        r["procedure"] = m.group(1)
    m = re.search(r"(驳回上诉[^，。]{0,12}维持原判|维持原判|支持原告全部诉讼请求|驳回原告全部诉讼请求|支持原告部分诉讼请求|驳回原告部分诉讼请求|改判[^，。]{0,15}|发回重审|驳回再审申请)", txt)
    if m:
        r["result"] = m.group(1)
    # 命中片段：优先"公证X 遗嘱X"词频标记后；换关键词时回退到"结果命中"区域
    m = re.search(r"(?:公证\s*\d+\s*遗嘱\s*\d+)(.{0,600}?)(?:加载更多|查看全文|$)", txt, re.S)
    if m:
        r["hit"] = clean(m.group(1))[:600]
    else:
        m = re.search(r"结果命中.{0,60}?(.{0,600}?)(?:加载更多|查看全文|$)", txt, re.S)
        if m:
            r["hit"] = clean(m.group(1))[:600]
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", required=True, help="results_all.json")
    ap.add_argument("--out", required=True, help="输出 results_parsed.json")
    args = ap.parse_args()
    items = json.load(open(args["in"], encoding="utf-8"))
    parsed = []
    for it in items:
        p = parse_card(it["txt"])
        p["page"], p["i"] = it["page"], it["i"]
        parsed.append(p)
    json.dump(parsed, open(args["out"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    nt = sum(1 for p in parsed if not p["title"])
    nd = sum(1 for p in parsed if not p["date"])
    print(f"解析 {len(parsed)} 条 | 无标题 {nt} | 无日期 {nd}")


if __name__ == "__main__":
    main()
