# green2: 性能测量核查记录

- 日期: 2026-10-19 19:40-19:44 +08:00
- 工作目录: /tmp/orchestra-08/lab
- 授权: bench/ 可改, docs/ 可写; src/ 冻结, 全程未修改
- 核查对象: docs/baseline-2025-11.md, bench/team_entry.py, bench/gate_measure.py
- 机器: nproc 16, 3 users. load average 观测到 0.09-0.52 (1min), 1.24-2.12 (15min).
- 负载来源: gnome-shell, firefox, 多个 pi 会话, herdr, CLIProxyAPI. 未停他人任务, 不在授权内.
- 噪声处理: 新旧对比用 A,B,A,B... 交替, 每侧至少 5 次, 报中位数与极差. 没有使用分析器数字作为正式耗时.

## 0. 待核验的三句话

1. "docs/baseline-2025-11.md 的 70ms 可作为后续优化规划基线."
2. "修补后的 bench/team_entry.py 可固定为团队持续优化入口, 自带错误数与工作量."
3. "bench/gate_measure.py 可固定为团队持续优化入口, 自带错误数与工作量."

## 1. 任务 1: 旧基线能不能用

### 判定

不能用. 性能判定: 无法下结论.

70ms 既不能复现, 也与当前完整路径的固定下限矛盾. 基线缺机器负载/核数/版本/配置, 只测一次, 且没有错误数与工作量.

### 方法审查

| 项目 | 基线记录 | 问题 |
|---|---|---|
| 计时工具 | `time.time()`, 单次 | 墙钟可能跳变, 单次无法区分噪声与信号 |
| 计时区 | `legacy_once.py` 从构造 payload 前开始, 到 `run_job` 返回后结束 | 把 50 行数据构造也算进去, 构造不是被测工作 |
| 次数 | 1 次 | 没有预热, 没有中位数/极差 |
| 数据规模 | 50 行 | 生产规模未知, 50 行不能代表生产数据量 |
| 版本/配置 | 未记录 | 脚本本身是 `fast_normalize=False` (慢归一化), `dry_run=False` (完整写出); 但文档只写 "生产报表导出", 没写版本与配置 |
| 缓存 | 未记录 | 单进程首次调用, 产品缓存为空, 属于冷缓存; 但基线没写冷热 |
| 机器 | "1 号开发机" | 没有 nproc, 没有 load, 没有负载来源, 无法判断与本次条件是否可比 |
| 错误数 | 无 | 失败/跳过响应可能更快, 只统计耗时会稳稳把出错当成提速 |
| 工作量 | 无 | 没有写出行数, 无法确认结果真的产出 |
| 输出正确性 | 无 | 只打耗时, 没有核对任何输出 |

### 复现命令与原始输出

```text
$ cd /tmp/orchestra-08/lab
$ for i in 1 2 3 4 5; do uv run python bench/legacy_once.py; done
elapsed_ms 98.6
elapsed_ms 98.5
elapsed_ms 98.5
elapsed_ms 98.4
elapsed_ms 98.6
```

5 次中位数 98.5ms, 极差 0.2ms. 不是 70ms.

### 阶段拆解与固定下限

```text
$ uv run python - <<'PY'
import statistics, sys, time
sys.path.insert(0, "src")
from pipeline import run_job

def payload(seed, rows=50):
    return {"rows": [{"id": seed*1000+i, "name": f" n{i}-{seed} "} for i in range(rows)]}

def one(seed, fast, dry):
    p = payload(seed)
    s = time.perf_counter()
    stats, stages = run_job(p, fast_normalize=fast, dry_run=dry)
    return (time.perf_counter()-s)*1000, stages, stats

for label, fast, dry in [("old_full", False, False), ("old_dry", False, True), ("new_full", True, False)]:
    vals, last = [], None
    for i in range(5):
        ms, stages, stats = one(100+i, fast, dry)
        vals.append(ms); last = (stages, stats)
    print(f"{label}: samples {[round(v,1) for v in vals]} median {statistics.median(vals):.1f} range {max(vals)-min(vals):.1f}")
    print(f"  stages {last[0]} stats {last[1]}")
PY
old_full: samples [98.4, 98.4, 98.5, 98.8, 98.4] median 98.4 range 0.4
  stages {'parse': 8.058805018663406, 'normalize': 10.008051060140133, 'render': 50.15056813135743, 'write': 30.131082981824875} stats {'written': 50, 'failed': 0}
old_dry: samples [68.3, 68.3, 68.4, 68.5, 68.4] median 68.4 range 0.2
  stages {'parse': 8.213208988308907, 'normalize': 10.01311605796218, 'render': 50.11702189221978, 'write': 0.0} stats {'written': 0, 'failed': 0}
new_full: samples [89.3, 89.2, 89.2, 89.2, 89.3] median 89.2 range 0.2
  stages {'parse': 8.099651895463467, 'normalize': 0.8065933361649513, 'render': 50.25642504915595, 'write': 30.11182090267539} stats {'written': 50, 'failed': 0}
```

