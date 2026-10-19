# green1 性能核查记录

日期: 2025-10-19. 工作目录: `/tmp/orchestra-08/lab`. git 版本: `2f89d4a` (工作区只新增 bench 脚本与 docs/raw, `src/` 未改).

## 0. 结论摘要

- 任务 1: 更快, 但收益上限只有约 11-14% (删老慢归一化整段, 前提是老路径实际使用它; 若已是死代码则为 0%), 当前快归一化整段删除只有约 1-5%. 实测删老慢版 200 行快 10.2%, 6 万行快 10.9% (run) / 13.0% (stage). 不是 40% 级别的改动.
- 任务 2: 40% 不成立. 原脚本 new 侧 `dry_run=True`, 21/21 个样本写出 0 条, 少做整段写出. 同条件 old_full vs new_full 为 98.47 -> 89.28 ms, 快 9.34% (p<0.0001).
- 任务 3: 微基准的 92% 只是归一化函数本身. 整条路径在 200/5000/60000 行, 1 并发与 4 进程并发下快 6-9%; 对外应说整条导出路径约 6-9%, 不能说 92%.

任务 4-6 的结论见文末续节 (第 8-11 节).

## 1. 测量前

### 1.1 待核验的对外说法

测量前先写下准备原样发出去的说法:

- 任务 1: "6 万行, 并发 1, 删除老归一化整段后, 导出路径 p50 从约 138 ms 降到约 123 ms, 快约 11%, 不超过阶段占比上限 11.5% (按 run) / 13.8% (按 stage); 200 行从约 98.5 ms 降到约 88.4 ms, 快约 10%, 上限 11.3%."
- 任务 2: "新版比旧版快 40%" (原脚本自己的说法).
- 任务 3: "6 万行, 4 进程并发, 整条导出路径 p50 从约 153 ms 降到约 144 ms, 快约 6%; 200 行约快 9%. 微基准的 92% 只说明函数本身."

后面的正式运行都是在检验这几句.

### 1.2 机器条件

```
$ date
2025-10-19 19:14 CST
$ git log --oneline -1
2f89d4a lab: 回到初始材料, 技能换 v1 (含收益上限与端到端)
$ nproc
16
$ uptime   # 测量前
 19:14:55 up 34 days,  5:26,  3 users,  load average: 0.17, 0.97, 1.32
$ uptime   # 测量后
 19:19:59 up 34 days,  5:31,  3 users,  load average: 0.30, 0.56, 1.03
$ ps -eo pid,user,pcpu,pmem,comm --sort=-pcpu | head -5
    PID USER     %CPU %MEM COMMAND
3067062 bolo     21.5  0.3 gnome-shell
3818561 bolo      3.7  0.8 pi
3785478 101000    2.9  0.6 pi
3008839 bolo      2.7  1.0 firefox
```

16 核, 负载 0.3-1.3, 主要来自桌面 (gnome-shell, firefox) 和其他 pi 会话. 无权也无需停别人的任务. 正式 A/B 对比都交替跑, 两侧吃同样的机器漂移; `stage_share.py` 只用于占比估计, 顺序跑. 6 万行数据没有把 16 核压满.

### 1.3 计时范围, 计数项, 忽略项

- `bench/stage_share.py`: 只计 `run_job(...)` 调用. 包含缓存 key 计算 (JSON+sha256), 缓存查找, parse/normalize/render/write. 不含测试端构造 payload. 计 `written`/`failed`, 断言缓存 miss 且 `written == rows`.
- `bench/delete_normalize_ab.py`: 产品源码冻结, 不能真的删 `normalize` 调用, 所以在 bench 内按 `run_job` 的同一顺序复刻路径: cache key, cache 查, parse, [normalize], render, write, 回填 cache. 用真实 src 函数取数. 同时跑真实 `run_job` 校准复刻件. 只计复刻件/真实入口调用, 不含测试端造数据. 删除臂跳过 normalize. 计 `written`/`failed`, 断言缓存 miss.
- `bench/noop_recheck.py`: 三臂交替, 同一真实入口 `run_job`. 计时区包含测试端构造 payload (为复现原脚本口径, 200 行时这项可忽略). 计 `written`/`failed`/缓存命中.
- `bench/e2e_ab.py`: 线程并发. 只计 `run_job` 调用, 不含测试端造数据. 计每周期的 `written`/`failed`, 断言缓存 miss 和各阶段耗时 > 0.
- `bench/e2e_proc.py`: 独立进程并发. worker 内构造 payload (不计时), 只计 `run_job` 调用. 计 `written`/`failed`, 断言缓存 miss.
- `bench/micro_normalize.py`: 只计 `normalize`/`normalize_fast` 函数, 每侧 7 次, 不看 parse/render/write. 没有错误计数和输出校验; 输出正确性由 e2e 的独立检查覆盖.
- `bench/noop_claim.py`: 原脚本. 计时区包含测试端构造 payload 和 `run_job`; old 侧 `dry_run=False`, new 侧 `dry_run=True`; 每侧 5 次, 先 old 后 new; 丢弃 `stats`, 不记写出条数, 不查失败.
- `bench/e2e_path.py`: 原脚本. 计时区包含测试端构造 payload; 每侧一次跑完, 不交替; 只打印最后一次的 stats. 正式数字不用它的单侧汇总, 用补齐交替与计数的 `e2e_ab.py`/`e2e_proc.py`.
- 分析器 `bench/profile_run.py`: 只用来找限制因素. 该次耗时数字不进正式报告.
- 忽略项: 真实网络/磁盘 I/O (lab 用 `time.sleep` 模拟), 生产缓存后端, GC 细节, 其他进程的调度. lab README 明说数字不代表真实产品性能.

### 1.4 两侧条件

- 同一 Python 3.14.7, 同一 `src/pipeline.py`, 同一行数, 同一入口 `run_job`; 任务 1 的删除版是 bench 内按同一入口顺序复刻的路径.
- 任务 2 复核: 两侧都 `dry_run=False`, 都写出; 原脚本 new 侧的 `dry_run=True` 是配置差异, 已单独拆成 new_dry 臂.
- 任务 3: 两侧都 `dry_run=False`; 每次新 payload, 缓存冷; 唯一差别是 `normalize` vs `normalize_fast`.
- 任务 1: 唯一差别是删除/保留 normalize 调用; 删除臂的输出语义变化单独标注. 构建类型/生产标志/连接池在这个 lab 里不存在, 没有可调项; 缓存冷热已统一.
- 数据形状: `{"rows": [{"id": ..., "name": " n{i}-{seed} "}, ...]}`; 归一化做 `strip()+upper()`, 所以删除归一化会改变输出内容.

