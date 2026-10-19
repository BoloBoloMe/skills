# 01-ac001 AC-001-1 alpha 状态页与 report

判据原文 (PRODUCT.md): 假定 health 返回 `ok instance=alpha`; 当核对状态页截图与 `python3 app.py report --port 18101` 输出; 那么截图显示 `instance=alpha`, `state=ready`, `version=relay-v1`; 而且 report 输出为 `relay-report instance=alpha version=relay-v1 state=ready`.

## 命令与结果
1. 前提 health: `python3 app.py health --port 18101` -> `ok instance=alpha`, exit=0, 70ms, 2026-10-19T14:15:18Z (22:15:18+0800). 见 health.txt
2. 辅助 `python3 app.py status --port 18101` -> HTML 含 instance=alpha / state=ready / version=relay-v1, exit=0. 见 status-html.txt
3. 截图: `google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars --virtual-time-budget=3000 --window-size=900,400 --screenshot=.../04-ac005/alpha-status.png http://127.0.0.1:18101/status-page` -> exit=0, 376ms, 8788 bytes, 2026-10-19T14:15:20Z. 见 screenshot-cmd.txt, 图 alpha-status.png (与 04-ac005 同一文件, sha256 4374f026...)
4. 截图内容 (我方直接看图): 页面标题 relay board, 三行文字 `instance=alpha` / `state=ready` / `version=relay-v1`.
5. report: `python3 app.py report --port 18101` -> `relay-report instance=alpha version=relay-v1 state=ready`, exit=0, 70ms, 2026-10-19T14:15:23Z (22:15:23+0800). 见 report.txt

## 结论
通过 (当前观察). 截图三项与 report 单行逐字匹配判据, report 无多余行 (输出即单行 + 换行), 截图与 report 相隔 3 秒, 同一实例 alpha 同一版本 relay-v1. 材料类型: 当前观察 (本轮命令 + 本轮截图).
