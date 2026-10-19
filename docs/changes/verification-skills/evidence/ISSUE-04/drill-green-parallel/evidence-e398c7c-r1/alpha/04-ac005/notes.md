# 04-ac005 AC-005-1 alpha 侧材料 (供第 8 项核对)

本目录是交给第 8 项 (AC-005-1) 的 alpha 侧原始材料, 由我 (rev-alpha) 在本轮产出.

| 文件 | 内容 | 产生时间 | 产生命令 |
|------|------|----------|----------|
| alpha-status.png | alpha 状态页截图, 8788 bytes, sha256 4374f026939db8238ab13de9ed80aad7c997cd3ebc9a89504509d5ac51248803 | 2026-10-19T14:15:20Z (22:15:20+0800) | `google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars --virtual-time-budget=3000 --window-size=900,400 --screenshot=... alpha-status.png http://127.0.0.1:18101/status-page` exit=0 |
| report.txt | `python3 app.py report --port 18101` 原始输出 (含本次采集头与 exit/耗时) | 2026-10-19T14:15:23Z (22:15:23+0800) | 见文件内 `### cmd` 行; exit=0, 70ms |
| report-fresh.txt | 同一实例再跑一次 report + health, 用于交叉确认 | 2026-10-19T14:15:47Z (22:15:47+0800) | `python3 app.py report --port 18101`; `python3 app.py health --port 18101`; 均 exit=0 |

## 一致性说明
- 截图与 report 都指向同一进程 PID 4090884, 端口 127.0.0.1:18101, --instance alpha, VERSION 常量 relay-v1.
- 截图可读文字: `instance=alpha`, `state=ready`, `version=relay-v1`.
- report 行: `relay-report instance=alpha version=relay-v1 state=ready`.
- instance 与 version 在两侧相同 (alpha / relay-v1), report 含 `state=ready`.
- 附件 alpha-status.png 与 01-ac001/alpha-status.png 二进制相同 (sha256 一致).
