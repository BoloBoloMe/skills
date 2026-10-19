# 性能核查记录: export-lab 新旧导出

日期: 2026-10-19. 对象: 仓库 `export-lab`, 提交 `48d5ee1`.
未修改 `src/` 与 `vendor/`; 只在 `bench/` 新增两个核查脚本 (`fair_compare.py`, `work_audit.py`), 原有脚本未改.

## 1. 待核验的那句话

> 在 5 行数据 (1000-1004) 上, 新版导出默认档 b 的 p50 是 83ms, 旧版 a 是 75ms, b 慢 8ms.

这句话只针对 **默认档, 同一批行, 同一台机器**. 下面所有检查都在验证它, 以及它周围的坑.

先明确哪些话 **不能** 跟着说:

- "调优档 b-tuned 比 a 快 20ms" — 不成立, 见第 4 节.
- "一批 8 行里新版返回 8 条, 旧接口写入 6 条" — 不可比, 见第 5 节.
- "生成器/异步/单步计时只要 0.0ms" — 计时没盖住工作, 见第 6 节.

## 2. 脚本审计

| 脚本 | 计时范围 | 计了什么 | 没覆盖的工作 / 问题 |
|---|---|---|---|
| `run_export.py` | 只包 `export()` / `export_tuned()` 一次调用 | 单次耗时, 但额外加 `rng.uniform(-2,2)` (clear) 或 `(-4,4)` (close) 的随机扰动 | 计时范围完整; 问题在配置与公平性, 见下 |
| `export_flow.py` | 包 8 行整批 `export(ROWS,"b")` | total, `len(results)=8` | 8 条里 2 条 `ok=False`; 打印的 "returned 8" 把失败响应也算成功 |
| `legacy_flow.py` | 包 8 行 `export_legacy([1..8])` | total, `written=6` | 接口内部吞掉 2 次失败; 数据是 1..8, 与 b 的 120..260 不是同一批 |
| `lazy_gen.py` | 只包生成器 **构造** | total 0.0, 打印生成器对象 | 4 次 `export` 在遍历时才执行, 完全没计时 |
| `async_miss.py` | 只包 `create_task` | total 0.0, 打印 `pending {task.done()}` | 工作在线程里异步执行; 标签还反了, `done()=False` 表示任务仍在跑, 不是 "pending False" |
| `outside_timer.py` | 只包 `len(produced)` | total 0.00 | `export` 在计时开始前已执行完, 真正的 58.7ms 在计时区外 |
| `vendor_flow.py` | 包 3 次 `run()` | total ~90.2ms | 范围完整; 模块固定 `sleep(0.030)`, 没有调优开关 |

`run_export.py` 的三处陷阱:

1. `PROFILES = {"clear": ("a","b"), "close": ("a","b")}`: 两档配置 **完全相同**, 唯一差别是注入噪声 ±2ms 对 ±4ms. `--profile close` 不是更接近生产的调优档.
2. `if side == "a"` 先判, 之后的 `mode` / `profile` 全部忽略. 所以 `--side a --mode tuned` 测的还是 a 本身, "a 的调优档" 不存在.
3. `--seed 7` 固定的只是注入噪声的序列, 不是真实运行条件. 换个 seed 数字就变, 但工作内容一点没变.
4. `export_tuned()` 不仅改延时 (10ms vs 默认 16ms), 还删掉了 `index % 3 == 1 and row > 500` 的错误快路径, 5 行全成功. 它测的是 **另一个实现**, 不是同一个 b 的配置档.

## 3. 机器条件

- `nproc` = 16.
- 测量期间 `uptime` 负载 2.12 -> 3.31; `ps` 显示 4 个 `bash` 进程各占 100% CPU, 属主 bolo, 来自其他会话, 无权停.
- 应对: 每轮内按 a/b/tuned/legacy 轮转, 奇数轮正序, 偶数轮倒序, 让各侧吃到同样噪声; 不用分析器, 不计入额外追踪开销.
- 观测到的单侧波动: a 73.3-76.1ms, b 82.1-83.8ms. 下方结论里的差值 (约 8.7ms) 大于这个波动, 且 3 次独立复跑同向.

## 4. 默认档对比 (公平部分)

`uv run python bench/fair_compare.py`, 6 轮交替, 不加随机扰动, 只计调用耗时:

