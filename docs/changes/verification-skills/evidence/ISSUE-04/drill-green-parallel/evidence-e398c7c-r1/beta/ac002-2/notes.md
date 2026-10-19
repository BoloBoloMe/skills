# AC-002-2 beta 耗时任务

- 判据原文: 假定 beta 在 127.0.0.1:18102 运行; 当运行 `python3 app.py job --port 18102 --ms 4000`; 那么输出为 `job-done instance=beta elapsed_ms=4000` 且退出码 0; 而且命令实际耗时不少于 4 秒.
- 材料类型: 当前观察.

## 前提

beta 实例由本轮启动并运行中 (PID 4090715, 见 ../instance-start.txt). health 在 22:15:08 返回 `ok instance=beta`.

## 被测命令

```
cd /tmp/orchestra-04/parallel
t0=$(date +%s%N)
python3 app.py job --port 18102 --ms 4000
rc=$?
t1=$(date +%s%N)
```

- 执行时间: 2026-10-19T22:15:12+08:00 至 22:15:16+08:00
- 原始输出: out.txt
- 耗时: 4067 ms (4067314976 ns), 用 date +%s%N 前后差测得
- 退出码: 0

## 输出核对

- 输出全文为 `job-done instance=beta elapsed_ms=4000`: 是 (逐字一致, 单行)
- 退出码为 0: 是
- 实际耗时 >= 4 秒: 是 (4067 ms >= 4000 ms)

## 结论: 通过