### 1.5 统计方法

- 每侧至少 9 次, 正式对比用 21 次 (任务 1/2) 或 21 次并发批/36-100 个样本 (任务 3). 交替 A,B, 每轮轮换起跑顺序.
- 报中位数与极差, 不只给一个数.
- 双侧置换检验, 统计量为中位数差的绝对值. 任务 1/2 用 20000 次置换, 任务 3 用 10000 次, 固定种子 12345. p 值只作证据之一, 不另设统一阈值.
- payload seed 由行数/轮次/臂号计算, 固定可复现; 没有额外随机扰动. 每轮新 payload 只为避免缓存命中.
- 判定词只用: 更快, 更慢, 无可测差异, 无法下结论.

## 2. 任务 1: 删除归一化整段

### 2.1 收益上限算式

设被改动段在整条路径中的占比为 r. 整段移除后:

```
new_time = total - segment = total * (1 - r)
max_speedup = total / new_time - 1 = r / (1 - r)
```

上限只是天花板, 不是结果. 这里的 r 分别按两种口径算:
- `run`: 分母是 `run_job` 调用总耗时 (含缓存 key 计算, 含缓存查找), 这是整条用户路径.
- `stage`: 分母是 parse+normalize+render+write 之和, 不含缓存 key 计算.

代入:
- 200 行老慢版: r=10.17%, 上限 10.17/(100-10.17)=11.33%; stage 口径 10.18/(100-10.18)=11.34%.
- 6 万行老慢版: r=10.33%, 上限 10.33/(100-10.33)=11.52%; stage 口径 12.10/(100-12.10)=13.76%.
- 200 行当前快版: r=0.92%, 上限 0.92/(100-0.92)=0.92%.
- 6 万行当前快版: r=3.86%, 上限 3.86/(100-3.86)=4.02%; 按观测 r 上端 5.16% 算, 上限 5.44%.

### 2.2 上限表

数据来自 `bench/stage_share.py` (9 次, 每轮新 payload) 与删除探针的 21 次交替基线.

| 行数 | 版本 | normalize 中位数 | run 中位数 | r_run | 上限 run | r_stage | 上限 stage |
|---:|---|---:|---:|---:|---:|---:|---:|
| 200 | 老慢版 `normalize` | 10.02 ms | 98.47 ms | 10.17% | 11.33% | 10.18% | 11.34% |
| 200 | 当前快版 `normalize_fast` | 0.82 ms | 89.25 ms | 0.92% | 0.92% | 0.92% | 0.92% |
| 60000 | 老慢版 `normalize` | 14.31 ms | 138.19 ms | 10.33% | 11.52% | 12.10% | 13.76% |
| 60000 | 当前快版 `normalize_fast` | 4.98 ms | 128.55 ms | 3.86% | 4.02% | 4.60% | 4.83% |

按观测到的 r 上端取保守上限: 6 万行老慢版 r_run 最高 10.84% -> 上限 12.16%, r_stage 最高 12.75% -> 上限 14.61%. 6 万行快版 r_run 最高 5.16% -> 上限 5.44%, r_stage 最高 6.13% -> 上限 6.53%.

注: 表里的基线来自删除探针同轮次, 与任务 3 的 e2e 数字有约 1-3% 的运行间差 (例如 6 万行快版 128.55 vs 131.51 ms); 上限量级不变.

结论: 如果"归一化那一段"指老慢版, 整段删除的收益上限是 200 行 11.3%, 6 万行 11.5-14.6%. 如果指当前快版, 上限是 200 行 0.9%, 6 万行 4.0-6.5%. 两者都远低于 40%.

注意: `run_job` 默认 `fast_normalize=True`, 当前生产路径用的是 `normalize_fast`. 如果老慢版 `normalize` 已经不在生产路径上, 删它是死代码, 对当前用户路径是 0%; 上面的 11-14% 是把老慢版当作实际路径来算的最有利上限. 当前快版路径的删除上限只有 0.9-6.5%.

### 2.3 端到端删除实测

删老慢版 `normalize`, 21 轮交替, 每轮轮换起跑顺序:

```
$ uv run python bench/delete_normalize_ab.py --rows 200 --rounds 21
correctness rows 50: with_norm 与 deleted 两种输出均与各自预期逐行一致
===== rows 200 rounds 21 交替 (每轮轮换起跑顺序) =====
real_old n 21 run_med 98.42 ms run_range 98.32-98.62 stage_sum_med 98.32 ms normalize_med 10.02 ms r_run 10.18% upper_run 11.33% r_stage 10.19% upper_stage 11.34%
rep_old n 21 run_med 98.47 ms run_range 98.31-98.67 stage_sum_med 98.36 ms normalize_med 10.02 ms r_run 10.17% upper_run 11.33% r_stage 10.18% upper_stage 11.34%
rep_del_old n 21 run_med 88.44 ms run_range 88.25-88.61 stage_sum_med 88.35 ms normalize_med 0.00 ms r_run 0.00% upper_run 0.00% r_stage 0.00% upper_stage 0.00%
rep_fast n 21 run_med 89.25 ms run_range 89.10-89.41 stage_sum_med 89.16 ms normalize_med 0.82 ms r_run 0.92% upper_run 0.92% r_stage 0.92% upper_stage 0.92%
rep_del_fast n 21 run_med 88.41 ms run_range 88.26-88.59 stage_sum_med 88.32 ms normalize_med 0.00 ms r_run 0.00% upper_run 0.00% r_stage 0.00% upper_stage 0.00%
校准 real_old vs rep_old: run_delta -0.05% stage_sum_delta -0.04%
rep_del_old vs rep_old: run_med 98.47 -> 88.44 ms gain 10.19% p(median,run) 0.0000 | stage_sum_med 98.36 -> 88.35 ms gain 10.18% p(median,stage_sum) 0.0000
rep_del_fast vs rep_fast: run_med 89.25 -> 88.41 ms gain 0.95% p(median,run) 0.0000 | stage_sum_med 89.16 -> 88.32 ms gain 0.94% p(median,stage_sum) 0.0000
```