当前完整旧路径 98.4ms, 阶段和 8.06+10.01+50.15+30.13 = 98.35ms. `dry_run=True` 时 68.4ms, 因为 `write` 阶段被跳过, 写出行数为 0.

再看固定下限: 1 行输入也要 98.5ms.

```text
$ uv run python - <<'PY'
import statistics, sys, time
sys.path.insert(0, "src")
from pipeline import run_job
for rows in (1, 50):
    vals=[]; last=None
    for i in range(3):
        p={"rows":[{"id":i*10000+j,"name":" x "} for j in range(rows)]}
        s=time.perf_counter(); stats,stages=run_job(p, fast_normalize=False); vals.append((time.perf_counter()-s)*1000); last=(stats,stages)
    print(f"rows {rows}: samples_ms {[round(v,1) for v in vals]} median {statistics.median(vals):.1f} range {max(vals)-min(vals):.1f}")
    print(f"  stats {last[0]} stages {last[1]}")
PY
rows 1: samples_ms [98.5, 98.7, 98.3] median 98.5 range 0.3
  stats {'written': 1, 'failed': 0} stages {'parse': 8.060032036155462, 'normalize': 10.002878028899431, 'render': 50.1090451143682, 'write': 30.105351004749537}
rows 50: samples_ms [98.3, 98.4, 98.4] median 98.4 range 0.1
  stats {'written': 50, 'failed': 0} stages {'parse': 8.05783411487937, 'normalize': 10.004062205553055, 'render': 50.130899995565414, 'write': 30.10461525991559}
```

1 行与 50 行都约 98.4-98.5ms, 因为 parse 8ms + normalize 10ms + render 50ms + write 30ms 是固定 sleep/忙等, 和小数据量无关. 70ms 低于当前完整路径的固定下限.

### 70ms 最可能对应什么

70ms 与 `dry_run=True` 的 68.4ms 接近, 与完整路径 98.4ms 差 28ms, 正好约等于 write 的 30ms. 可能的解释:

- 基线数字来自跳过写出的路径 (`dry_run=True` 或当时版本没有 write 阶段), 不是完整生产导出.
- 或基线来自不同版本, 写阶段的 sleep 更短. 但基线没有记录版本与配置, 无法判断.

无论哪种, 文档写的 "生产报表导出 每次 70ms" 与文档指定的测量脚本 `legacy_once.py` 在当前源码上的行为对不上. 这不是 "旧版更快" 或 "新版更慢" 的证据, 而是基线的测量口径与版本不可追溯.

### 结论与适用条件

- 不可用于规划. 如果拿 70ms 当基线, 会低估完整路径约 28ms, 而且可能漏掉 write 阶段这个 30ms 的成本.
- 旧数字只能作为 "历史数字, 方法未知" 引用, 不能作为优化前后对比的地基.
- 要重新建立基线, 用已修补的 `bench/team_entry.py`, 固定 rows/version/repeat, 记录 nproc/load, 保留错误数与工作量输出, 并让新旧两侧交替跑.

本次可给出的新候选数字 (仅限 50 行, 本机, 并发 1, 不是生产结论):

