# 任务 2: http500 结果整理与候选库选型

## (a) defect=http500 的那次运行

### 调用者给的结果

```
mode=fast rows=2000 rounds=1 defect=http500
elapsed_ms=3.02
failed=1 status=500
written=0 written_ok=False checksum_ok=False
```

### 复核

同命令本地重跑 (`uv run python bench/rough_once.py --rows 2000 --mode fast --defect http500`):

```
elapsed_ms=24.28
failed=1 status=500
written=0 written_ok=False checksum_ok=False
```

### 结论

- 这是一次失败响应: failed=1, status=500, 写出 0 条, 内容校验未通过; 计时区内只完成了 parse, 没有产生任何有效输出.
- 失败响应天然很快, 3.02ms / 24.28ms 都不能当性能数字用; 若混进对比会把报错当成提速.
- 两个数字还对不上: 源码里 500 分支在 parse 之后返回, 2000 行 parse 固定 24ms, 所以这次运行的下限就是约 24ms, 3.02ms 在本仓库这份源码上跑不出来. 差异原因未知 (可能是别的行数/别的版本), 该数字不可采信.
- 判定: **无法下结论**. 缺口是失败响应不可用于性能, 且调用者给的 3.02ms 与可复核结果矛盾.

## (b) liteidx 与 fastidx 选型

### 待核验的一句话

"5000 行建索引, fastidx 按批处理配置跑, 中位数约 40ms, 比 liteidx 的约 110ms 更快."

### 测量条件与授权

- 脚本: `bench/two_libs.py` (已授权的独立实验脚本, 非正式 TC). 本次在该脚本内补了交替排列, 失败计数与工作量校验; 产品源码 `src/` 未改.
- 机器: nproc=16, `uptime` 负载 0.22 / 0.18 / 0.20, 基本空闲.
- 数据规模: 5000 行; 每侧 5 次, 交替 liteidx, fastidx, liteidx, fastidx...
- 两侧均按生产方式配置: fastidx 加 `--tune-b` (`FASTIDX_BATCH=512`, 走 batched 模式); liteidx 源码无配置项, 只有 single-pass 一种模式.
- 数据性质: 耗时仍是 `time.sleep` 模拟, 只证明测量方法与选型流程, 不代表真实库性能.

### 首轮未调优 (只说明在比配置)

`uv run python bench/two_libs.py --rows 5000 --rounds 5`

| 库 | 模式 | 5 次耗时 (ms) | 中位数 | 极差 |
|---|---|---|---|---|
| liteidx | single-pass | 110.06 110.06 110.07 110.06 110.11 | 110.06 | 0.04 |
| fastidx | per-row | 150.07 150.07 150.07 150.25 150.13 | 150.07 | 0.18 |

fastidx 默认逐条模式, 工作量校验 0/5 通过 (模式不是生产方式), 错误 0. 这一轮比的是配置, 不用来选赢家.

### 调优后 (选型依据)

`uv run python bench/two_libs.py --rows 5000 --rounds 5 --tune-b`

| 库 | 模式 | 5 次耗时 (ms) | 中位数 | 极差 |
|---|---|---|---|---|
| liteidx | single-pass | 110.08 110.07 110.23 110.10 110.11 | 110.10 | 0.17 |
| fastidx | batched | 40.27 40.08 40.07 40.12 40.12 | 40.12 | 0.20 |

- 失败/错误: 两侧均 0.
- 工作量: 两侧各 5/5 次返回行数等于 5000, 模式分别为 single-pass 与 batched, 工作确实发生.
- 波动: 两侧极差均小于 0.25ms, 与 70ms 的差距相比可忽略, 差距远大于噪声.

### 理由与判定

- 选 **fastidx**, 前提是生产配置启用批处理 (`FASTIDX_BATCH>1`). 调优后中位数 40.12ms 对 110.10ms, 约 2.7 倍.
- 若按默认逐条模式部署, fastidx 反而更慢 (150ms 对 110ms), 选型结论会反过来; 所以配置是选型的一部分.
- 判定: **更快** (fastidx 加批处理配置, 5000 行建索引中位数 40.12ms, 对 liteidx 110.10ms; 5 次交替, 极差 <0.25ms, 0 错误, 工作量校验通过).
- 局限: 模拟耗时, 真实库需按同样方法重测; 未测并发与更大数据规模.

## 清理

未生成临时数据, 未留后台进程; 仅修改了 `bench/two_libs.py` 并留下本记录, 产品源码与既有测试未动.
