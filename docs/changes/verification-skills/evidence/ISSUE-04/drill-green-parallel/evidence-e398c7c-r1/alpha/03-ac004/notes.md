# 03-ac004 AC-004-1 只读查看事件日志

判据原文: 假定 alpha 在跑且其耗时任务正在执行; 当运行 `python3 app.py log --port 18101`; 那么输出含 `instance=alpha` 与 `event=job-start` 且退出码 0.

## 时序 (证据)
- 14:15:34Z (22:15:34+0800) 后台起 job: `python3 app.py job --port 18101 --ms 4000 &`, 后台 pid 4092125. 见 run.txt
- 14:15:36Z (22:15:36+0800) 任务仍在执行时 (`kill -0 4092125` 返回存活, 输出 "yes, job pid 4092125 alive during log") 运行 `python3 app.py log --port 18101` -> exit=0, 66ms, 原始输出 03-ac004/log.out. 见 run.txt
- 14:15:38Z 后台 job 结束: `job-done instance=alpha elapsed_ms=4000`, exit=0, 总耗时 4065ms. 见 job-bg.out
- log.out 最后一行是 `2026-10-19T14:15:34.746476Z instance=alpha event=job-start ms=4000`, 该行之后没有对应 job-end: 证明读取发生在任务执行中.
- log.out 中 `instance=alpha` 出现 4 次, `event=job-start` 出现 3 次 (含 alpha 的两条 job-start).

## 结论
通过 (当前观察). 执行中读取成功, 输出含 `instance=alpha` 与 `event=job-start`, exit=0. 材料类型: 当前观察. 注: 该文件是多实例共享事件日志, log.out 里也含 beta 的行, 属共享目录设计, 不影响本判据的包含性要求.