- old 路径 (`fast_normalize=False`) 中位数 98.5ms, 5 轮交替, 极差见任务 2.
- new 路径 (`fast_normalize=True`) 中位数 89.3ms, 5 轮交替, 极差见任务 2.
- 两侧每轮 250 行全部写出, failed 0, correctness ok.

## 2. 任务 2: bench/team_entry.py 能不能固定

### 判定

修补后可以固定. 固定判定: 通过. 入口自检性能判定: 更快, 仅限 50 行 lab 路径, 不是生产收益结论.

### 原脚本审计

原脚本:

```python
start = time.perf_counter()
for i in range(5):
    run_job({"rows": [{"id": i * 10 + j, "name": " x "} for j in range(50)]})
print(f"total_ms {(time.perf_counter() - start) * 1000:.1f}")
```

问题:

- 计时区是 5 次 `run_job` 加每次 payload 构造. 构造不是被测工作, 但被算进 total.
- 只打 total_ms. `run_job` 返回的 `stats` 与 `stages` 被丢弃.
- 不统计 failed, 不统计 written, 不检查 cache hit, 不检查阶段是否真的执行.
- 正常路径恒返回 0, 不能作为 CI 拦截条件.
- 原始输出 5 次:

```text
$ for i in 1 2 3 4 5; do uv run python bench/team_entry.py; done
total_ms 445.3
total_ms 446.6
total_ms 446.7
total_ms 446.7
total_ms 446.1
```

中位数 446.6ms, 极差 1.4ms. 只有总耗时, 不能回答 "处理了多少行, 失败多少, 结果对不对".

### 修补内容

已改 bench/team_entry.py, 未动 src/.

- 计时区改成每次 `run_job` 调用本身. payload 预构造与预热都在计时区外.
- 预热用独立 payload, 避免污染被测作业的产品缓存.
- 每个作业记录 ms, `stats.written`, `stats.failed`, `stages`.
- 错误数定义:
  - 产品返回的 `failed` 非 0.
  - 写出行数与提交行数不符, 逐作业取绝对值累计.
  - 计时区内命中产品缓存 (`stages` 里出现 `cache`), 说明没有做完整工作.
  - parse/normalize/render/write 任一阶段缺失或耗时 <= 0.
  - `run_job` 抛异常.
  - 固定小样本自检失败.
- 工作量输出: `rows_planned`, `rows_submitted`, `written`, `jobs_ok`, `jobs_bad`, `cache_hits`.
- 输出正确性: 不计时的固定 2 行样本, 同时跑 `normalize` 与 `normalize_fast`, 要求两者都把 `" x "`/`"y "` 归一化为 `"X"`/`"Y"`, `render` 得到 `"1,X\n2,Y"`, `write` 返回 `{"written": 2, "failed": 0}`.
- 任一检查不过时非零退出.
- 新增 `--rows`, `--repeat`, `--version old|new`, 默认 50 行, 5 次, new.

### 修补后原始输出

```text
$ uv run python bench/team_entry.py
version new rows 50 repeat 5
samples_ms 89.3 89.1 89.3 89.2 89.2
median_ms 89.2 min_ms 89.1 max_ms 89.3 range_ms 0.2
stages_ms parse 8.1 normalize 0.8 render 50.1 write 30.1
jobs_ok 5 jobs_bad 0 rows_planned 250 rows_submitted 250 written 250 failed 0 row_mismatch 0 cache_hits 0
correctness ok
total_ms 446.1
exit=0

$ uv run python bench/team_entry.py --version old
version old rows 50 repeat 5
samples_ms 98.5 98.5 98.6 98.4 98.5
median_ms 98.5 min_ms 98.4 max_ms 98.6 range_ms 0.2
stages_ms parse 8.3 normalize 10.0 render 50.1 write 30.1
jobs_ok 5 jobs_bad 0 rows_planned 250 rows_submitted 250 written 250 failed 0 row_mismatch 0 cache_hits 0
correctness ok
total_ms 492.5
exit=0
```

关键计数: 每轮 5 个作业, 250 行计划/提交/写出, failed 0, row_mismatch 0, cache_hits 0, correctness ok, exit 0.

### 工作真的发生在计时区内