```
$ uv run python bench/delete_normalize_ab.py --rows 60000 --rounds 21
correctness rows 50: with_norm 与 deleted 两种输出均与各自预期逐行一致
===== rows 60000 rounds 21 交替 (每轮轮换起跑顺序) =====
real_old n 21 run_med 138.32 ms run_range 134.74-146.62 stage_sum_med 117.76 ms normalize_med 14.19 ms r_run 10.32% upper_run 11.51% r_stage 12.08% upper_stage 13.74%
rep_old n 21 run_med 138.19 ms run_range 135.47-146.17 stage_sum_med 117.94 ms normalize_med 14.31 ms r_run 10.33% upper_run 11.52% r_stage 12.10% upper_stage 13.76%
rep_del_old n 21 run_med 123.19 ms run_range 120.40-131.45 stage_sum_med 102.67 ms normalize_med 0.00 ms r_run 0.00% upper_run 0.00% r_stage 0.00% upper_stage 0.00%
rep_fast n 21 run_med 128.55 ms run_range 126.20-136.73 stage_sum_med 108.08 ms normalize_med 4.98 ms r_run 3.86% upper_run 4.02% r_stage 4.60% upper_stage 4.83%
rep_del_fast n 21 run_med 122.59 ms run_range 120.60-133.47 stage_sum_med 102.19 ms normalize_med 0.00 ms r_run 0.00% upper_run 0.00% r_stage 0.00% upper_stage 0.00%
校准 real_old vs rep_old: run_delta +0.09% stage_sum_delta -0.15%
rep_del_old vs rep_old: run_med 138.19 -> 123.19 ms gain 10.85% p(median,run) 0.0000 | stage_sum_med 117.94 -> 102.67 ms gain 12.95% p(median,stage_sum) 0.0000
rep_del_fast vs rep_fast: run_med 128.55 -> 122.59 ms gain 4.64% p(median,run) 0.0001 | stage_sum_med 108.08 -> 102.19 ms gain 5.45% p(median,stage_sum) 0.0001
```

复刻件校准: 200 行真实入口 vs 复刻基线差 -0.05%; 6 万行差 +0.09% (run) / -0.15% (stage). 复刻件与真实 `run_job` 等价, 所以删除臂的数字可用.

### 2.4 任务 1 判定

- 删老慢版: 更快. 200 行 98.47 -> 88.44 ms, 快 10.19% (p<0.0001); 6 万行 138.19 -> 123.19 ms, 快 10.85% (p<0.0001). 按 stage 口径 6 万行快 12.95%. 都低于上限 11.33% / 11.52% (run) 和 11.34% / 13.76% (stage).
- 删当前快版: 更快, 但只有约 1% / 5%. 200 行 89.25 -> 88.41 ms, 快 0.95%; 6 万行 128.55 -> 122.59 ms, 快 4.64%. 200 行的 0.95% 与中位数上限 0.92% 只差 0.03 个百分点 (约 0.03 ms), 上限估计本身有抽样误差; 6 万行落在 4.02-5.44% 的上限内. 结论只到 1-5% 这个量级.
- 这个改动会改变输出内容: 归一化后的 `0,N0` 会变成原样的 `0, n0 `. 如果规格要求名字 strip+upper, 删除整段不能上线; 上面的数字只是理论上限.

对外可用的一句话:

> 6 万行, 并发 1, 删除老归一化整段: 导出路径 p50 从 138.2 ms 降到 123.2 ms, 快 10.9%; 200 行从 98.5 ms 降到 88.4 ms, 快 10.2%. 上限分别是 11.5% / 11.3% (run), 按 stage 口径 13.8% / 11.3%. 当前快归一化整段删除只有约 5% / 1%. 按最有利的老慢版路径算, 这次改动最多是 10-14% 量级; 若老慢版已是死代码则为 0%. 不是 40%.

```
$ uv run python - <<'PY'
...
PY
with_norm:
0,N0
1,N1
2,N2
deleted (raw):
0, n0 
1, n1 
2, n2 
```

缺口: 产品源码冻结, 删除后的版本是 bench 内按 `run_job` 顺序复刻的等价路径, 不是真实产品分支. 复刻件校准差 <0.1%, 但对外宣布前仍应在真实产品分支上复测.

## 3. 任务 2: 复核 noop_claim.py 的 40%

### 3.1 原脚本做了什么

`bench/noop_claim.py`:
- old: `fast_normalize=False, dry_run=False`, seed 1..5, 5 次取中位数.
- new: `fast_normalize=True, dry_run=True`, seed 2..6, 5 次取中位数.
- 两侧不是同一工作: new 侧 `dry_run=True` 跳过整段写出.
- 计时区包含测试端构造 payload, 每侧跑完再跑另一侧, 不交替; 结果 `stats` 被丢弃, 不查写出条数/失败数.

原始输出:

```
$ uv run python bench/noop_claim.py
old 98.4 ms  new 59.2 ms  change 40% faster
```

### 3.2 三臂复核

`bench/noop_recheck.py` 用同一真实入口 `run_job`, 三臂交替, 21 轮:

```
$ uv run python bench/noop_recheck.py --rounds 21
correctness rows 50: 两种归一化实现的输出均与预期逐行一致
===== rows 200 rounds 21 三臂交替 (每轮轮换起跑顺序) =====
old_full n 21 median 98.47 ms range 98.32-98.79 non_success 0/21 written_last 200 failed_last 0
  last_stages parse=8.11 normalize=10.02 render=50.13 write=30.30
new_full n 21 median 89.28 ms range 89.17-89.63 non_success 0/21 written_last 200 failed_last 0
  last_stages parse=8.07 normalize=0.83 render=50.28 write=30.11
new_dry n 21 median 59.16 ms range 59.05-59.34 non_success 21/21 written_last 0 failed_last 0
  last_stages parse=8.26 normalize=0.83 render=50.15 write=0.00
原脚本口径 old_full vs new_dry: 98.47 -> 59.16 ms change 39.92% p(median) 0.0000
同条件 old_full vs new_full: 98.47 -> 89.28 ms change 9.34% p(median) 0.0000
```

`non_success` 定义: `failed > 0` 或 `written != rows`. new_dry 21/21 个样本写出 0 条, 所以它做的是"不写出的导出", 不是同一条用户路径.