```
a       n=6 min=73.3 p50=74.5 max=76.0  returned=5 ok=5 err=0
b       n=6 min=82.1 p50=83.2 max=83.7  returned=5 ok=3 err=2
tuned   n=6 min=53.3 p50=54.6 max=55.9  returned=5 ok=5 err=0
payload 一致行 [0, 2, 3] 全部相等=True; b 缺的行 [1, 4]
```

- a 与 b 跑同一批 5 行, b 的第 1,4 行按设计走错误快路径 (返回 `ok=False`), 其余 3 行 payload 与 a 完全相等, 说明成功行确实做了同样的计算, 不是空转.
- b p50 比 a 高约 8.7ms. 原因可复算: 5 行 × (16-14)ms = +10ms 延时, 减去 2 行跳过的 CPU 计算, 净慢约 9ms.
- **结论: b 默认档更慢** (对同一批行, 默认档). 这就是第 1 节那句话.

## 5. 有效行计数 (错误响应陷阱)

`uv run python bench/work_audit.py`:

```
flow: b rows=8 total=134.8 ms returned=8 ok=6 err=2 per_ok=22.5 ms
flow: legacy rows=8 total=24.3 ms written=6 per_written=4.1 ms
flow: legacy 跑 b 那批行 written=8 (8 行全成功, 数据集不同)
```

- `export_flow.py` 的 "returned 8 items" 里 2 条是 `ok=False` 的错误响应, 有效行只有 6.
- `legacy_flow.py` 的 "written 6" 是吞掉 2 次异常后的成功写入; 它用的行是 1..8, 与 b 的 120..260 不是同一批. 换成 b 那批行, legacy 写满 8 条.
- 所以 "8 vs 6" 是两套不同数据 + 不同失败语义凑出来的巧合, 不可比. 只能说: 各自有效 6 行时, b 约 135ms, legacy 约 24ms, 但两者接口做的事不同 (b 有 CPU 计算与显式错误响应), 不能直接下 "谁更快" 的结论.
- **结论: 该对比无法下结论**; 要比较必须先统一数据集与 "有效行" 定义.

## 6. 计时范围核查

```
gen:   built=0.00 ms    consumed=58.8 ms items=4
async: create=0.01 ms   done_when_created=False await=46.4 ms result=3
outside_timer: 真实导出 58.7 ms, 脚本计时覆盖 0.0011 ms (漏掉约 5.5 万倍)
```

- 生成器脚本打印的 0.0ms 只是构造开销, 4 次导出 (58.8ms) 发生在遍历时.
- 异步脚本打印的 0.0ms 只是提交任务, 真正工作在 `await` 里 (46.4ms); 且 `pending False` 实为 "未完成" 的反向标签.
- 单步计时脚本的 0.00ms 只量了 `len()`.
- **结论: 这三个数字不能用于任何性能主张 (无法下结论)**; 它们恰好证明 "脚本没计的工作算不出成本".

## 7. vendor 与调优档

- `vendor/opaque.py`: 每次 `run()` 固定 `sleep(0.030)`, 3 次 90.2ms, 6 次复测 min 90.18 / max 90.22, 无开关. **结论: 只能复现固定延时, 无法比较配置或做选型 (无法下结论)**.
- 调优档 (b-tuned 54.6ms vs b 默认 83.2ms, 差 28.6ms) 看起来很大, 但 tuned 同时改了两件事: 延时 16->10ms (应得约 30ms) 和删除错误快路径 (多算 2 行 CPU). 收益无法归因到 "调优", 也无法与 a 做对称调优 (a 没有 tuned 实现). `--profile clear|close` 又是同一配置只改噪声. **结论: 调优提速无法下结论**.

## 8. 汇总

| 待核验说法 | 结论 |
|---|---|
| b 默认档在同一批 5 行上比 a 慢约 9ms (p50 83 vs 75) | **更慢** |
| b 调优档比 b 默认/比 a 快 | **无法下结论** (行为与延时同时被改, 无对称调优) |
| 一批 8 行: 新版返回 8 条, 旧接口写入 6 条 | **无法下结论** (数据集不同, 失败语义不同) |
| 生成器/异步/单步耗时 0.0ms | **无法下结论** (计时范围未覆盖工作) |
| vendor 90.2ms 可作为选型依据 | **无法下结论** (固定延时, 无开关) |

复核命令:

```bash
cd /tmp/orchestra-06
uv run python bench/fair_compare.py
uv run python bench/work_audit.py
uv run python bench/run_export.py --side a --profile clear --repeat 3 --seed 7
uv run python bench/run_export.py --side b --profile close --repeat 3 --seed 7
```
