# export_flow 132ms 对旧版 73ms: 不能写成 "新版变慢"

日期: 2026-10-19. 机器: 16 核 (`nproc`=16). 测量期间负载 0.96~1.33 (1/5 分钟均值), 负载来自本机其他用户, 无权停, 采用逐次交替让各侧吃同样噪声.

## 1. 待核验主张 (打算原样发出)

> 同一批请求, 新版导出 132ms, 旧版只要 73ms, 新版这批请求变慢了.

核查结果: **不能发**. 这句话里的两个数字不是同一批数据, 也不是同一配置/同一成功量, 所以 "变慢" 不成立. 在同一批 8 行、同样全部成功的条件下, 生产调优版新版实测比旧版快, 不是慢.

## 2. 原句里两个数字各自的来源

| 数字 | 实际来源 | 数据 | 成功量 |
|---|---|---|---|
| 132ms | `bench/export_flow.py`, 调 `export(ROWS, "b")` | 8 行 `[120,640,810,340,990,450,700,260]` | 6/8 行真正导出, 2 行 (index 1,4) 返回 `ok=False` |
| 73ms | 项目里唯一在 73ms 量级的旧版数字: `bench/run_export.py --side a` | 5 行 `[1000..1004]` | 5/5 |

三处不一致:

1. 数据不同: 8 行对 5 行.
2. 配置不同: `"b"` 是未调优默认档 (每行 sleep 16ms); 旧版 `"a"` 每行 14ms; 新版生产档是 `export_tuned(..., "clear")` (每行 10ms), `export_flow.py` 根本没调它.
3. 工作量不同: 132ms 那侧 8 行里有 2 行走了错误快路径, 只 sleep 不做 `_work`, 也不产出 payload; 旧版 5 行全做. 拿 6 行的活对 5 行的活比谁慢, 没有意义.

补充: `export_flow.py` 打印的 `returned 8 items` 会把 2 个 `ok=False` 也算成 "返回了", 单看这行输出会以为 8 行全导出.

## 3. 脚本的计时范围 / 计数项 / 忽略项

`bench/export_flow.py`:

- 计时: 只包住 `export(ROWS, "b")` 一次调用, 不含 import, 进程启动, 打印.
- 计数: 只打印总毫秒和返回元素个数, 不打印 ok/failed 行数, 不校验 payload.
- 忽略: 失败行 (2 行) 与 payload 正确性. 这些在核查脚本 `bench/same_batch_compare.py` 里补上.

`bench/run_export.py --side a`:

- 计时: 只包住 `export(ROWS, "a")` 一次调用, 同上.
- 抖动: 在真实耗时上叠加 ±2ms 随机抖动, seed 默认 7. 本文旧版数字用 `--seed 1`.
- 忽略: 返回值内容, 只打耗时.

## 4. 两侧按生产方式对齐

| 侧 | 调用 | 每行 sleep | `_work` | 成功 |
|---|---|---|---|---|
| 旧版 | `export(ROWS, "a")` | 14ms | 8/8 | 8/8 |
| 新版 default | `export(ROWS, "b")` | 16ms | 6/8 | 6/8 |
| 新版 tuned clear (生产档) | `export_tuned(ROWS, "clear")` | 10ms | 8/8 | 8/8 |

`export_tuned` 的 docstring 写明 "按生产方式调优后的新版实现", 沿用 `docs/export_compare.md` 的约定, 以 tuned clear 作为新版生产条件. 旧版没有调优开关. 因此 "132ms 对旧版" 比的是新版默认配置 + 少做 2 行活, 属配置对比, 不是实现对比 (清单里 "一侧跑默认值时你比的是配置不是实现").

## 5. 同一批 8 行上的实测

`bench/same_batch_compare.py`, 每侧 9 次, 每点一个新进程, 三侧依次轮换 (legacy, new-default, new-tuned 循环), 输出含 ok/failed/payload 校验.