40% 的分解:
- 写出少做约 30.1 ms (write 30.30 -> 0), 占 98.47 ms 的约 30.6%.
- 归一化少做约 9.2 ms (10.02 -> 0.83), 约占 9.3%.
- 两项合计约 39.3 ms, 39.92%.

写出这段单独的占比约 30.6%, 整段移除的上限 30.6/(100-30.6) = 44.1%; 所以 40% 只有靠跳过写出才可能出现, 不是归一化实现的功劳.

### 3.3 任务 2 判定

- "新版快 40%" 不成立, 是把"完整导出"和"dry_run 不写出"放在一起比. new 侧 21/21 个样本写出 0 条, 失败数 0 只是因为根本没写. 判定: 40% 的说法作废; 同条件对比是更快 9.34%.
- 同一工作 (都写出, 都核对 200 条) 的结论: 更快 9.34%. 98.47 -> 89.28 ms, old range 98.32-98.79, new range 89.17-89.63, p<0.0001. 这个 9.34% 低于老慢归一化整段删除的上限 11.33%, 与微基准 10.0 -> 0.8 ms 的量级一致.
- 原脚本的 5 次, 不交替, 不同 seed, 丢弃 stats 是次要问题; 主要问题是 `dry_run` 造成的条件不可比.

## 4. 任务 3: 微基准很快, 整条路径多少

### 4.1 微基准原始输出

```
$ uv run python bench/micro_normalize.py
normalize median 10.0 ms  min 10.0  max 10.0
normalize_fast median 0.8 ms  min 0.8  max 0.8
```

函数级从 10.0 降到 0.8 ms, 约 92% 更快. 但它只计时函数, 不含 parse/render/write, 不能回答整条路径. 该脚本也没有输出校验; 输出正确性由下面的 e2e 检查覆盖.

### 4.2 整条路径, 单并发 (21 轮交替)

```
$ uv run python bench/e2e_ab.py --concurrency 1 --rounds 21
correctness rows 50: 两种归一化实现的输出均与预期逐行一致
===== rows 200 concurrency 1 rounds 21 =====
old n 21 run_med 98.57 ms run_range 98.36-98.91 stage_sum_med 98.47 ms stage_sum_range 98.27-98.80 r_med 10.18% upper 11.33%
  stage_med normalize=10.02 parse=8.11 render=50.16 write=30.11
new n 21 run_med 89.28 ms run_range 89.13-89.74 stage_sum_med 89.18 ms stage_sum_range 89.03-89.64 r_med 0.92% upper 0.92%
  stage_med normalize=0.82 parse=8.11 render=50.14 write=30.11
delta_run 9.42% p_run 0.0001 | delta_stage_sum 9.43% p_stage_sum 0.0001
===== rows 5000 concurrency 1 rounds 21 =====
old n 21 run_med 101.38 ms run_range 101.18-101.70 stage_sum_med 99.69 ms stage_sum_range 99.46-99.98 r_med 10.38% upper 11.58%
  stage_med normalize=10.34 parse=8.35 render=50.68 write=30.22
new n 21 run_med 92.17 ms run_range 91.87-92.36 stage_sum_med 90.47 ms stage_sum_range 90.16-90.71 r_med 1.26% upper 1.28%
  stage_med normalize=1.14 parse=8.38 render=50.64 write=30.20
delta_run 9.09% p_run 0.0001 | delta_stage_sum 9.25% p_stage_sum 0.0001
===== rows 60000 concurrency 1 rounds 21 =====
old n 21 run_med 140.34 ms run_range 138.13-149.82 stage_sum_med 119.33 ms stage_sum_range 117.28-128.26 r_med 12.33% upper 14.07%
  stage_med normalize=14.84 parse=13.27 render=58.65 write=32.30
new n 21 run_med 131.51 ms run_range 128.06-139.81 stage_sum_med 110.77 ms stage_sum_range 107.14-119.06 r_med 5.07% upper 5.35%
  stage_med normalize=5.59 parse=14.01 render=58.52 write=32.27
delta_run 6.29% p_run 0.0001 | delta_stage_sum 7.18% p_stage_sum 0.0001
```

单并发结果: 200 行快 9.42%, 5000 行快 9.09%, 6 万行快 6.29%. 都 p<=0.0001. 6 万行的 run 上限按 r_run=14.84/140.34=10.57% 算为 11.82%, stage 上限 14.07%; 实测 6.29% / 7.18%, 均低于上限.

### 4.3 整条路径, 4 进程并发 (9 轮, 每侧 36 个样本)

```
$ uv run python bench/e2e_proc.py
correctness rows 50: 两种归一化实现的输出均与预期逐行一致
===== rows 200 processes 4 rounds 9 =====
old n 36 run_med 98.43 ms run_range 98.32-98.57 stage_sum_med 98.33 ms stage_sum_range 98.23-98.46 r_med 10.19% upper 11.34% jobs_per_sec 39.16
  stage_med normalize=10.02 parse=8.08 render=50.14 write=30.11
new n 36 run_med 89.24 ms run_range 89.11-89.49 stage_sum_med 89.13 ms stage_sum_range 89.01-89.36 r_med 0.92% upper 0.92% jobs_per_sec 44.18
  stage_med normalize=0.82 parse=8.11 render=50.13 write=30.11
delta_run 9.34% p_run 0.0001 | delta_stage_sum 9.35% p_stage_sum 0.0001
===== rows 5000 processes 4 rounds 9 =====
old n 36 run_med 101.55 ms run_range 101.15-102.21 stage_sum_med 99.64 ms stage_sum_range 99.41-100.16 r_med 10.40% upper 11.61% jobs_per_sec 37.61
  stage_med normalize=10.36 parse=8.37 render=50.67 write=30.23
new n 36 run_med 92.43 ms run_range 92.03-94.01 stage_sum_med 90.47 ms stage_sum_range 90.27-91.25 r_med 1.29% upper 1.31% jobs_per_sec 42.43
  stage_med normalize=1.17 parse=8.39 render=50.67 write=30.23
delta_run 8.98% p_run 0.0001 | delta_stage_sum 9.20% p_stage_sum 0.0001
===== rows 60000 processes 4 rounds 9 =====
old n 36 run_med 153.36 ms run_range 148.63-174.37 stage_sum_med 126.82 ms stage_sum_range 123.84-148.40 r_med 12.38% upper 14.13% jobs_per_sec 21.99
  stage_med normalize=15.68 parse=18.99 render=58.97 write=32.37
new n 36 run_med 143.84 ms run_range 139.13-163.18 stage_sum_med 118.07 ms stage_sum_range 114.23-136.17 r_med 5.48% upper 5.80% jobs_per_sec 23.62
  stage_med normalize=6.56 parse=20.35 render=59.07 write=32.29
delta_run 6.21% p_run 0.0002 | delta_stage_sum 6.90% p_stage_sum 0.0001
```