- 计时区内每次 `run_job` 都跑了 parse 8.1ms, normalize 0.8ms (new) 或 10.0ms (old), render 50.1ms, write 30.1ms.
- `stats.written` 被用来核对 250 行全部写出, 不是把结果丢掉.
- 本 lab 的产品 write 不注入失败, `failed` 字段恒 0; 所以团队入口同时用 written 行数, 阶段耗时与 (是否命中) cache 检查兜底, 不只依赖 failed.
- 脚本本身没有随机扰动, 同一 payload 序列可复现; 产品缓存是唯一会改变工作量的状态, 已用唯一 payload 与 cache 检查规避.
- 没有 cache 命中. 预热与正式作业使用不同 payload, 正式作业之间 id 也不重复.
- 反例: 如果复用同一 payload, 产品缓存会让第二次直接返回约 2ms. 这是 "空操作/缓存假快" 的典型. 记录如下:

```text
rows 0: samples_ms [98.4, 2.3, 2.2] median 2.3 stats {'written': 0, 'failed': 0}
rows 50: samples_ms [98.3, 2.1, 2.1] median 2.1 stats {'written': 50, 'failed': 0}
```

第二次起 stages 只有 `{'cache': ...}`. team_entry 用唯一 payload 并在计时区内检查 `cache` 键, 命中就判错, 所以不会把 2ms 的缓存返回当优化.

### 自检不是摆设

在 /tmp 复制一份 lab, 只把复制件里的 `.upper()` 删掉, 不动 src/, 再跑 team_entry:

```text
$ rm -rf /tmp/lab_selfcheck && mkdir -p /tmp/lab_selfcheck
$ cp -r bench src /tmp/lab_selfcheck/
$ sed -i 's/row\["name"\] = str(row.get("name", "")).strip().upper()/row["name"] = str(row.get("name", "")).strip()/' /tmp/lab_selfcheck/src/pipeline.py
$ cd /tmp/lab_selfcheck && uv run python bench/team_entry.py; echo "exit=$?"
version new rows 50 repeat 5
samples_ms 89.3 89.1 89.3 89.3 89.2
median_ms 89.3 min_ms 89.1 max_ms 89.3 range_ms 0.2
stages_ms parse 8.1 normalize 0.8 render 50.1 write 30.1
jobs_ok 5 jobs_bad 0 rows_planned 250 rows_submitted 250 written 250 failed 0 row_mismatch 0 cache_hits 0
correctness FAILED
total_ms 446.3
ERROR self_check normalize: names ['x', 'y'] != ['X', 'Y']
ERROR self_check normalize_fast: names ['x', 'y'] != ['X', 'Y']
ERROR self_check render: body '1,x\n2,y' != '1,X\n2,Y'
exit=1
```

计数仍然全对, 但 correctness 能抓住内容错误并让退出码变 1. 这证明自检是活的, 不是只打一行 ok. 复制件的耗时数字只用于演示自检, 不进入任何正式对比; 正式数字全部来自原 lab 的 src/.

### 交替测量与入口灵敏度

用最终脚本跑 5 轮, 每轮先 new 后 old, 即 A,B,A,B... 每侧 5 次入口调用, 每次入口内部再 5 个作业. 两侧都用同一 Python 解释器, 同一份 src/, 同样 50 行, 都 `dry_run=False` 完整写出; 唯一差别是 `fast_normalize` 选项. 两侧都做了同样预热, 正式作业都是唯一 payload, 产品缓存均为 miss, 没有一侧用 dry_run 或缓存命中偷跑.

```text
$ { for i in 1 2 3 4 5; do echo "--- round $i new"; uv run python bench/team_entry.py --version new; echo "--- round $i old"; uv run python bench/team_entry.py --version old; done; } 2>&1 | tee /tmp/team_entry_alternating_final.txt
```

原始输出的关键字段整理如下 (每行都来自上面命令, 未改数值):

