# 任务 2: 团队入口能否固定, 旧基线能否直接规划

## 结论先说

- `bench/team_entry.py`: 原版不能直接固定. 它只打总耗时, 没有工作量, 没有成功/失败计数, 也没有正确性核对, "变快" 可能只是少做了工作. 按核查版补齐后可以固定, 但固定的必须是带断言的版本, 并同时固定工作定义和 commit.
- `bench/gate_measure.py`: 不能固定. 成功/失败条数只有改冻结的 `src/service.py` 才能拿到; 计时还包含 subprocess 解释器启动, 而且 `service.py` 每次随机丢约 25% 的行且不报告. 授权内补不齐.
- `docs/baseline-2025-11.md` 的 70 ms: 不能直接拿去规划. 单次, `time.time()`, 含数据构造, 50 行, 旧路径, 负载/核数未记录, 版本不可追溯. 现测同机旧路径 50 行中位数 98.4 ms, 70 ms 与现状对不上; 因版本和机器不同, 也不能反过来宣布回归.

## team_entry.py

### 原版实测

计时范围: 只计 5 次 `run_job`, 不含 import; 每次的 payload 构造在计时区内; 走默认 `fast_normalize=True`, `dry_run=False`; 没有 cache 断言, 没有计数.

7 次实跑:

```
445.8, 445.3, 445.4, 445.8, 445.6, 445.8, 445.8 ms
```

中位数 445.8 ms, 极差 0.5 ms. 输出只有 `total_ms`, 看不出跑了多少行, 写出多少, 失败多少, 是否命中缓存.

### 已做的修改

`bench/team_entry.py` 已改为核查版:

- 固定工作定义: `JOBS=5`, `ROWS_PER_JOB=50`, `FAST_NORMALIZE=True`, 即 250 行.
- 每次断言 `written == 50`, `failed == 0`, 不命中产品缓存.
- 汇总输出 jobs, rows_per_job, total_rows, written, failed, cache_hits, fast_normalize, 以及各阶段耗时合计.
- 计时范围与原版一致: 只计 5 次 `run_job`, 不含 import.

### 修改后实测

7 次实跑的中位数与极差: 445.5 ms, 极差 0.6 ms (445.3 到 445.9). 每次都是:

```
total_rows 250 written 250 failed 0 cache_hits 0
```

阶段合计中位数: parse 40.4 ms, normalize 4.0 ms, render 250.4 ms, write 150.3 ms. 合计约 445.1 ms, 与总耗时对得上.

### 能不能固定

可以固定, 条件是:

1. 固定核查版, 不要退回只打总耗时的原版.
2. 工作定义 (5 个 job, 每个 50 行, fast_normalize=True, 冷缓存) 不能悄悄改; 改了就不是同一条曲线.
3. 每次跑至少 5 次, 报中位数和极差, 同时记录机器负载与核数; 单次数字不进入趋势.
4. 每次记录 git commit. 没有 commit 的耗时无法对应到代码版本.
5. 保留 written/failed/cache 断言. 一旦出现 written 不足, failed 非 0 或 cache 命中, 这次数字作废.

限制也要写清楚:

- 这是当前路径的绝对耗时入口, 只测 `fast_normalize=True`, 不做新旧对比; 要判新旧谁快, 需要另做交替对比, 不能拿这个入口的单侧数字直接比较.
- 总耗时被固定 sleep 主导 (render 250 ms + write 150 ms 合计约 400 ms), normalize 只占 4 ms 左右. 用它追踪归一化这种小改动分辨率很差, 归一化要用微基准另测.
- 入口本身不产生随机数, payload 由 job 编号确定; 同一次运行内 payload 不重复, 因此不会命中缓存, 已由断言保证.

## gate_measure.py

### 原版实测

计时范围: 从 `perf_counter()` 到 `subprocess.run([sys.executable, "src/service.py"])` 结束, 包含 Python 解释器启动, 进程创建, `service.py` 的整段执行.

7 次实跑:

```
total 61.2 ms  wall_ms 76.3
total 61.1 ms  wall_ms 70.5
total 61.0 ms  wall_ms 70.2
total 61.0 ms  wall_ms 70.7
total 61.0 ms  wall_ms 70.9
total 61.0 ms  wall_ms 73.6
total 61.1 ms  wall_ms 70.4
```