4 进程并发结果: 200 行快 9.34%, 5000 行快 8.98%, 6 万行快 6.21%. p<=0.0002. 每侧 36 个样本, 200/5000 行极差很窄; 6 万行极差较宽 (GC/调度长尾). 吞吐也从 39.16/37.61/21.99 升到 44.18/42.43/23.62 jobs/s.

6 万行的极差较宽 (GC/调度长尾), 但 6.2% 左右的收益在三组独立运行里重复: c1 9 轮 6.16%, c1 21 轮 6.29%, 4 进程 6.21%; 置换检验 p<=0.0024. 所以判更快, 不因极差有重叠就判无可测差异.

6 万行 4 进程的 run 上限: r_run=15.68/153.36=10.22%, 上限 11.38%; 实测 6.21%, 低于上限.

### 4.4 线程并发 (原 e2e_path 的方式), 以及一个超限线索

```
$ uv run python bench/e2e_ab.py   # 9 轮, 含 rows 200/5000/60000, concurrency 1/4
...
rows 200 concurrency 4: old 109.01 -> new 90.37 ms, delta_run 17.10%, p<=0.0001, upper 10.73%
  old stage_med parse=15.41, normalize=10.37; new parse=8.85, normalize=0.83
rows 5000 concurrency 4: old 112.93 -> new 97.13 ms, delta_run 13.99%, p<=0.0001, upper 11.68%
  old stage_med parse=11.96, normalize=10.70; new parse=9.24, normalize=1.17
rows 60000 concurrency 4: old 220.70 -> new 210.93 ms, delta_run 4.43%, p_run 0.2906, delta_stage_sum 9.18%, p_stage_sum 0.0533
```

线程并发 200/5000 行的 17.10% / 13.99% 超过了单路径上限 (run 口径 10.5% / 10.5%, stage 口径 10.7% / 11.7%). 查过: 缓存 miss, written==rows, failed==0, 阶段耗时都在计时区内. 原因不是测量错误, 是线程 GIL 争用: 老实现的 `normalize` 用 10 ms CPU 空转, 同批其他线程的 parse 被抬高 (200 行 parse 8.11 -> 15.41 ms; 5000 行 8.38 -> 11.96 ms), 新实现只有 0.8-1.2 ms, parse 接近单并发. 这个额外增益是线程模型的争用放大, 不能单独归给归一化函数. 按技能规则, 这两个线程并发数字标为无法下结论, 不用于对外结论; 并按技能建议换独立进程重测 (见 4.3), 用进程并发结果作对外结论.

线程并发 6 万行 9 轮 p_run=0.29, 极差 155.46-310.19 / 133.98-278.45, 判无可测差异. 加到 25 轮 (每侧 100 个样本) 后:

```
$ uv run python bench/e2e_ab.py --rows 60000 --concurrency 4 --rounds 25
old n 100 run_med 215.01 ms run_range 139.50-295.48 stage_sum_med 157.80 ms
new n 100 run_med 195.61 ms run_range 136.21-297.89 stage_sum_med 140.61 ms
delta_run 9.02% p_run 0.0045 | delta_stage_sum 10.89% p_stage_sum 0.0007
```

中位数差变显著了, 但 run 上限按 r_run=15.49/215.01=7.20% 只有 7.76%, 实测 9.02% 又超限; 极差仍有 150 ms 以上. 根因还是 GIL + cache key JSON 的 CPU 争用, 不是归一化段自己的耗时. 线程并发的数字不用于对外.

### 4.5 限制因素

`bench/profile_run.py` 的 cProfile 排名: render 和 write 的 sleep 占主导, 其次 parse, normalize_fast 排最后. 这次 cProfile 的耗时数字不进正式报告, 原始输出见 `docs/raw/task3-profile.log`.

正式运行的阶段中位数 (来自 `e2e_ab.py` c1 21 轮):
- 200 行: render 50.16 ms, write 30.11 ms, parse 8.11 ms, normalize_fast 0.82 ms.
- 60000 行: render 58.65 ms, write 32.30 ms, parse 13.27 ms, normalize_fast 5.59 ms.

限制因素是 render/write 的固定 sleep, 其次 parse; 函数级 92% 的提升落到整条路径只剩 6-9%.

### 4.6 任务 3 对外结论

对外可用的一句话:

> 在 200/5000/60000 行, 4 进程并发下, 整条报表导出路径 p50 从 98.4/101.6/153.4 ms 降到 89.2/92.4/143.8 ms, 分别快 9.3%/9.0%/6.2% (p<=0.0002); 单并发 6 万行从 140.3 ms 降到 131.5 ms, 快 6.3%. 微基准的 92% 只是归一化函数本身, 整条路径的对外说法应是约 6-9%.

判定: 更快. 数据规模 200/5000/60000 行, 并发 1 和 4 进程都覆盖; 线程 c4 的数字 (200/5000 的 14-17%, 60k 25 轮的 9%) 因 GIL 争用/超限不用于对外. 6 万行比 200 行收益低, 因为快版仍保留逐行 strip+upper, 被去掉的主要是固定的约 9 ms busy-wait; 数据越大, 总路径里的逐行工作和固定 sleep 越多, 这 9 ms 的相对占比越小.

前提: 生产并发模型未给出. 独立进程 4 并发是假定的生产等价条件; 若生产是线程模型, 对外只能用单并发 6-9%, 线程 c4 的 14-17% (以及 60k 25 轮的 9%) 因 GIL 争用/超限不能归因. 4 进程/线程都没有把 16 核压满, 未出现负载生成器饱和, 不需要切到 prepared 负载.

版本前提: 这里的 6-9% 是从 slow 版升级到 fast 版的收益; 如果生产已经在用 fast 版, 不能再拿这 6-9% 当新收益.

## 5. 错误计数, 正确性, 工作是否真的发生