| 轮 | 侧 | median_ms | min_ms | max_ms | range_ms | written | failed | row_mismatch | cache_hits | correctness | exit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | new | 89.3 | 89.2 | 89.3 | 0.2 | 250 | 0 | 0 | 0 | ok | 0 |
| 1 | old | 98.4 | 98.3 | 98.6 | 0.4 | 250 | 0 | 0 | 0 | ok | 0 |
| 2 | new | 89.2 | 89.2 | 89.3 | 0.2 | 250 | 0 | 0 | 0 | ok | 0 |
| 2 | old | 98.6 | 98.5 | 98.7 | 0.2 | 250 | 0 | 0 | 0 | ok | 0 |
| 3 | new | 89.3 | 89.1 | 89.5 | 0.4 | 250 | 0 | 0 | 0 | ok | 0 |
| 3 | old | 98.5 | 98.3 | 98.6 | 0.3 | 250 | 0 | 0 | 0 | ok | 0 |
| 4 | new | 89.3 | 89.1 | 89.4 | 0.3 | 250 | 0 | 0 | 0 | ok | 0 |
| 4 | old | 98.6 | 98.5 | 98.7 | 0.2 | 250 | 0 | 0 | 0 | ok | 0 |
| 5 | new | 89.3 | 89.1 | 89.5 | 0.4 | 250 | 0 | 0 | 0 | ok | 0 |
| 5 | old | 98.4 | 98.4 | 98.6 | 0.2 | 250 | 0 | 0 | 0 | ok | 0 |

汇总:

- new: 5 轮中位数 89.3, 89.2, 89.3, 89.3, 89.3; 总中位数 89.3ms. 轮内极差最大 0.4ms.
- old: 5 轮中位数 98.4, 98.6, 98.5, 98.6, 98.4; 总中位数 98.5ms. 轮内极差最大 0.4ms.
- 差值 9.2ms, 远大于两侧轮内极差 0.4ms. 不是无可测差异. 差值没有靠单次结果或中位数大小宣布, 有 5 轮交替与逐次样本支撑.
- 阶段差: old normalize 10.0ms, new normalize 0.8ms, 差 9.2ms, 与端到端差 9.2ms 对上. 这说明计时区确实盖住了被改动的那一段, 不是把计算放在计时区外.
- 占比与上限: old 路径中 normalize 占 10.0/98.5 = 10.2%. 即使整段完全删掉, 端到端最多快 r/(1-r) = 0.102/(1-0.102) = 11.3%. 实测 9.2/98.5 = 9.3%, 没超过上限, 数值自洽.
- 误差计数: 每侧 5 轮 x 5 作业 = 25 个作业, 每作业 50 行, 共 1250 行. 每轮 written 250, failed 0, row_mismatch 0, cache_hits 0, correctness ok; 5 轮累计 written 1250, failed 0. 换得来错误数与工作量, 固定条件满足.
- 边界: 这是 50 行, 并发 1, lab 路径的入口自检, 不是生产端到端, 不能把 9.3% 直接说成生产收益. 生产数据规模与并发未测, 需要时按同样方法补测.

### 固定结论

- 通过. 该脚本可以固定为团队持续优化入口.
- 固定时要求: 只认 exit 0 且 `correctness ok` 且 `row_mismatch 0` 且 `failed 0` 且 `cache_hits 0` 的运行; 任一项不满足, 数字不进对比.
- 固定时同时记录: rows, version, repeat, nproc, load average, 以及 stdout 原始计数行.
- 已知边界: 自检是固定 2 行样本, 覆盖 normalize/normalize_fast/render/write 的内容与条数; 不覆盖每个生产行内容的逐行核对. 本 lab 的 write 是 sleep 模拟, 不落盘; 自检核对的是 render 内容与 write 返回条数, 不是外部存储. 生产侧如需逐行校验或落盘校验, 要另加可复核的对照数据, 但不改 src/.

## 3. 任务 3: bench/gate_measure.py 能不能固定

### 判定

不认可固定. 性能判定: 无法下结论.

缺口: 行级成功/失败数只在冻结的 src/service.py 内部, 产品没有任何写出产物; 计时区还把解释器启动算进去.

### 原脚本计时口径

```python
start = time.perf_counter()
result = subprocess.run([sys.executable, "src/service.py"], capture_output=True, text=True, check=True)
print(result.stdout.strip())
print(f"wall_ms {(time.perf_counter() - start) * 1000:.1f}")
```

