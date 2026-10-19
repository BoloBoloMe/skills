# 02-ac002 AC-002-1 alpha 耗时任务

判据原文: 当运行 `python3 app.py job --port 18101 --ms 4000`; 那么输出为 `job-done instance=alpha elapsed_ms=4000` 且退出码 0; 而且命令实际耗时不少于 4 秒.

## 命令与结果
- 命令: `python3 app.py job --port 18101 --ms 4000`
- 执行时间: 2026-10-19T14:15:26Z 起, 结束 2026-10-19T14:15:30Z (22:15:26 - 22:15:30 +0800)
- 原始 stdout: `job-done instance=alpha elapsed_ms=4000`
- exit=0
- 实际耗时 (date +%s%N 前后差): 4067 ms = 4067316912 ns, 满足 >= 4000 ms.
- 见 job.txt

## 结论
通过 (当前观察). 输出与判据逐字一致, 退出码 0, 实测 4.067 秒 >= 4 秒. 材料类型: 当前观察.