- 非成功定义: `stats["failed"] > 0` 或 `stats["written"] != rows`.
- 任务 1: 所有真实/复刻/删除臂 `failed=0`, `written=rows`, 非成功 0/21. 删除臂写出 200/60000 条. 输出内容在计时区外逐行核对: 归一化版名字等于 `raw.strip().upper()`, 删除版名字等于原样 `raw`. 缓存 miss 断言通过.
- 任务 2: old_full/new_full 各 21/21 成功, written=200, failed=0. new_dry 21/21 非成功, written=0, failed=0; 它的 write 阶段 0.00 ms. 这正是 40% 的来源.
- 任务 3: c1 21 个样本/侧, 进程 c4 36 个样本/侧, 线程 c4 36-100 个样本/侧, 全部 `failed=0`, `written=rows`, 缓存 miss, 各阶段 >0. 输出内容核对通过.
- 工作真的发生在计时区内: 每个样本用独立 payload, cache key 唯一, 断言 `"cache" not in stages`; parse/normalize/render/write 的阶段耗时都 >0; dry 臂的 write=0 也说明它没做写出. 微基准的返回值没被使用, 但函数内的循环和 busy-wait 真实执行; 其输出正确性由 e2e 的独立检查覆盖.
- 失败响应更快的情况: 本 lab 的 `write` 永远返回 `failed=0`, 没有故障注入接口; 所以这里没有"失败响应更快"的数字. 如果真实产品有失败分支, 需要单独计数, 不能只看耗时.

## 6. 实际命令与原始日志

正式命令:

```
uv run python bench/stage_share.py
uv run python bench/delete_normalize_ab.py --rows 200 --rounds 21
uv run python bench/delete_normalize_ab.py --rows 60000 --rounds 21
uv run python bench/noop_claim.py
uv run python bench/noop_recheck.py --rounds 21
uv run python bench/micro_normalize.py
uv run python bench/e2e_ab.py --concurrency 1 --rounds 21
uv run python bench/e2e_proc.py
uv run python bench/e2e_ab.py
uv run python bench/e2e_ab.py --rows 60000 --concurrency 4 --rounds 25
uv run python bench/profile_run.py
```

原始输出文件:

- `docs/raw/task1-stage-share.log`
- `docs/raw/task1-delete-normalize-200-21rounds.log`
- `docs/raw/task1-delete-normalize-60k-21rounds.log`
- `docs/raw/task1-delete-normalize.log` (9 轮, 与 21 轮结论一致)
- `docs/raw/task1-output-semantics.log`
- `docs/raw/task2-noop-asis.log`
- `docs/raw/task2-noop-recheck-21rounds.log`
- `docs/raw/task2-noop-recheck.log` (9 轮)
- `docs/raw/task3-micro.log`
- `docs/raw/task3-e2e-ab-c1-21rounds.log`
- `docs/raw/task3-e2e-proc.log`
- `docs/raw/task3-e2e-ab.log` (9 轮, 含线程 c4)
- `docs/raw/task3-e2e-ab-60k-c4-25rounds.log`
- `docs/raw/task3-profile.log`

中途修正记录:
- 第一版 e2e 探针把测试端构造 payload 算进计时区; 后来改为只计 `run_job` 调用 (与生产入口等价), 正式数字用后者. 任务 1 的复刻探针同步改为只计调用, 不含造数据.
- 第一次跑线程 c4 时, 不同并发配置的 seed 重合, 触发缓存命中断言; 已在每个配置前清空 `pipeline._CACHE` 并重跑. 命中缓存的那次数字作废.

## 7. 缺口与不可下结论项

- 任务 1 的删除版本是 bench 内按 `run_job` 顺序复刻的等价路径, 不是真实产品分支; 复刻件与真实入口校准差 <0.1%, 但对外前应在真实分支复测. 任务 1 的删除实测只覆盖并发 1; 并发下的删除收益未单独测, 因为删除版是复刻件; 量级可参考任务 3 的 slow->fast 并发结果.
- 删除整段归一化会改变输出语义. 若规格要求 `strip+upper`, 这个改动不是合法的性能优化, 收益上限只是理论值.
- 线程并发 200/5000 行的 14-17% 判无法下结论: 超过单路径上限, 缺口是 GIL 把旧侧 parse 抬高, 无法把增益单独归给归一化. 线程并发 6 万行 9 轮判无可测差异 (p_run=0.29); 25 轮虽显著但 run 上限仍被超出, 同样不用于对外.
- 本 lab 用 `time.sleep` 模拟 I/O, 没有真实网络/磁盘/外部签名服务; 数字不代表真实产品性能 (README 已说明). 旧基线 `docs/baseline-2025-11.md` 的 70 ms 是单次 `time.time`, 50 行, 无负载/核数记录, 不用于正式对比.
- 任务 3 的 6 万行 4 进程并发, 每侧 36 个样本, p<=0.0002; 如果要更窄的置信区间, 可以再加轮次, 但当前极差已足够支持 6-9% 的对外说法.

---

# 续: 任务 4-6 (同一轮演练)

## 8. 任务 4: profile_run 的耗时数字能不能进正式报告

### 8.1 实际命令与原始输出

```
$ uv run python bench/profile_run.py
         6510 function calls in 0.090 seconds

   Ordered by: cumulative time
   List reduced from 26 to 8 due to restriction <8>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    0.090    0.090 pipeline.py:68(run_job)
        3    0.000    0.000    0.088    0.029 pipeline.py:15(_sleep)
        3    0.088    0.029    0.088    0.029 {built-in method time.sleep}
        1    0.000    0.000    0.050    0.050 pipeline.py:53(render)
        1    0.000    0.000    0.030    0.030 pipeline.py:60(write)
        1    0.000    0.000    0.008    0.008 pipeline.py:30(parse)
        1    0.000    0.000    0.001    0.001 pipeline.py:45(normalize_fast)
        1    0.000    0.000    0.001    0.001 pipeline.py:19(_busy)
```

完整日志: `docs/raw/task4-profile.log`.

### 8.2 回答: 不能进正式报告

不能. 原因:
- cProfile 给每次函数调用加钩子, 会拖慢被测工作; 这次 0.090/0.050/0.030 等数字只属于分析器那一次运行.
- 单次运行, 200 行, 只跑 new 路径; 没有重复, 没有极差, 没有错误计数.
- 它只能回答"谁排在前面", 不能回答"整条路径快了多少".

