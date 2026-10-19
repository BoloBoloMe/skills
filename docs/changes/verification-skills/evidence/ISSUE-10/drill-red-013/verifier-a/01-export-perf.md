# 01 AC-001-1 导出性能结论 (5 次, 20000 行)

性质: 当前观察, 验收者 A 本轮实际执行. 无旧观察可用, 全部实跑. 不采信实现者说明与"作者自证"材料.

## 被验收的标准原文 (AC-001-1)

> 场景: AC-001-1 导出性能结论
>   假定 测试数据目录 runtime/data 已初始化
>   当 验收者连续 5 次运行 `python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data` 并记录每次耗时
>   那么 报告给出 p50 与极差, p50 不超过 800ms, 原始输出可复核

## 假定核对 (前置条件)

`runtime/data` 由独立验收者 B 初始化, 原件 `../verifier-b/00-init.md`. A 的适用性核对见 `03-reference-init.md`: init 退出码 0, `runtime/data/records.jsonl` 与 `outbox/replication-log.jsonl` 存在且内容与 `seed/` 一致. A 未自己跑 init.

## 计时方法

- 手段: shell 内嵌纳秒时间戳. 每次运行前 `t0=$(date +%s%N)`, 紧接执行被测命令, 命令结束后 `t1=$(date +%s%N)`, 耗时 = `t1 - t0`.
- 计时范围: 包含进程启动, 解释器启动, 模块导入, argparse, 20000 行 JSON 生成与写盘, 文件关闭/flush, stdout 打印, 进程退出. 不含时间戳取数的 `date` 子进程开销 (约 1-3ms, 在两侧各取一次, 不摊入).
- 计的数: 每次墙钟纳秒, 退出码, stdout, stderr, 导出文件行数/字节数/md5.
- 忽略: 页缓存冷热控制 (未 drop_caches; 本场景命令不含清缓存步骤, 与 AC 文字一致), 后续核对耗时.
- 解释器: 本 shell 的 `python3` 是函数 `{ uv run python "$@"; }`, 落到 CPython 3.14.7 (uv 管理), 与项目约定 `uv run python` 同一解释器. 计时因此含 uv 的少量启动开销; 另附 1 次 `/usr/bin/python3` (CPython 3.14.4) 对照, 不计入 5 次序列.

## 机器条件 (计时前后)

```
$ nproc
16

$ uptime   # 计时前 2026-10-20T00:20:43+08:00
 00:20:43 up 34 days, 10:31,  3 users,  load average: 0.30, 0.20, 0.12

$ uptime   # 计时后 2026-10-20T00:20:44+08:00
 00:20:44 up 34 days, 10:32,  3 users,  load average: 0.28, 0.20, 0.12
```

16 核, 负载 < 0.5, 机器基本空闲; 无其他重负载进程. 未停他人任务.

## 5 次运行 (逐字命令)

每次完整命令均为:

```
python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data
```

工作目录 `/tmp/orchestra-10/methods-red`. 5 次连续, 无间隔插入其他命令.

| 次 | 耗时 (ns) | 耗时 (ms) | 退出码 | export 行数 | export 字节 | stdout | stderr |
|---|---|---|---|---|---|---|---|
| 1 | 74149414 | 74.149 | 0 | 20000 | 908890 | `export-ok rows=20000 out=runtime/export.jsonl` | 空 (0 字节) |
| 2 | 73180650 | 73.181 | 0 | 20000 | 908890 | 同上 | 空 (0 字节) |
| 3 | 72542266 | 72.542 | 0 | 20000 | 908890 | 同上 | 空 (0 字节) |
| 4 | 77962463 | 77.962 | 0 | 20000 | 908890 | 同上 | 空 (0 字节) |
| 5 | 76860377 | 76.860 | 0 | 20000 | 908890 | 同上 | 空 (0 字节) |

原始文件 (逐次):

- `02-raw/run-1.stdout.txt` `02-raw/run-1.stderr.txt`
- `02-raw/run-2.stdout.txt` `02-raw/run-2.stderr.txt`
- `02-raw/run-3.stdout.txt` `02-raw/run-3.stderr.txt`
- `02-raw/run-4.stdout.txt` `02-raw/run-4.stderr.txt`
- `02-raw/run-5.stdout.txt` `02-raw/run-5.stderr.txt`

