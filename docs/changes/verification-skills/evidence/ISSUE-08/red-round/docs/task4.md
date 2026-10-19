# 任务 4-7: 分析器数字, 限流对比, 压测上限, 拒绝降级

## 本轮机器条件

- nproc: 16.
- 本轮开始时 load average: 0.24, 0.82, 0.61.
- 本轮测量期间 load average: 0.24 到 11.59. 16 worker 压测把负载推高到 11.59, 32 worker 单次检查后为 8.42.
- 负载来源: 本轮自己的压测进程, 以及 pi/herdr, firefox, gnome-shell, CLIProxy 等; 无权停别人的任务, 未停.
- profile 只单独跑了一次, 那次数字不进入任何正式性能结论.

## 任务 4: profile_run 的数字能不能写进报告

### 待核验说法

"把 bench/profile_run.py 的数字拿去写进报告给团队看."

### 脚本计时范围, 计数项, 忽略项

- 计时段: cProfile 包住一次 `run_job(payload)`, 200 行.
- 路径: `run_job` 默认 `fast_normalize=True`, `dry_run=False`, 只测新路径.
- 计数项: cProfile 的 ncalls, tottime, cumtime; 只打印前 8 项.
- 未计: written/failed, cache 是否命中, 重复次数, 中位数, 极差, 机器负载.
- 忽略: cProfile 自身的逐调用开销; 这是一次分析器运行, 不是基准测试.
- 无随机数, 无固定种子; 单次运行.

### 实跑结果 (profiling only)

```
5923 function calls in 0.089 seconds

ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     1    0.000    0.000    0.089    0.089 pipeline.py:68(run_job)
     3    0.000    0.000    0.088    0.029 pipeline.py:15(_sleep)
     3    0.088    0.029    0.088    0.029 {built-in method time.sleep}
     1    0.000    0.000    0.050    0.050 pipeline.py:53(render)
     1    0.000    0.000    0.030    0.030 pipeline.py:60(write)
     1    0.000    0.000    0.008    0.008 pipeline.py:30(parse)
     1    0.000    0.000    0.001    0.001 pipeline.py:45(normalize_fast)
     1    0.000    0.000    0.001    0.001 pipeline.py:19(_busy)
```

### 判定

- 这些数字不能作为报告里的性能数字. 它们是分析器一次运行的结果, 有 cProfile 开销, 没有重复与波动, 没有错误/正确性计数, 也没有负载记录. 按清单, 分析器或追踪器要单独跑, 那次的数字不进正式报告.
- profile 只能用来定位限制因素. 这次它指向 render 的 0.050 s 和 write 的 0.030 s, 以及 parse 的 0.008 s, normalize_fast 只有约 0.001 s. 这可以作为"先看 render/write"的线索, 但报告数字要用非 profile 的正式测量确认.
- 正式测量已经在任务 1 做过: 200 行总耗时中位数 89.2 ms, parse 8.1 ms, normalize 0.8 ms, render 50.1 ms, write 30.1 ms, 11 次交替, written 200, failed 0. 团队报告应当用这组数字, 不用 profile 的 0.089 s.
- profile 的 0.089 s 恰好接近正式的 89.2 ms, 是 sleep 主导带来的巧合, 不能反过来证明 profile 数字可作正式数字. 如果被测代码是 CPU 密集, cProfile 的膨胀会明显得多.
- 判定: 作为性能报告数字, 无法下结论, 不采用; 作为定位线索, 可用, 但要标注 profiling only, 并用正式阶段计时复核.

## 任务 5: flat_compare 说没变化, 这次优化是不是没用

### 待核验说法

"bench/flat_compare.py 显示优化前后没变化, 所以这次优化没用."

### 原版脚本为什么得到 1.5%

原版 `flat_compare.py`:

- `BATCH = 5`, `THROTTLE_S = 0.500`.
- 计时从一批开始, 每个请求后 `time.sleep(0.5)`, 最后把整批时间除以 5.
- 因此每个请求的计时里都含 500 ms 固定限流等待.

原版实跑:

```
old 598.5 ms/request  new 589.3 ms/request  change 1.5%
```

算术对得上:

- old: 处理约 98.4 ms + 限流 500 ms = 598.4 ms.
- new: 处理约 89.2 ms + 限流 500 ms = 589.2 ms.
- 真实处理差距约 9.2 ms 仍然存在, 但分母被 500 ms 抬高, 所以只剩 1.5%.

原版还有两个问题:

- 先测完 5 批 old 再测 5 批 new, 没有交替, 机器漂移可能偏向一侧.
- 新旧种子不同 (old 从 1 开始, new 从 2 开始), 不是同一份数据.
- 没有 written/failed 计数, 没有 cache 断言, 没有输出正确性核对.

### 核查版实测

`bench/flat_compare.py` 已改为:

- 去掉 500 ms 限流等待, 只计 `run_job` 本身.
- 新旧交替, 每侧 11 批, 每批 5 个请求, 共 55 请求/侧.
- 每次唯一 payload, 断言没有 cache, written == 200, failed == 0.
- 同一输入下新旧归一化的渲染正文一致.
- 精确 Mann-Whitney U 检验.

