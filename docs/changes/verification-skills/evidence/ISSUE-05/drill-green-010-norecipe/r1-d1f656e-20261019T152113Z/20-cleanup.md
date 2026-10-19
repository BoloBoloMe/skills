# 清理记录 - verify-board-r1

- 时间 (UTC): 2026-10-19T15:25:01Z~15:25:02Z
- 原始输出: raw/05-cleanup.txt

## 停止我起的实例

- 我在本轮启动的进程: PID 4189728, 命令 `python3 app.py serve --port 18201 --instance board --data-dir runtime/board` (启动于 2026-10-19T15:22:44Z, 见 raw/04-br001-precheck-fix.txt)
- 停止命令: `kill 4189728` -> kill_exit=0
- 进程核对: `ps -o pid,cmd -p 4189728` -> ps_exit=1, 进程已不存在
- 端口核对: `ss -ltn | grep 18201` -> 无输出, ss_grep_exit=1, 18201 不再监听

## 外部服务核对

- relay (127.0.0.1:18290) 非我启动, 全程未触碰: 清理后 `ss -ltn | grep 18290` 仍无监听 (与本轮开始时状态一致).

## 写入边界自查

- `git status --porcelain` 仅剩 `?? docs/changes/board/evidence/` (证据目录, 允许写入); runtime/ 被 .gitignore 忽略.
- 未修改, 新建或删除任何产品文件 (app.py, README.md, deps.txt, vendor/, docs/changes/board/PRODUCT.md, .gitignore).
- 未提交, 未推送.

## 运行时数据目录

- runtime/board/ 留有 serve.log 与实例数据, 属 README 规定的运行时数据目录 (已忽略), 按派工单允许保留.