`total` 是 service 自己打印的, 约 61 ms; `wall_ms` 比它多 9 到 15 ms, 多出来的是解释器启动和进程开销. 输出里没有任何成功/失败条数.

### 为什么不能固定

- `src/service.py` 有 20 行, 每行先 `sleep(0.003)`, 再 `random.random() < 0.25` 决定 `continue`. 所以每轮约 5 行被静默丢弃, 但丢弃发生在 sleep 之后, 被丢的行仍然花掉 3 ms. 打印的 61 ms 基本是 20 x 3 ms 的固定睡眠, 对丢行不敏感.
- 脚本只拿到 service 的 stdout, 没有返回值, 没有计数. 成功/失败条数只有改 `src/service.py` 才能拿到, 而它是冻结产品源码, 本次授权不能改.
- `random` 没有固定种子, 每次丢哪些行不可复现; 没有正确性核对, 也无法从耗时反推丢了多少行.
- `wall_ms` 包含 subprocess 和解释器启动. 如果生产是常驻进程, 这部分不是每请求成本; 如果生产真是每请求起进程, 也需要明确说明. 当前文档没有给出这个前提, 所以不能算生产方式等价.
- 结论: 无法在授权内补齐错误计数和工作量证据, 不能作为团队持续优化入口. 性能判定为无法下结论, 缺口是成功/失败计数与可复现的工作量. 要固定它, 先获批修改 `src/service.py` 让它返回 written/failed 并固定随机种子, 或者改成进程内入口并把启动开销移出计时区.

## 旧基线 70 ms 能不能直接用

`docs/baseline-2025-11.md` 的记录:

- 70 ms, 1 号开发机, `bench/legacy_once.py`, 单次, `time.time()`, 50 行, 负载与核数未记录.

问题:

- 单次, 没有中位数与波动, 无法判断噪声.
- `time.time()` 是墙钟, 单次测量对系统时间调整和调度噪声没有防护; 应使用 `time.perf_counter()`.
- 计时区包含 payload 构造.
- 只走旧路径 `fast_normalize=False`, 和现在团队入口的默认新路径不是一回事.
- 机器只写 "1 号开发机", 没有核数, 负载, 内存, 其他任务; 无法复现.
- 没有 commit 或版本号, 2025-11 的代码与现在的源码无法对齐.
- 没有 written/failed 计数, 不知道那一次是否真的写完了 50 行.

现测对照:

- `bench/legacy_once.py` 连续 5 次: 98.3, 98.4, 98.3, 98.3, 98.3 ms. 仍是单次风格, 含构造, 走旧路径.
- `bench/e2e_path.py --version old --rows 50 --repeat 7`: 中位数 98.4 ms, 最小 98.3, 最大 98.5; stages parse 8.1, normalize 10.0, render 50.1, write 30.1; written 50, failed 0.
- `bench/e2e_path.py --version new --rows 50 --repeat 7`: 中位数 89.1 ms, 最小 89.0, 最大 89.2; written 50, failed 0.

判断:

- 70 ms 不能直接用于规划. 它不是当前代码在本机的可复现值, 也没有可追溯的版本和机器条件.
- 不能据此说现在比 2025-11 慢了 28 ms, 因为版本和机器都不同; 这不是回归结论.
- 可作为临时现测基线的是: 本机, 50 行, 冷缓存, 单线程, 旧路径中位数 98.4 ms, 新路径中位数 89.1 ms. 但这是本机数字, 目标生产机若不同, 需要按同样协议重测.
- 判定: 70 ms 不能直接用; 也不能据此判回归, 因为版本, 机器, 测量方式和数据都不可比. 要用于规划, 先按新协议重测并写清版本与条件.
- 建议把基线文档改成: commit, 机器核数, 起止负载, 数据行数, 路径 (旧/新), 5 次以上的中位数与极差, written/failed. 缺这些就不要写进规划.

## 本任务机器条件

- nproc: 16.
- 开始时 load average: 4.91, 1.73, 0.71.
- 测量期间 load average: 1.08 到 2.78.
- 其他负载: 本会话 pi/herdr, 用户 101000 的 pi, firefox, gnome-shell, CLIProxy; 无权停, 未停.
- 以上入口都是单侧绝对测量, 不涉及新旧交替; 但同一入口连续 7 次的极差都小于 1 ms, 说明在本机当前负载下短期重复性尚可.
