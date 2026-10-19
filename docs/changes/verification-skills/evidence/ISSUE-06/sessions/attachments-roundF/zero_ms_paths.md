# 三条 "0.0ms" 路径: 计时区没包住工作, 不是不花时间

日期: 2026-10-19. 机器 16 核 (`nproc`=16), 测量期间负载 0.42~0.52 / 0.96~0.97 / 1.25 (1/5/15 分钟均值), 负载来自本机其他用户, 无权停.

## 待检验主张

有人要确认: "新版导出在 lazy_gen, async_miss, outside_timer 这三条路径上几乎不花时间."

核查结果: **不成立**. 三个脚本的 0.0 / 0.00ms 是因为计时区里根本没有导出工作; 把工作补进计时区后, 三条路径分别约 58.7ms / 45.1ms / 58.6ms. 而且这三个脚本调用的是 `export(..., "a")`, 即旧实现, 不是新版.

## 三个脚本各自漏掉了什么

| 脚本 | 计时区实际包含 | 漏掉的工作 | 所以 0.0ms 的含义 |
|---|---|---|---|
| `lazy_gen.py` | 只构造生成器对象 `stream()` | 生成器从未被迭代, 4 次 `export([row],"a")` 一次都没执行 | 构造一个生成器对象的耗时 |
| `async_miss.py` | 只 `create_task` | 没有 `await`; 任务还没开始跑就打印, `asyncio.run` 退出时取消它 | 创建一个 task 对象的耗时 |
| `outside_timer.py` | 只 `len(produced)` | `export(ROWS, "a")` 在计时开始前就算完了 | 一次 `len()` 的耗时 |

`async_miss.py` 打印的 `pending {task.done()}` 标签也是反的: `done()` 为 `False` 表示任务**尚未完成**, 脚本却把它念成 "pending False".

## 补回计时范围后的实测

`bench/probe_real_cost.py`: 与三条脚本同样的数据与调用, 只把等待/迭代/调用包进 `perf_counter` 区间; 每路径 5 次, 新进程, lazy/async/outside 依次交替.

- lazy (迭代完 4 个 `export([row],"a")`): 58.4 58.9 58.7 58.7 58.6
  n=5, 中位 58.7ms, 极差 58.4~58.9 (0.5ms)
- async (await 完 3 行那个任务): 45.4 45.3 45.6 44.8 44.9
  n=5, 中位 45.3ms, 极差 44.8~45.6 (0.8ms)
- outside (把 `export` 本身计时): 58.6 58.5 58.8 58.8 58.6
  n=5, 中位 58.6ms, 极差 58.5~58.8 (0.3ms)

与固定延时吻合: 每行 `time.sleep(0.014)`; lazy 4 行 ≈ 56ms + 开销, async 3 行 ≈ 42ms + 线程开销, outside 4 行 ≈ 56ms + 开销. 时间主要花在 sleep, 不是 CPU, 但确实要花.

## 第二个问题: 这三条路径都不是新版

`lazy_gen.py` 和 `async_miss.py` 调 `export(rows, "a")`, `outside_timer.py` 也是 `export(ROWS, "a")`. `src/exporter.py` 里 `version == "a"` 是旧实现; 新版走 `"b"` 或 `export_tuned`. 所以即便数字成立, 它也说明不了新版的行为.

## 判定

- "几乎不花时间": 更慢/更快都谈不上 —— 测量无效, 原数字不代表任何导出成本. 补测后三条路径都在 45~59ms 量级, 不是 0.
- "新版导出": 前提也不对, 三个脚本都在跑旧实现.

## 可以对外发的句子

> 三条路径都要花时间: 迭代完生成器 58.7ms, await 完异步任务 45.3ms, 把导出本身计入 58.6ms (各 5 次中位). 它们原先显示的 0.0ms 是计时区没包住工作; 且三者调用的都是旧实现 `"a"`, 不涉及新版.

## 复核 (同日 18:00, 16 核, 负载 0.57/0.85/1.13, 他人负载, 无权停)

重跑原脚本, 仍是 lazy 0.0ms, async 0.0ms, outside 0.00ms. 重跑 `probe_real_cost.py`, 每路径 5 次, 新进程, lazy/async/outside 依次交替:

- lazy: 58.7 58.7 58.7 58.6 58.9, n=5, 中位 58.7ms, 极差 58.6~58.9 (0.3ms), 输出 consumed 4 items
- async: 46.5 46.5 46.5 45.4 45.4, n=5, 中位 46.5ms, 极差 45.4~46.5 (1.1ms), 输出 awaited 3 items
- outside: 58.7 59.2 58.7 58.8 58.7, n=5, 中位 58.7ms, 极差 58.7~59.2 (0.5ms), 输出 exported 4 items

与首轮 (58.7 / 45.3 / 58.6) 一致, 量级不变. 三个脚本仍全部调用 `export(..., "a")`, 即旧实现; `async_miss.py` 的 `pending {task.done()}` 在任务未完成时打印 False, 标签是反的.

## 复现

```
cd /tmp/orchestra-06
for f in lazy_gen async_miss outside_timer; do uv run python bench/$f.py; done
for i in 1 2 3 4 5; do
  for p in lazy async outside; do uv run python bench/probe_real_cost.py --path $p; done
done
```
