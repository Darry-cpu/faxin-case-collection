---
name: faxin-case-collection
description: 法信判决书案例收集工作流。给定检索关键词（如"公证遗嘱"、案由、时间范围），自动完成：法信全量检索→结构化解析→按收录/排除标准筛选→生成溯源清单Excel→真实浏览器打印下载PDF→逐份验证。可反复使用，只需替换关键词/案由/时间/筛选标准。触发词：收集某类判决书、法信检索下载案例、公证遗嘱判决书收集、按标准筛案例并下载PDF。
---

# 法信案例收集工作流（faxin-case-collection）

把"法信检索 → 筛选 → 下载判决书 PDF"全流程打包成可复用技能。只需替换检索参数即可反复使用。

## 用法

**重要分工（务必遵守）**：
- **检索条件由用户自己操作**：AI 只负责打开法信登录界面（https://www.faxin.cn），用户自己登录、自己输入筛选条件、自己点检索，**到达结果列表界面**后，把**结果页完整 URL**（地址栏内容，含 `cid=` 参数）提供给本流程。
- AI 负责：抓取结果 → 筛选 → 生成清单 → 下载 PDF → 验证。

调用本技能时，提供以下参数（替换关键词即可）：

| 参数 | 必填 | 示例 |
|---|---|---|
| `result_url` | 是 | 用户检索结果页完整 URL（含 cid=） |
| `include_rule` | 否 | 收录标准（默认：当事人对遗嘱成立/真实性/效力/撤回变更/内容解释有实质分歧，或法院主动审查影响裁判） |
| `exclude_rule` | 否 | 排除标准（默认：遗嘱仅是背景/无争议，或案由与遗嘱效力无关） |
| `output_dir` | 否 | 输出目录（默认 D:\法信判决书下载\） |
| `download_mode` | 否 | real_print（真实浏览器打印，默认） |

关键词可以是任意法信检索词："公证遗嘱""打印遗嘱""录音录像遗嘱""代书遗嘱"等均可，无需改代码。

## 工作流步骤（按顺序执行）

### 第 0 步：自检（首次使用/小白必做）

```bash
python scripts/00_selfcheck.py
```

检查：Python 版本、依赖库、Chrome/Edge、Playwright 引擎、法信登录会话、脚本完整性、输出目录、无硬编码关键词。全部 ✅ 才能继续；有 ❌ 按提示修复后重跑。

### 第 1 步：检索并抓取全部结果

- 用户已自行完成：登录法信 → 输入筛选条件 → 检索 → 到达结果页，提供结果页 URL。
- AI 运行抓取：

```bash
python scripts/01_search_fetch.py --url "<用户提供的结果页URL>" --out <output_dir>
```

翻页抓取全部结果（含法信码 uniqid 和卡片文本），保存 `results_all.json`。

### 第 2 步：结构化解析

用 `scripts/02_parse.py` 把卡片文本解析成结构化字段（标题/案号/法院/裁判日期/审理程序/裁判结果/命中片段）：

```bash
python scripts/02_parse.py --in <output_dir>/results_all.json --out <output_dir>/results_parsed.json
```

解析要点（吸取经验）：
- 裁判日期在案号**之前**，取案号前最后一个 yyyy-mm-dd
- 当事人名可能含数字（某1/某2），标题提取从"同案智推"后到"案情特征"前

### 第 3 步：按收录/排除标准筛选

用 `scripts/03_filter.py` 自动初筛 + 人工复核：

```bash
python scripts/03_filter.py --in <output_dir>/results_parsed.json --include "..." --exclude "..." --out <output_dir>/筛选结果.json
```

- 脚本先用关键词规则初筛（无效/不认可/撤回/撤销/伪造/异议/形式要件等），分三档：收录/排除/待查
- **必须人工复核**：逐条读命中片段确认，尤其"待查"（命中为空）的要抓全文确认（`scripts/03_filter.py --resolve`）

### 第 4 步：生成溯源清单 Excel

```bash
python scripts/04_trace_xlsx.py --in <output_dir>/筛选结果.json --out "<output_dir>/溯源清单.xlsx"
```

包含 3 个 sheet：收录清单（含法信码 uniqid、案号、理由）、待查、全部结果。收录清单顶部附溯源说明（按案号在法信可溯源）。

### 第 5 步：真实浏览器打印下载 PDF

**关键：必须用真实浏览器打印流程**（headless/程序化打印的字体渲染与真实打印对话框不同，页数会差 1-2 页、带导航——已实测确认）。

```bash
# 启动打印浏览器（有头 Chrome，读任务队列）
python scripts/05_download_browser.py

# 逐条协调（另开终端/由 AI 协调）：
python scripts/05_download_step.py next     # 发送下一条任务，等待打印对话框就绪
# 桌面操作：切到浏览器窗口前台 → 点打印对话框"保存"按钮 → Alt+S（另存为PDF）
python scripts/05_download_step.py finish   # 验证文件并移动到目标目录
```

协调要点（吸取经验）：
- 操作前先把浏览器窗口切到**前台**（否则点击无效）
- 保存对话框用 **Alt+S**（保存助记键）触发
- 用户操作桌面会中断流程，下载期间请勿动鼠标键盘
- 失败时按 Esc 关闭对话框，重新发送该条任务

### 第 6 步：验证

```bash
python scripts/06_verify.py --dir <output_dir>/打印版PDF
```

逐份检查 PDF 正文包含对应案号、无导航栏（法信大纲）、页数正常。全部通过才算完成。

## 输出物

- `<output_dir>/打印版PDF/` —— 全部入选案例的打印版 PDF（案号_标题.pdf）
- `<output_dir>/溯源清单.xlsx` —— 筛选溯源清单
- `<output_dir>/筛选结果.json` —— 结构化筛选结果

## 环境要求

- Windows + 系统安装的 Google Chrome（或 Edge）
- Python 3.12+（含 playwright、pypdf、openpyxl、lxml）
- 法信机构账号（已在浏览器持久化会话，位于 `~/.faxin-mcp/browser-data`）

## 合规声明

- 仅使用本人法信账号权限内的内容，按需检索，不绕过平台任何限额/验证
- 下载用浏览器打印功能（正常用户行为），不规避平台下载限额
- 结果仅供个人研究学习，版权归原平台