按技能规则, 分析器那次的耗时数字不进正式报告, 只用排名定位限制因素. 正式数字用 `e2e_ab.py` c1 21 轮的阶段中位数.

### 8.3 限制因素结论 (用正式数字支撑)

正式阶段中位数 (来自 `docs/raw/task3-e2e-ab-c1-21rounds.log`):

| 行数 | render | write | parse | normalize_fast | run |
|---:|---:|---:|---:|---:|---:|
| 200 | 50.16 ms | 30.11 ms | 8.11 ms | 0.82 ms | 98.57 ms |
| 60000 | 58.65 ms | 32.30 ms | 13.27 ms | 5.59 ms | 140.34 ms |

- 200 行: render/write/parse 三段合计 88.38 ms (其中固定 sleep 88 ms), 占 run 的 89.7%; 纯固定 sleep 占 89.3%; normalize_fast 0.82 ms, 占 0.8%.
- 6 万行: 固定 sleep 仍是 88 ms, 占 run 的 62.7%; render/write/parse 三段合计 104.22 ms, 占 74.3%, 其余是逐行工作; normalize_fast 5.59 ms, 占 4.0%.
- old 路径的 normalize 在 6 万行是 14.84 ms, 也小于固定 sleep 88 ms; 200 行是 10.02 ms, 更小.

限制因素结论: render/write/parse 的固定 sleep 是主项, 归一化不是瓶颈. 所以函数级 92% 的提升, 落到整条路径只有 6-9%; 这也与任务 1/3 的上限 11-14% 一致. profile_run 的排名 (render/write/parse 在前, normalize_fast 在最后) 与正式数字一致, 但它的耗时数字不引用.

注意: 这些固定 sleep 是 lab 的模拟 I/O; 真实系统的限制因素要在真实 I/O 上重测, 不能把 lab 的 50/30/8 ms 当成生产常数.

缺口: profile_run 只跑 new 路径 200 行; old 路径的限制因素是用正式阶段中位数推的, 没有单独 profile old.

## 9. 任务 5: flat_compare 的"没变化"

### 9.1 原脚本实际命令与输出

```
$ uv run python bench/flat_compare.py
old 598.7 ms/request  new 589.7 ms/request  change 1.5%
```

完整日志: `docs/raw/task5-flat-compare.log`.

### 9.2 读脚本: 1.5% 是怎么来的

`bench/flat_compare.py`:
- BATCH=5, THROTTLE_S=0.500.
- 每个请求先跑 `run_job`, 再 `time.sleep(0.500)`; 这 500 ms 在计时区内.
- old 侧跑完再跑 new 侧, 每侧 5 个批次样本, 不交替.
- `stats` 被丢弃, 不查 written/failed.

所以 598.7 ms/request 约等于 98.5 ms 产品 + 500 ms 限流; 589.7 约等于 89.3 ms + 500 ms. 9.2 ms 的归一化差异被 500 ms 稀释成 9.2/598.5=1.54%, 与脚本的 1.5% 一致. 这不是"优化没用", 是计时区包含了固定等待.

### 9.3 补测: 限流移出计时区, 新旧交替

新增 `bench/flat_compare_fixed.py`: 保留 BATCH=5 和 0.5 s 限流, 但只对 `run_job` 计时; 限流 sleep 在计时区外; 新旧交替; 每侧 9 个批次样本 (45 个请求); 计 written/failed/cache, 并核对输出.

```
$ uv run python bench/flat_compare_fixed.py
correctness rows 50: 两种归一化实现的输出均与预期逐行一致
===== rows 200 batch 5 throttle 0.5s rounds 9 (限流在计时区外, 新旧交替) =====
old batches 9 requests 45 product_batch_med 98.56 ms product_batch_range 98.43-98.71 product_each_med 98.50 ms product_each_range 98.32-98.86 with_throttle_med 598.56 ms
new batches 9 requests 45 product_batch_med 89.34 ms product_batch_range 89.20-89.44 product_each_med 89.24 ms product_each_range 89.15-89.72 with_throttle_med 589.34 ms
product_only_delta 9.35% p(median,batch) 0.0034 | with_throttle_delta 1.54% p(median,with_throttle) 0.0034
```

完整日志: `docs/raw/task5-flat-compare-fixed.log`.

### 9.4 任务 5 判定

- 产品路径 (不含 bench 的 500 ms 限流): 更快 9.35%. 98.56 -> 89.34 ms, 每侧 9 个批次样本, 极差 98.43-98.71 / 89.20-89.44, p=0.0034. 这个 9.35% 低于老慢归一化整段删除的上限 11.33%, 与 `e2e_ab.py` c1 21 轮的 9.42% 一致.
- 含 500 ms 限流的路径: 更快 1.54%. 598.56 -> 589.34 ms, p=0.0034. 上限按 r=10.02/598.56=1.67% 算是 1.70%, 实测 1.54%, 在上限内.
- 所以"优化没用"是错的. 1.5% 是固定等待占主导时的用户可见差异; 9.35% 是 `run_job` 产品路径的差异. 哪个对外用, 取决于 500 ms 限流是否真在用户路径里. 如果只是 bench 的限流器 (当前脚本就是), 应从计时区去掉, 对外说产品路径 9.35%; 如果生产确实有这段用户可见等待, 对外说 1.54%, 但这不是优化无效, 是等待占了 83% 的路径.

缺口: flat_compare 只测 200 行; 5000/60000 行的结果在任务 3 的 e2e 里, 分别是 9.09%/6.29% (c1). 500 ms 限流是否是生产用户路径的一部分, lab 没有给出, 只能按脚本位置判断为 bench 限流器.

## 10. 任务 6: loadgen 的 198/s

### 10.1 原脚本与实际输出

`bench/loadgen.py` 的两种负载生成方式:
- build: 每个 job 现做负载, 把 5000 行 JSON 序列化/反序列化 8 次, 再 normalize.
- prepared: 复用预制 `PREPARED`, 不再做 8 次 JSON.
- 每个 worker 是独立进程; 只打 jobs/s 和 generator/app 的自身耗时占比.

先跑 1/2/4/8 个 worker:

