# 法信案例收集 Skill（faxin-case-collection）

把「法信检索 → 筛选 → 下载判决书 PDF」全流程打包成可复用技能。**换关键词即可反复使用**（公证遗嘱 / 打印遗嘱 / 录音录像遗嘱 / 代书遗嘱……均适用，无需改代码）。

## 它解决什么问题

法律研究者常需要按某个主题（如"公证遗嘱"）收集判决书并下载原文。本技能自动完成：

1. **抓取**你已检索好的法信结果（322 条这种规模，自动翻页抓全）
2. **解析**成结构化字段（标题 / 案号 / 法院 / 裁判日期 / 命中片段）
3. **筛选**：按【收录 / 排除】标准自动初筛 + 人工复核
4. **生成溯源清单** Excel（含案号，可溯源）
5. **下载 PDF**：真实浏览器打印流程（点打印 → 另存为 PDF），效果与手动打印完全一致
6. **验证**：逐份检查 PDF 内容对应、无导航栏

## 安装（小白 3 步）

### 1. 准备环境

- Windows 系统 + 安装 [Google Chrome](https://www.google.com/chrome/)（或 Edge）
- 安装 [Python 3.10+](https://www.python.org/downloads/)，勾选 "Add to PATH"

### 2. 安装依赖

```bash
pip install playwright pypdf openpyxl lxml
python -m playwright install chromium
```

### 3. 配置法信登录

首次使用需要法信用本人账号登录一次（会话保存在本地，不会上传）：

```bash
python login.py      # 弹出浏览器 → 用你的法信账号登录 → 回车保存
```

> `login.py` 与 `auto_login.py` 在本仓库根目录（由本技能配套的登录工具）。

## 自检（首次使用必做）

```bash
python 00_selfcheck.py
```

10 项检查全部 ✅ 才能使用；❌ 会直接告诉你修复方法。**小白照着提示做即可，不会卡壳。**

## 使用流程（重要分工）

1. **你（用户）**：打开法信（https://www.faxin.cn）→ 登录 → 输入筛选条件（如：全文检索"公证遗嘱"限"本院认为"、民事、判决书、裁判日期范围）→ 检索 → 到达**结果列表页**
2. 把**结果页网址**（含 `cid=` 参数）交给本流程
3. **AI / 流程**：抓取 → 筛选 → 清单 → 下载 → 验证

### 步骤命令

```bash
# 1. 抓取结果（url 为你在浏览器里检索后的结果页网址）
python scripts/01_search_fetch.py --url "<结果页网址>" --out ./cases

# 2. 解析
python scripts/02_parse.py --in ./cases/results_all.json --out ./cases/results_parsed.json

# 3. 筛选（可自定义收录/排除标准）
python scripts/03_filter.py --in ./cases/results_parsed.json \
    --include "当事人对遗嘱成立/真实性/效力/撤回变更/内容解释有实质分歧" \
    --exclude "遗嘱仅是背景无争议" --out ./cases/筛选结果.json

# 4. 生成溯源清单 Excel
python scripts/04_trace_xlsx.py --in ./cases/筛选结果.json --out "./cases/溯源清单.xlsx"

# 5. 下载 PDF（真实浏览器打印）
python scripts/05_download_browser.py          # 终端1：启动打印浏览器
python scripts/05_download_step.py tasks --in ./cases/筛选结果.json   # 生成任务
# 然后对每条：05_download_step.py next → 桌面操作打印对话框保存 → finish

# 6. 验证
python scripts/06_verify.py --dir ./cases/打印版PDF
```

### 下载 PDF 的桌面操作要点

- 每条案例会自动打开详情页并弹出打印对话框
- 手动点打印对话框的「保存」，在另存为对话框按 **Alt+S**（保存）即可
- 操作前先把浏览器窗口切到**前台**（否则点击无效）
- 下载期间请勿操作鼠标键盘（会中断保存）

## 环境变量（可选配置）

| 变量 | 默认 | 说明 |
|---|---|---|
| `FAXIN_USER_DATA_DIR` | `~/.faxin-mcp/browser-data` | 法信登录会话目录 |
| `FAXIN_WORK_DIR` | 本脚本目录 | 协调文件（cmd/ready/tasks）位置 |
| `FAXIN_OUTPUT_DIR` | `~/faxin-case-downloads` | PDF 输出目录 |

## 输出物

- `打印版PDF/` —— 全部入选案例的打印版 PDF（案号_标题.pdf）
- `溯源清单.xlsx` —— 收录清单（含案号，可在法信按案号溯源）+ 待查 + 全部结果
- `筛选结果.json` —— 结构化筛选结果

## 合规说明

- 仅使用本人法信账号权限内的内容，按需检索
- 下载使用浏览器**打印功能**（正常用户行为），不绕过平台任何限额或验证
- 检索结果仅供个人研究学习使用，版权归法信平台（www.faxin.cn）及原权利人
- 使用前请遵守法信平台用户协议

## License

MIT License（见 [LICENSE](LICENSE)）