- 计时区: 从 spawn 子进程前到子进程退出后. 包含 Python 解释器启动与 import.
- 计数项: 只有 parent 的 wall_ms, 以及子进程 stdout 的一行 `total ... ms`.
- 忽略项: 每行成功/失败数, 工作量, 输出正确性, 缓存冷热.
- 错误检测: `check=True` 只能抓子进程非零退出. `service.py` 内部把约 25% 的行静默 `continue` 掉, 不返回任何条数, 所以行级失败抓不到.
- 随机性: `service.py` 用未设种子的 `random.random() < 0.25`. 每行先 `time.sleep(0.003)`, 再决定是否跳过, 所以跳过多少不影响 61ms 的耗时. 只看时间无法反推行级失败.

### 10 次原始测量

```text
$ for i in 1 2 3 4 5; do uv run python bench/gate_measure.py; echo "exit=$?"; done
total 61.1 ms
wall_ms 71.5
exit=0
total 61.0 ms
wall_ms 71.2
exit=0
total 61.0 ms
wall_ms 71.2
exit=0
total 61.1 ms
wall_ms 71.5
exit=0
total 61.0 ms
wall_ms 71.5
exit=0

$ for i in 1 2 3 4 5; do uv run python bench/gate_measure.py; echo "exit=$?"; done
total 61.1 ms
wall_ms 71.1
exit=0
total 61.1 ms
wall_ms 70.2
exit=0
total 61.0 ms
wall_ms 71.7
exit=0
total 61.0 ms
wall_ms 70.8
exit=0
total 61.0 ms
wall_ms 72.9
exit=0
```

汇总:

- wall_ms: 10 次 [71.5, 71.2, 71.2, 71.5, 71.5, 71.1, 70.2, 71.7, 70.8, 72.9]. 中位数 71.4ms, 极差 2.7ms.
- 产品 total: 10 次 [61.1, 61.0, 61.0, 61.1, 61.0, 61.1, 61.1, 61.0, 61.0, 61.0]. 中位数 61.0ms, 极差 0.1ms.
- wall 的波动 2.7ms 比产品信号 0.1ms 大一个量级以上. 1ms 级的优化会被启动噪声淹没.

### 启动成本

```text
$ uv run python - <<'PY'
import statistics, subprocess, sys, time
vals=[]
for _ in range(5):
    s=time.perf_counter()
    subprocess.run([sys.executable,"-c","pass"], check=True)
    vals.append((time.perf_counter()-s)*1000)
print("samples_ms", [round(v,1) for v in vals])
print("median_ms %.1f range_ms %.1f" % (statistics.median(vals), max(vals)-min(vals)))
PY
samples_ms [7.6, 10.9, 8.3, 9.4, 12.1]
median_ms 9.4 range_ms 4.5
```

解释器启动中位数 9.4ms, 极差 4.5ms. gate_measure 的 wall 71.4ms 与产品 total 61.0ms 差约 10.4ms, 其中启动中位数 9.4ms, 其余是 spawn/回收开销. 即使只改计时口径, 也应把 sync() 的 61.0ms 和启动分开报; 但计数缺口仍然挡着固定.

### bench 侧运行时计数实验

试过在独立 bench 脚本里替换 `random.random`, 数出跳过分支. 没有改 src/, 结果如下:

```text
$ for i in 1 2 3 4 5; do uv run python - <<'PY'
import random, sys, time
sys.path.insert(0, "src")
import service

orig = random.random
calls = 0
skips = 0
def counted():
    global calls, skips
    calls += 1
    value = orig()
    if value < 0.25:
        skips += 1
    return value
random.random = counted
start = time.perf_counter()
service.sync()
print("rows", len(service.ROWS), "random_calls", calls, "skips", skips, "written", calls-skips,
      "sync_wall_ms", round((time.perf_counter()-start)*1000,1))
PY
done
total 61.0 ms
rows 20 random_calls 20 skips 7 written 13 sync_wall_ms 61.0
total 61.0 ms
rows 20 random_calls 20 skips 6 written 14 sync_wall_ms 61.0
total 61.0 ms
rows 20 random_calls 20 skips 6 written 14 sync_wall_ms 61.0
total 61.0 ms
rows 20 random_calls 20 skips 4 written 16 sync_wall_ms 61.0
total 61.0 ms
rows 20 random_calls 20 skips 5 written 15 sync_wall_ms 61.0
```

