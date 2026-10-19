# 00-env 环境与实例启动

- 目标提交校验: `git rev-parse HEAD` = e398c7cc7ca4e493d23689bee3cca1a34d306000, 与派工值一致; `git status --porcelain` 只有 `?? docs/changes/relay-board/evidence-e398c7c-r1/` (证据目录). 见 env.txt.
- 执行时间: 2026-10-19T14:15:05Z (22:15:05 +0800)
- 环境: python3 3.14.7, Google Chrome 154.0.8037.97; 依赖仅标准库, 见 deps.txt.
- 启动前 runtime/ 只有 rev-beta 的 beta-serve.log, 18102 已有 beta 在听; 18101 无监听, 无冲突.

## alpha 实例启动 (我方唯一负责)
- 工作目录: /tmp/orchestra-04/parallel
- 完整命令:
  `setsid nohup python3 app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared > docs/changes/relay-board/evidence-e398c7c-r1/alpha/00-env/serve.log 2>&1 &`
- PID 4090884, PPID 4090880, PGID=SID=4090884 (setsid 独立会话, 回合结束仍运行)
- 启动时间: 2026-10-19 22:15:07 +0800 (2026-10-19T14:15:07Z), 来源 ps lstart
- 启动日志: 00-env/serve.log, 内容 `listening on 127.0.0.1:18101 instance=alpha`
- 监听确认: `ss -ltnp` LISTEN 127.0.0.1:18101 pid=4090884
- 未执行 append, 未创建/改写 runtime/shared/record.jsonl.
