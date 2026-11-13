#!/usr/bin/env python3
"""05_download_step.py — 真实浏览器打印下载（协调端）。
用法:
  python 05_download_step.py tasks --in <筛选结果.json>  生成待下载任务
  python 05_download_step.py next                       发送下一条任务（等打印对话框就绪）
  python 05_download_step.py finish                     验证保存文件并移动到目标目录
配合 05_download_browser.py 使用。"""
import json, os, sys, time, glob, re, shutil
from pathlib import Path

BASE = os.environ.get("FAXIN_WORK_DIR", os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(BASE, "tasks.json")
CMD = os.path.join(BASE, "cmd.json")
READY = os.path.join(BASE, "ready.json")
DONE_IDX = os.path.join(BASE, "done_idx.json")
DEFAULT_DL = os.environ.get("FAXIN_OUTPUT_DIR", str(Path.home() / "faxin-case-downloads"))


def safe(s):
    s = re.sub(r'[\\/:*?"<>|\s]+', "_", s or "")
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:60]


def gen_tasks(sel_path, dl_dir=DEFAULT_DL):
    sel = json.load(open(sel_path, encoding="utf-8"))
    done = set(json.load(open(DONE_IDX, encoding="utf-8"))) if os.path.exists(DONE_IDX) else set()
    inc = [r for r in sel if r["判定"] in ("收录", "收录(初筛)") and r["序号"] not in done]
    inc.sort(key=lambda r: r["序号"])
    tasks = [{"idx": r["序号"], "uniqid": r.get("法信码uniqid", ""),
              "case_no": r["案号"], "title": r["标题"]} for r in inc]
    json.dump(tasks, open(TASKS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"待下载: {len(tasks)} 条")
    return tasks


def next_task():
    if not os.path.exists(TASKS):
        print("先运行 tasks 生成任务")
        return
    tasks = json.load(open(TASKS, encoding="utf-8"))
    if not tasks:
        print("ALL_DONE")
        return
    t = tasks[0]
    if os.path.exists(READY):
        os.remove(READY)
    json.dump({"uniqid": t["uniqid"]}, open(CMD, "w", encoding="utf-8"))
    deadline = time.time() + 40
    while time.time() < deadline:
        if os.path.exists(READY):
            r = json.load(open(READY, encoding="utf-8"))
            print(json.dumps({"idx": t["idx"], "uniqid": t["uniqid"],
                              "case_no": t["case_no"], "title": t["title"],
                              "ready_ok": r.get("ok"), "page_title": r.get("title")}, ensure_ascii=False))
            return
        time.sleep(1)
    print("READY_TIMEOUT")
    return


def finish(dl_dir=DEFAULT_DL):
    if not os.path.exists(TASKS):
        print("NO_TASKS")
        return
    tasks = json.load(open(TASKS, encoding="utf-8"))
    if not tasks:
        print("ALL_DONE")
        return
    t = tasks[0]
    dl = os.path.expanduser("~") + r"\Downloads"
    deadline = time.time() + 20
    newf = None
    while time.time() < deadline:
        cands = [f for f in glob.glob(dl + r"\*.pdf") if time.time() - os.path.getmtime(f) < 120]
        if cands:
            newf = max(cands, key=os.path.getmtime)
            break
        time.sleep(1)
    if not newf:
        print("NO_NEW_FILE")
        return
    os.makedirs(dl_dir, exist_ok=True)
    target = os.path.join(dl_dir, f"{safe(t['case_no'])}_{safe(t['title'])}.pdf")
    shutil.move(newf, target)
    os.remove(READY) if os.path.exists(READY) else None
    tasks.pop(0)
    json.dump(tasks, open(TASKS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    done = set(json.load(open(DONE_IDX, encoding="utf-8"))) if os.path.exists(DONE_IDX) else set()
    done.add(t["idx"])
    json.dump(sorted(done), open(DONE_IDX, "w", encoding="utf-8"))
    print(json.dumps({"idx": t["idx"], "target": os.path.basename(target)}, ensure_ascii=False))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tasks"
    if cmd == "tasks":
        p = sys.argv[2] if len(sys.argv) > 2 else None
        if not p:
            print("用法: tasks <筛选结果.json>")
            sys.exit(1)
        gen_tasks(p)
    elif cmd == "next":
        next_task()
    elif cmd == "finish":
        finish()