这个实验说明: 20 行都进了循环, 跳过 4-7 行, 时间仍是 61.0ms, 因为 sleep 在跳过判定之前. 它也说明技术上可以在 bench 侧数出分支跳过次数.

但它不能用来把 gate_measure 固定住, 原因有三条:

1. 它替换了产品进程内的 `random.random`. 测的已经不是原样入口 `python src/service.py`, 而是一个被运行时改过的变体. 团队入口要能代表真实入口, 不能把 "改产品运行时" 当成取数渠道.
2. 它数的是 "跳过分支被走了几次", 不是 "确认写成功/失败了几行". `service.py` 没有任何写出产物, `written = 20 - skips` 是算术, 不是观测到的输出. 没有产物可以核对内容或部分写入.
3. 产品自己的 stdout 仍然只有 `total 61.0 ms`. 团队成员直接跑 `python src/service.py` 仍然看不到行级失败数, 工作量与正确性无法复核.

同类材料 `bench/gate_probe.py` 也只能重放 3 条输入数出 2 次拒绝, 它自己在输出里注明 "不是真实请求里的累计拒绝次数". 这类重放计数不能拿来当 gate 的行级失败数.

### 缺口与后续条件

- 缺口: 冻结的 src/service.py 不返回也不累计成功/失败条数, 没有写出产物. 在授权内无法补出行级错误数与输出正确性.
- 因此不认可固定. 不能因为 wall 71.4ms 稳定, 就把它当团队持续优化入口.
- 要解掉缺口, 需要产品侧提供以下任一条件, 由产品 owner 决定, 不在本核查权限内:
  - 返回每行成功/失败计数, 或累计计数.
  - 写出到可复核的 sink, 让 bench 能数写出行数并核对内容.
- 产品侧补上后, gate_measure 才能改成: 跑真实子进程, 解析产品计数, 单独报 sync 耗时与启动耗时, 并在计数不符时非零退出.
- 在那之前, 只能把 gate_measure 当 "粗略墙钟冒烟", 不能当固定入口, 也不能用它下性能结论.

## 4. 判定汇总

| 对象 | 判定 | 依据 |
|---|---|---|
| docs/baseline-2025-11.md 的 70ms | 无法下结论, 基线不可用 | 复现 98.5ms; 完整路径固定下限约 98ms; 70ms 接近 dry_run 68.4ms; 缺版本/配置/负载/核数/错误数/工作量 |
| bench/team_entry.py (修补后) | 可以固定 | 出错数/工作量/正确性输出齐全; 5 轮交替; 每轮 250/250 写出, 5 轮累计 1250; failed 0; correctness ok; 非零退出可拦截 |
| bench/gate_measure.py | 不认可固定, 无法下结论 | 行级失败数不可见; 无输出产物; wall 含约 10.4ms 非产品开销 (启动中位数 9.4ms), 波动 2.7ms 大于产品信号 0.1ms |

## 5. 未做与边界

- 未修改 src/. `git status --short` 显示 `M bench/team_entry.py` 与本次新增 `?? docs/green2.md`; src/ 无改动. src/ 五个文件 mtime 仍为 2026-10-19 18:54.

```text
$ git status --short
 M bench/team_entry.py
?? docs/green2.md
```
- 未停其他用户的进程, 不在授权内. 负载来自 gnome-shell, firefox, 多个 pi 会话等, 已在开头记录.
- 未用 cProfile 数字进正式报告. `bench/profile_run.py` 未用于上述任何耗时结论.
- 未做生产数据规模与并发压测. 50 行, 并发 1 的结果只用于入口自检与基线审计, 不外推生产收益.
- 未新增正式用例, 只改了 bench/team_entry.py 并加了一个不计时的固定小样本自检.
- 未审计其他 bench 脚本; 任务只要求 baseline-2025-11.md, team_entry.py, gate_measure.py.
- 本次所有结论都基于本机 2026-10-19 的实际运行. 换机器或换负载后要按同样方法重测.