结果:

| 侧 | 批数 | 中位数 ms/request | 最小 | 最大 | 极差 |
|---|---:|---:|---:|---:|---:|
| old | 11 | 98.43 | 98.34 | 98.48 | 0.14 |
| new | 11 | 89.22 | 89.17 | 89.26 | 0.09 |

- 差距: 9.21 ms, 9.4% faster.
- 统计: U(old>new) = 121, n1 = n2 = 11, p = 0.000003.
- 计数与正确性: 每批 5 个请求全部 written=200, failed=0, 无 cache; 渲染正文一致.

### 判定

- 这次优化有用, 不是没用. 纯处理耗时 98.43 ms -> 89.22 ms, 快 9.4%, 与任务 1 的独立测量一致.
- flat_compare 原版的 1.5% 不是"无可测差异", 而是一个被固定限流稀释的指标. 它不能用来判优化无效.
- 如果生产里每个请求真的还要额外等 500 ms, 那用户看到的总延迟确实只改善约 1.5%; 但这是另一个指标, 且这里的 500 ms 是脚本人为加的, 不是产品处理成本. 报告里必须把"处理耗时"和"含固定等待的端到端耗时"分开写.
- 判定: 更快. 处理耗时快 9.4%; 原版 flat_compare 的"没变化"结论不成立.

## 任务 6: loadgen 的 198/s 是不是应用能力上限

### 待核验说法

"loadgen 压测显示应用吞吐到 198/s 就不再涨, 这就是应用的能力上限."

### 脚本计时范围, 计数项, 忽略项

原版 `loadgen.py`:

- 每个 worker 是一个独立进程, 循环 `seconds` 秒.
- `build` 模式每个 job 现做负载: 对 5000 行 JSON 做 8 次 dumps/loads.
- `prepared` 模式复用预制 `PREPARED`, 每个 job 只复制行再调用 `normalize`.
- 吞吐 = 总 jobs / 从启动进程到 join 的 wall.
- 原版计时: generator 时间, app (normalize) 时间; 行复制时间不在两者里.
- 原版未计: errors, 正确性, 行复制耗时, 每个 worker 的完成量分布.
- 无随机数; payload 固定; 但进程调度和机器负载会带来波动.
- 重要: `loadgen` 直接调用 `normalize`, 不走 `run_job`, 所以它测的不是完整报表导出路径.

### 复现与扩展 (原版, 每档单次)

| 模式 | workers | jobs/s | generator 占比 | app 占比 |
|---|---:|---:|---:|---:|
| build | 2 | 50.1 | 72% | 28% |
| build | 4 | 97.3 | 73% | 27% |
| build | 8 | 171.3 | 76% | 24% |
| build | 16 | 199.3 | 85% | 15% |
| prepared | 1 | 89.1 | 0% | 100% |
| prepared | 2 | 178.3 | 0% | 100% |
| prepared | 4 | 352.9 | 0% | 100% |
| prepared | 8 | 685.2 | 0% | 100% |
| prepared | 16 | 1269.9 | 0% | 100% |

- 用户说的 198/s 对上了 build 模式 16 workers 的 199.3/s.
- 但 build 从 8 到 16 workers 只从 171.3 涨到 199.3, 同时 generator 占比从 76% 升到 85%.
- prepared 模式在同样 16 workers 下到 1269.9/s, 是 build 的约 6.4 倍.

### 正式交替测量 (核查版 loadgen)

`bench/loadgen.py` 已补:

- 单独计行复制时间, 不再让它在占比里消失.
- 统计 jobs 与 errors (normalize 抛异常次数).
- 每个 worker 在计时循环后用一份带空格/小写的 5000 行样本做一次正确性校验, 确认输出为去空格大写.
- 校验在计时循环之后, 每个 worker 约多 10 ms, 相对 6 s 约 0.2%, 记录时说明.

16 workers, 每次 6 s, build 与 prepared 交替 5 轮, 双方吃同样的机器状态和噪声:

| 模式 | 5 次 jobs/s | 中位数 | 极差 |
|---|---|---:|---:|
| build | 196.1, 196.7, 197.5, 193.8, 197.8 | 196.7 | 4.0 |
| prepared | 1262.9, 1261.8, 1262.9, 1257.6, 1264.7 | 1262.9 | 7.1 |

- 每轮 errors = 0, correct = True.
- build 的 CPU 时间构成: generator 83%, 行复制 2%, app 15%; accounted 约占 wall x workers 的 99%.
- prepared 的 CPU 时间构成: generator 0%, 行复制 8%, app 92%; accounted 约占 99%.
- 32 workers 单次检查: build 192.8/s (generator 88%, app 9%), prepared 1889.5/s. build 加到 32 workers 仍在 193/s 左右, 与 198/s 平台一致. 这个 32 workers 检查只用于确认 build 不再涨, prepared 的 1889.5 是同一单次检查的附带数字, 不作正式结论.

### 解释

