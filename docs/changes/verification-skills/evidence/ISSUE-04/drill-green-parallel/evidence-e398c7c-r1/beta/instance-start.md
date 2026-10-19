# beta 实例启动记录

- 材料类型: 当前观察
- 启动时间: 2026-10-19T22:15:03+08:00 (进程 STARTED 字段), 22:15:04 记录
- 完整命令 (在 /tmp/orchestra-04/parallel 下执行):

```
setsid nohup python3 app.py serve --port 18102 --instance beta \
  --data-dir runtime/beta --shared-dir runtime/shared \
  > runtime/beta-serve.log 2>&1 < /dev/null &
```

- setsid 包装进程 PID: 4090711
- 实际 serve 进程 PID: 4090715 (PPID 4090711, PGID 4090715, SID 4090715, 独立会话, 本回合结束后继续运行)
- 监听: 127.0.0.1:18102 (users:(("python3",pid=4090715,fd=3)))
- 启动日志文件: runtime/beta-serve.log, 内容 `listening on 127.0.0.1:18102 instance=beta`
- 启动后 health: `ok instance=beta`, exit=0 (22:15:08)

## 生命周期约束遵守情况

- 两条标准 (AC-001-2, AC-002-2) 完成后未停止、未重启实例 (AC-005-1 材料复用同一实例).
- 未执行 append, 未创建或改写 runtime/shared/record.jsonl. 我执行的命令只有: health, status, job, report, status (截图走 /status-page), 以及只读的 ls/cat.
- runtime/shared/events.log 中出现 `instance=alpha event=append ...` 与 `instance=beta event=append ...` 两条: 由 rev-shared 通过自己/我的实例执行 append 产生, 不是我的操作; record.jsonl 同理由 rev-shared 产生 (见 shared-dir-state.txt, 22:15:25 观察).
- job 命令按产品设计会写 events.log 的 job-start/job-end, 属预期行为.
