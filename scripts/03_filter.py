#!/usr/bin/env python3
"""03_filter.py — 按收录/排除标准筛选（通用版）。
自动初筛（关键词规则）+ 输出待人工复核的清单。
用法: python 03_filter.py --in parsed.json --include "标准文本" --exclude "标准文本" --out 筛选结果.json
"""
import argparse, json, os, re

# 默认收录/排除标准（可被 --include/--exclude 覆盖）
DEFAULT_INCLUDE = ("当事人对该遗嘱的成立、真实性、效力、撤回变更、内容解释等问题存在实质分歧，"
                   "或者法院主动对这些问题作出影响裁判的审查；遗嘱自身的法律评价构成实质争点")
DEFAULT_EXCLUDE = ("遗嘱仅是案件背景、无争议的事实依据或普通证据，"
                   "法院实际解决的法律问题与该遗嘱本身无关")

# 争议信号词（命中片段出现这些词 → 疑似收录）
SIGNAL_WORDS = ["无效", "不认可", "不予认可", "撤回", "变更", "异议", "撤销", "伪造",
                "篡改", "非真实意思", "形式要件", "否认", "撤销该", "废除"]
# 无关案由信号（标题/命中出现 → 疑似排除，除非遗嘱效力是争点）
UNRELATED_CAUSES = ["债务清偿", "合同纠纷", "金融借款", "商标", "植物新品种",
                    "执行异议", "代位权", "租赁", "储蓄存款", "侵权责任", "排除妨害",
                    "返还原物", "分家析产", "共有纠纷", "赠与合同", "确认合同无效"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--include", default=DEFAULT_INCLUDE)
    ap.add_argument("--exclude", default=DEFAULT_EXCLUDE)
    args = ap.parse_args()

    parsed = json.load(open(args["in"], encoding="utf-8"))
    rows = []
    for n, p in enumerate(parsed, 1):
        title, hit = p["title"] or "", p["hit"] or ""
        signals = [w for w in SIGNAL_WORDS if w in hit]
        unrelated = any(c in title for c in UNRELATED_CAUSES) if title else False
        if signals and not unrelated:
            verdict = "收录(初筛)"
            reason = "命中含争议信号: " + ",".join(signals[:4])
        elif unrelated:
            verdict = "排除(初筛)"
            reason = f"案由疑似无关({[c for c in UNRELATED_CAUSES if c in title][:2]}); 需人工复核"
        elif not hit:
            verdict = "待查"
            reason = "命中为空，需查看全文"
        else:
            verdict = "排除(初筛)"
            reason = "未见实质争议信号，需人工复核"
        rows.append({"序号": n, "判定": verdict, "理由": reason, "案号": p["case_no"],
                     "标题": p["title"], "法院": p["court"], "裁判日期": p["date"],
                     "审理程序": p["procedure"], "裁判结果": p["result"],
                     "命中片段": p["hit"][:300], "page": p["page"], "i": p["i"]})

    json.dump(rows, open(args["out"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    print("判定分布:", Counter(r["判定"] for r in rows))
    print("!! 初筛结果必须人工逐条复核（尤其'待查'和'排除(初筛)'）")
    print(f"收录标准: {args.include}")
    print(f"排除标准: {args.exclude}")


if __name__ == "__main__":
    main()