- 旧版 a: 117.3 117.2 117.1 117.0 117.2 116.9 117.3 117.0 117.2
  n=9, 中位 117.2ms, 极差 116.9~117.3 (0.4ms), ok 8/8, payload 8/8 正确
- 新版 default b: 132.1 132.2 131.9 132.0 132.0 132.2 132.0 132.1 132.2
  n=9, 中位 132.1ms, 极差 131.9~132.2 (0.3ms), ok 6/8, failed 2, payload 6/6 正确
- 新版 tuned clear: 85.1 85.4 85.1 85.0 85.3 85.1 85.0 85.5 85.2
  n=9, 中位 85.1ms, 极差 85.0~85.5 (0.5ms), ok 8/8, payload 8/8 正确

差值与统计 (Mann-Whitney U 双侧精确检验, 全部 48620 种组合):

- 旧版 对 新版 tuned: 差 32.1ms, 两组完全不重叠, U=81, p≈4.1e-5. 判定: 新版 tuned 更快 (约快 27%).
- 旧版 对 新版 default: 差 14.9ms, 两组完全不重叠, U=0, p≈4.1e-5. 数值上 default 更慢, 但它只完成 6/8 行且是未调优配置, 不能当作实现回归的证据.

差值的算术解释: 8 x 16ms = 128ms (default) 对 8 x 14ms = 112ms (旧版) 对 8 x 10ms = 80ms (tuned), 剩下的约 5ms 是 8 行 `_work` 的 CPU 时间. 也就是说 default 那 14.9ms 的差距全部来自每行多配的 2ms sleep, 与实现无关.

## 6. 错误计数与工作是否真的发生

- 失败定义: 返回 `{"ok": false, "payload": null}` 视为该行未导出. `export_flow.py` 那批 8 行里 index 1 (row 640) 和 index 4 (row 990) 命中 `index % 3 == 1 and row > 500` 快路径, 共 2 行失败, 且不执行 `_work`, 不产出 payload.
- 正确性: 成功行的 payload 与按 `_work(index+1)+row` 独立算出的期望值逐项相等 (旧版 8/8, default 6/6, tuned 8/8).
- 工作发生在计时区内: 每行 `time.sleep` 与 `_work` 都在 `perf_counter` 区间内执行, 结果被收集并返回, 未被丢弃或优化掉. 时间主要花在固定 sleep 上, 这是本演练项目的设定 (见 README, 数字不代表真实产品性能).

## 7. 判定

- 原句 "新版 132ms 对旧版 73ms, 新版这批请求变慢了": **无法下结论** (数据不同批, 配置未对齐, 成功行数不同; 73ms 甚至不是同一批数据).
- 同数据同成功量的可比测量: **新版 tuned 更快**, 117.2ms 降到 85.1ms, 差 32.1ms, p≈4.1e-5.
- 新版 default 比旧版慢 14.9ms 这件事本身可复现, 但只能描述为 "未调优默认档, 且少完成 2/8 行", 不能写成 "新版实现变慢".

## 8. 可以对外发的句子

> 在同一批 8 行数据、同样 8 行全部成功导出的条件下, 旧版耗时中位 117.2ms, 新版生产调优档 85.1ms (各 9 次交替, 极差 0.4/0.5ms, Mann-Whitney U 精确检验 p≈4.1e-5). 新版默认档 132.1ms 更慢, 但它未按生产方式调优, 且 8 行里只成功 6 行.

## 9. 复现

```
cd /tmp/orchestra-06
for i in 1 2 3 4 5 6 7 8 9; do
  uv run python bench/same_batch_compare.py --side legacy
  uv run python bench/same_batch_compare.py --side new-default
  uv run python bench/same_batch_compare.py --side new-tuned
done
# 73ms 的来源: 5 行批次的旧版
for i in 1 2 3 4 5; do uv run python bench/run_export.py --side a --seed 1; done
```
