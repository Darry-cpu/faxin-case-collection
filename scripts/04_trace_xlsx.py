#!/usr/bin/env python3
"""04_trace_xlsx.py — 生成溯源清单 Excel（通用版）。"""
import argparse, json, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", required=True, help="筛选结果.json")
    ap.add_argument("--out", required=True, help="输出 xlsx")
    ap.add_argument("--note", default="溯源说明：在法信类案检索中按【案号】检索即可找到对应判决书原文")
    args = ap.parse_args()

    rows = json.load(open(args["in"], encoding="utf-8"))
    inc = [r for r in rows if r["判定"] in ("收录", "收录(初筛)")]
    pend = [r for r in rows if r["判定"] == "待查"]

    wb = Workbook()
    head_font = Font(bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="4472C4")
    thin = Border(*[Side(style="thin", color="D9D9D9")] * 4)
    COLS = ["序号", "判定", "案号", "标题", "法院", "裁判日期", "审理程序", "裁判结果", "理由", "命中片段"]
    WIDTHS = [6, 10, 24, 38, 20, 12, 8, 16, 34, 50]

    def write_sheet(ws, data, note=""):
        r0 = 1
        if note:
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(COLS))
            c = ws.cell(row=1, column=1, value=note)
            c.font = Font(bold=True, size=10)
            c.fill = PatternFill("solid", fgColor="FFF2CC")
            r0 = 3
            ws.append([])
        ws.append(COLS)
        for c in ws[1]:
            c.font = head_font
            c.fill = head_fill
            c.alignment = Alignment(vertical="center", horizontal="center")
        for r in data:
            ws.append([r.get("序号"), r.get("判定"), r.get("案号"), r.get("标题"),
                       r.get("法院"), r.get("裁判日期"), r.get("审理程序"), r.get("裁判结果"),
                       r.get("理由"), r.get("命中片段")])
        for i, w in enumerate(WIDTHS, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
                c.border = thin
        ws.freeze_panes = "A4" if note else "A2"

    ws1 = wb.active
    ws1.title = f"收录({len(inc)})"
    write_sheet(ws1, inc, args.note)
    ws2 = wb.create_sheet(f"待查({len(pend)})")
    write_sheet(ws2, pend)
    ws3 = wb.create_sheet(f"全部({len(rows)})")
    write_sheet(ws3, rows)
    wb.save(args.out)
    print(f"已生成 {args.out} | 收录 {len(inc)} | 待查 {len(pend)} | 全部 {len(rows)}")


if __name__ == "__main__":
    main()