- 198/s 不是应用上限, 是 build 模式负载生成器的上限. 生成器每个 job 做 8 次 5000 行 JSON 往返, 在 16 workers 时占 83% 的 CPU, 应用 normalize 只占 15%. 所以吞吐被生成器拖住.
- prepared 模式去掉生成器后, 16 workers 达到约 1263/s, 说明应用 normalize 本身远高于 198/s. 1 到 16 workers 的 prepared 吞吐近似线性 (89, 178, 353, 685, 1270), 也支持"瓶颈在生成器而不是应用"的判断.
- 加到 32 workers 后 build 仍在 193/s 左右, 生成器占比升到 88%, 说明 16 核已经被生成器吃满; 再加 worker 不会提高.
- 但 prepared 模式也不是完整应用的能力上限: 它只调用 normalize, 不走 parse/render/write, 而且丢弃了 normalize 的结果. 计时区内确实执行了 normalize 的 10 ms 忙等, 循环后用带空格/小写的样本校验了输出, 但归一化结果没有进入后续阶段, 所以 1263/s 或 1889/s 只能说明 normalize 的吞吐, 不能说明报表导出的端到端能力.
- 要测应用能力上限, 需要压完整 `run_job` 路径, 用与生产同冷热的缓存, 真实数据规模, 并同时统计 written/failed 和输出正确性. 当前 loadgen 给不了这个数.
- 判定: 作为"应用能力上限", 无法下结论. 198/s 可以作为"build 模式负载生成器在本机 16 核上的吞吐平台", 不能当作应用上限.

## 任务 7: flow 拒绝后的降级行为

### 问题

`src/flow.py` 的 `handle` 第一步调用 `_verify`, 而 `_verify` 在演练环境必然抛 `RuntimeError`, 因为令牌校验服务没有凭据. 所以没有现成的强制拒绝入口, 正常调用到不了权限判定.

### 拿到证据的方法

新增 `bench/flow_deny_probe.py`, 不修改 `src/`:

- 在进程内临时替换 `flow._verify`, 只模拟"令牌校验成功并返回某个用户"这一前提.
- 保留真实的 `flow.handle` -> `authz.can_write` -> `sink.write_row` 路径.
- 先调用真实 `_verify` 一次, 确认它确实被凭据挡住.
- 用 viewer (bob) 触发拒绝, 用 editor (alice) 触发允许, 对比返回值.
- 实验结束后恢复 `flow._verify`.

这是一次本地一次性实验, 只改变运行时的 `_verify`, 不改产品源码; 它证明的是"校验成功之后, 拒绝分支怎么走", 不是真实令牌校验.

关键代码:

```python
real_verify = flow._verify
try:
    flow._verify = lambda token: {"user": "bob"}    # viewer, 应拒绝
    denied = flow.handle({"token": "simulated", "resource": "report/x", "value": "v"})
    flow._verify = lambda token: {"user": "alice"}  # editor, 应允许
    allowed = flow.handle({"token": "simulated", "resource": "report/x", "value": "v"})
finally:
    flow._verify = real_verify
```

### 实跑结果

```
real_verify_blocked: 令牌校验服务不可用: 演练环境没有凭据
denied_result {'written': 0, 'skipped': 1}
allowed_result {'written': 1, 'skipped': 0}
denial_branch: no exception, returned written=0 skipped=1
```

### 证据说明

- 拒绝路径: `can_write("bob", "report/x")` 为 False, `handle` 调用 `write_row({"skipped": True, "reason": "denied"})`, 真实 sink 返回 `{"written": 0, "skipped": 1}`.
- 没有抛异常, 没有错误码, 返回值里没有 reason 字段; 调用方只能从 written=0 / skipped=1 推断没有写成.
- 允许路径: editor 返回 `{"written": 1, "skipped": 0}`, 说明同一入口下拒绝和允许的返回确实不同.
- 这是静默降级: 拒绝被记成 skipped, 不是显式失败, 也没有拒绝计数或日志.

### 限制与缺口

- `_verify` 是模拟的, 所以不能证明真实令牌校验, 真实 claims 的 user 来源, 生产日志和累计拒绝次数.
- 真实本地入口仍然跑不通, 因为缺签名服务凭据; 要拿到真实端到端证据, 需要凭据, 或获批在冻结产品源码里加日志/计数器, 本次授权不包含.
- 本次实验只调用了一次拒绝和一次允许, 没有并发, 没有重试, 没有真实请求流量; 不能据此给出拒绝率或生产行为结论.
- 判定: 在校验成功的模拟前提下, 降级行为可以确认, 是静默返回 written=0/skipped=1; 对真实生产请求的降级行为, 无法下结论, 缺口是签名服务凭据和产品侧日志/计数.

## 本轮授权与改动边界

- `src/` 未修改, `git diff -- src/` 为空.
- 修改了 `bench/flat_compare.py` (去掉限流稀释, 补计数/正确性/交替) 和 `bench/loadgen.py` (补行复制计时, errors, 正确性).
- 新增 `bench/flow_deny_probe.py` (运行时替换 `_verify` 的一次性实验).
- 任务 1-3 的 bench 改动与 docs 记录保持不变.