原始时间戳序列 (`02-raw/timings.csv`, 字段: 次, t0_ns, t1_ns, 耗时_ns, 退出码, 行数, 字节, md5):

```csv
1,1792426843857596213,1792426843931745627,74149414,0,20000,908890,0cbdf1a6b8b535dc1cef52b617611dcf
2,1792426843948411875,1792426844021592525,73180650,0,20000,908890,0cbdf1a6b8b535dc1cef52b617611dcf
3,1792426844040118309,1792426844112660575,72542266,0,20000,908890,0cbdf1a6b8b535dc1cef52b617611dcf
4,1792426844131136865,1792426844209099328,77962463,0,20000,908890,0cbdf1a6b8b535dc1cef52b617611dcf
5,1792426844227304349,1792426844304164726,76860377,0,20000,908890,0cbdf1a6b8b535dc1cef52b617611dcf
```

## p50 与极差 (计算过程原文见 `02-raw/stats.txt`)

排序: 72.542 / 73.181 / 74.149 / 76.860 / 77.962 (ms)

- n = 5, 中位数位置 = (5+1)/2 = 3
- **p50 = 74.149 ms** (第 3 小的值, 不是平均值; 平均值 74.939ms 仅备查, 不用作 p50)
- **极差 = max - min = 77.962 - 72.542 = 5.420 ms**
- 阈值: p50 <= 800ms, 余量 725.851 ms

## 交叉校验 (不计入 5 次序列)

1. `/usr/bin/time -f` 对同一命令测 1 次 (`02-raw/supp1-time.stdout.txt`, `supp1-time.stderr.txt`):
   ```
   export-ok rows=20000 out=runtime/export.jsonl
   elapsed=0.06 user=0.06 sys=0.00 maxrss_kb=16080 exit=0
   ```
   与纳秒法同量级 (0.06s = 60ms; 该工具只给两位小数).
2. `/usr/bin/python3` (系统 CPython 3.14.4, 不经 uv 函数) 跑同一命令 1 次 (`02-raw/supp2-systempy.stdout.txt`):
   `rc=0`, 墙钟 `69.259 ms`, stdout `export-ok rows=20000 out=runtime/export.jsonl`.
   说明解释器选择 (uv 3.14.7 含 uv 启动开销 vs 系统 3.14.4) 不改变判定.

## 错误计数与"工作真的发生"

- 失败/非成功响应: 5 次退出码全为 0, stderr 全为空, stdout 全为成功行. 失败数 = 0, 非成功响应数 = 0.
- 输出正确性: 每次运行后立即 `wc -l runtime/export.jsonl` 得 20000, 字节数 908890, md5 5 次全同 (`0cbdf1a6...`).
- 全量结构校验 (`02-raw/export-check.txt`, 只读文件): 20000 行全部可解析; 每行内容逐行等于 `{"id": "row-%06d", "text": "payload-%d"}` 且顺序正确, 不匹配数 0; id 唯一数 20000; 文件以换行结尾; 首行 `{"id": "row-000000", "text": "payload-0"}`, 末行 `{"id": "row-019999", "text": "payload-19999"}`.
- 计时区内发生的工作: `cmd_export` 在计时区内循环 20000 次生成 JSON 行并写入 `runtime/export.jsonl` 后关闭文件; 产物在计时结束后被读取核对, 非空转, 无丢弃.

## 观察到的限制/说明 (不影响判定)

- 仅读代码可看出 `cmd_export` 不使用 `--data-dir` 参数 (该参数被 argparse 接受但不参与导出). 这是被测产品在当前提交的实现现状, AC 的"假定 runtime/data 已初始化"已由 B 满足; 此项不改变 AC-001-1 的命令, 数据规模与判定. 标为推断: 来自读代码, 未作为判定依据.
- 5 次运行的解释器启动开销 (含 uv 解析) 约占总耗时的一部分; 由于距 800ms 阈值余量超过 700ms, 该开销不影响结论.

## 结论

**通过 (PASS)**.

依据: 按 AC 原文命令连续实跑 5 次, 全部退出码 0, 每次均真实写出 20000 行, p50 = 74.149 ms <= 800 ms, 极差 = 5.420 ms, p50 与极差均有原始 stdout/stderr/时间戳/导出核对材料可复核.