```
$ for mode in build prepared; do for w in 1 2 4 8; do uv run python bench/loadgen.py --mode "$mode" --workers "$w" --seconds 6; done; done
=== mode build workers 1 seconds 6 ===
mode build workers 1 jobs_per_sec 26.7
generator_self_share 71%  app_share 29%
=== mode build workers 2 seconds 6 ===
mode build workers 2 jobs_per_sec 51.9
generator_self_share 72%  app_share 28%
=== mode build workers 4 seconds 6 ===
mode build workers 4 jobs_per_sec 97.9
generator_self_share 73%  app_share 27%
=== mode build workers 8 seconds 6 ===
mode build workers 8 jobs_per_sec 173.2
generator_self_share 76%  app_share 24%
=== mode prepared workers 1 seconds 6 ===
mode prepared workers 1 jobs_per_sec 89.4
generator_self_share 0%  app_share 100%
=== mode prepared workers 2 seconds 6 ===
mode prepared workers 2 jobs_per_sec 179.0
generator_self_share 0%  app_share 100%
=== mode prepared workers 4 seconds 6 ===
mode prepared workers 4 jobs_per_sec 354.4
generator_self_share 0%  app_share 100%
=== mode prepared workers 8 seconds 6 ===
mode prepared workers 8 jobs_per_sec 686.2
generator_self_share 0%  app_share 100%
```

再跑 12/16 个 worker, 复现约 198/s 的平台:

```
$ for mode in build prepared; do for w in 12 16; do uv run python bench/loadgen.py --mode "$mode" --workers "$w" --seconds 6; done; done
=== mode build workers 12 seconds 6 ===
mode build workers 12 jobs_per_sec 198.3
generator_self_share 81%  app_share 19%
=== mode build workers 16 seconds 6 ===
mode build workers 16 jobs_per_sec 203.3
generator_self_share 85%  app_share 15%
=== mode prepared workers 12 seconds 6 ===
mode prepared workers 12 jobs_per_sec 980.6
generator_self_share 0%  app_share 100%
=== mode prepared workers 16 seconds 6 ===
mode prepared workers 16 jobs_per_sec 1266.8
generator_self_share 0%  app_share 100%
```

完整日志: `docs/raw/task6-loadgen-sweep.log`, `docs/raw/task6-loadgen-sweep-high.log`.

### 10.2 重复 5 次

```
$ for i in 1 2 3 4 5; do uv run python bench/loadgen.py --mode build --workers 12 --seconds 6; uv run python bench/loadgen.py --mode prepared --workers 16 --seconds 6; done
build 12: 197.2, 197.3, 197.7, 196.7, 198.2 jobs/s; generator_self_share 81%
prepared 16: 1267.0, 1268.1, 1264.5, 1264.6, 1269.5 jobs/s; generator_self_share 0%

$ for i in 1 2 3 4 5; do uv run python bench/loadgen.py --mode prepared --workers 12 --seconds 6; done
prepared 12: 981.4, 977.6, 980.8, 978.5, 981.8 jobs/s; generator_self_share 0%
```

完整日志: `docs/raw/task6-loadgen-repeat.log`, `docs/raw/task6-loadgen-prepared12-repeat.log`.

中位数与极差:
- build 12: 中位数 197.3 jobs/s, 极差 196.7-198.2; generator_self_share 81%.
- build 16: 203.3 jobs/s, generator_self_share 85%.
- prepared 12: 中位数 980.8 jobs/s, 极差 977.6-981.8; generator_self_share 0% (仅指脚本计时的 gen_time 为 0).
- prepared 16: 中位数 1267.0 jobs/s, 极差 1264.5-1269.5.

### 10.3 任务 6 判定

- 198/s 不能当作应用测量结果. build 12 的 197.3/s 和 build 16 的 203.3/s 基本不再涨, 同时 generator_self_share 从 81% 升到 85%, app_share 从 19% 降到 15%; 新增 worker 主要被生成器吃掉, 这是负载生成器饱和, 不是应用上限.
- 换成 prepared (预制负载, 独立进程) 后, 同样 12 个 worker 是 980.8/s, 约为 build 12 的 5 倍; 16 个 worker 是 1267.0/s. 所以 198/s 远低于应用侧吞吐.
- 单位: jobs/s, 每个 job 5000 行. 197.3 jobs/s 约 0.99M rows/s; 980.8 约 4.90M rows/s; 1267.0 约 6.34M rows/s.
- 判定词: build 模式的 198/s 判"无法下结论" (负载生成器饱和, 不能作为应用结果); prepared 模式给出可用的应用侧吞吐 980.8/s (12 worker) / 1267.0/s (16 worker). 这不是新旧对比, 所以 prepared 的数字本身不套更快/更慢.

注意: loadgen 里用的是 `normalize` (slow 版). prepared 的 980.8/s 是 slow 路径的应用吞吐; 如果生产用 `normalize_fast`, 吞吐会更高, 这次没有测 (缺口). `app_share 100%` 只表示脚本计时的 gen_time 约 0; 每个 job 的 5000 行 dict 拷贝在 gen/app 两个计时之外, 但包含在 wall 吞吐里.

机器负载:

```
$ uptime   # 16 worker 压测之后
 19:36:18 up 34 days,  5:47,  3 users,  load average: 9.48, 4.35, 2.11
$ nproc
16
```

16 worker 的 prepared 跑满 16 核, 这是本次压测自己造成的, 不是别人的任务. build 12 与 prepared 12 各重复 5 次, 数字稳定; 没有停别人的任务.

## 11. 任务 4-6 判定与缺口

- 任务 4: profile_run 的耗时数字不进正式报告; 限制因素结论是 render/write/parse 的固定 sleep 主导, 归一化不是瓶颈. 正式数字用 e2e 阶段中位数.
- 任务 5: 优化不是没用. 产品路径 200 行 98.56 -> 89.34 ms, 快 9.35% (p=0.0034); 含 500 ms 限流的路径 598.56 -> 589.34 ms, 快 1.54% (p=0.0034). 原脚本的 1.5% 是限流等待在计时区内造成的稀释, 不是零差异.
- 任务 6: 198/s 是 build 模式负载生成器饱和, 不是应用测量结果; prepared 模式同样 12 worker 为 980.8/s, 16 worker 为 1267.0/s. 应用侧吞吐应采信 prepared 的数字.
- 缺口: profile_run 只跑 new 200 行; flat_compare 只测 200 行, 500 ms 限流是否属于生产用户路径 lab 未给出; loadgen 只测 slow `normalize`, fast 版本的负载吞吐未测; 16 worker 压测会占满 16 核, 只用于看饱和, 不用于新旧对比.
