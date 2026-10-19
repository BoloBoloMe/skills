# run_export.py: 新旧导出版本对比记录

日期: 2026-10-19. 机器: 16 核 (`nproc`=16), 负载 5 分钟均值 1.05~3.41, 负载来自本机其他用户, 无权停; 采用逐次交替 A/B 让两侧吃同样噪声.

## 1. 待对外主张 (先写, 后验证)

> 同一批 5 行数据, 导出 p50 从旧版 72.4ms 降到新版 52.7ms (约降 27%), 9 次交替测量, 差距远大于波动.

对象: `src/exporter.py` 的旧实现 `export(rows, "a")` 对新实现生产调优档 `export_tuned(rows, "clear")`.
单位: 每次导出的墙钟毫秒 (ms). 数据: `ROWS = [1000..1004]`, 5 行.

## 2. 脚本的计时范围 / 计数项 / 忽略项

`bench/run_export.py` 的 `measure()`:

- 计时: 只包住 `export(...)` 或 `export_tuned(...)` 一次调用, 不含 import, 进程启动, 打印.
- 计数: 每次调用输出一个总毫秒数; 不输出行数, 成功行数, 错误数.
- 忽略: 返回值是否完整; 默认档 `export(rows, "b")` 会在 index 1/4 提前返回 `ok=False`, 5 行里有 2 行跳过 `_work`, 工作量少算.
- 人工扰动: 脚本在真实耗时上叠加随机抖动. 当前版 clear 档 ±2ms, close 档 ±4ms; 旧版两档都是 ±2ms.
- 种子: `--seed` 默认 7, 同一进程多次重复共用一串随机数; 本次每次新进程且 seed 取 1..9.

## 3. 两侧条件 (按生产方式对齐)

| 侧 | 调用 | 每行 sleep | `_work` | 返回 ok |
|---|---|---|---|---|
| 旧版 | `export(ROWS, "a")` | 14ms | 5/5 行 | 5/5 |
| 新版 default | `export(ROWS, "b")` | 16ms | 3/5 行 (2 行错误快路径) | 3/5 |
| 新版 tuned clear | `export_tuned(ROWS, "clear")` | 10ms | 5/5 行 | 5/5 |
| 新版 tuned close | `export_tuned(ROWS, "close")` | 12.5ms | 5/5 行 | 5/5 |

`export_tuned` 的 docstring 写明 "按生产方式调优后的新版实现", 故以 tuned 档作为新版生产条件; 旧版无可调项. 新版 default 档既不是生产档, 又少做 2/5 的活并丢 2 行结果, 不能进入对比. 两侧 payload 表达式一致 (`_work(index+1)+row`), tuned 与旧版结果逐项相同.

## 4. 测量序列与结果

逐次交替, 每个点一个新进程, seed 依次 1..9 (一次配对):

- 旧版 (a): 72.1 75.2 72.4 72.3 73.7 74.3 72.4 72.2 73.2
  n=9, 中位数 72.4ms, 极差 72.1~75.2 (3.1ms)
- 新版 tuned clear: 52.0 55.2 52.3 52.2 53.6 54.6 52.7 52.2 53.2
  n=9, 中位数 52.7ms, 极差 52.0~55.2 (3.2ms)

差距 19.7ms, 大于两侧极差; 两组 9 个值完全不重叠. Mann-Whitney U 双侧精确检验 U=0, p≈4.1e-5. 判定: 新版更快.

敏感性 (tuned close, 同样 9 次交替): 旧版中位 72.4ms (71.8~75.0), 新版中位 64.5ms (62.7~69.4), 仍完全不重叠 (p≈4.1e-5). 新版即使在较保守的 close 档也更快, 幅度约 11%.

## 5. 不能拿来下结论的数字

- 新版 default: 81.1ms (80.5~84.0, n=3), 比旧版慢; 但它只成功导出 3/5 行, 且 sleep 16ms 是未调优默认值, 不是同工作量同生产配置, 不构成 "新版更慢" 的证据.
- `run_export.py` 自身新旧两版 (48cec44 vs HEAD) 的 diff 只改了抖动幅度 (±2 统一 → close 档 ±4), 不改被测代码; 同 seed 下 clear 档输出 72.5ms 对 72.4ms, 属噪声. 因此 "脚本新版更快/更慢" 均不成立, 脚本版本变化对结论无影响.

## 6. 复现

```
cd /tmp/orchestra-06
for s in 1 2 3 4 5 6 7 8 9; do
  uv run python bench/run_export.py --side a --seed $s
  uv run python bench/run_export.py --side b --mode tuned --profile clear --seed $s
done
```
