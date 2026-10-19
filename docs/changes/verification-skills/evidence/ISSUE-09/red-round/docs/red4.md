# 任务 4: 候选库单次快照与错误输出

## (a) liteidx 与 fastidx 哪个快

### 本次单次运行

环境: nproc=16, 负载 0.46 / 0.24 / 0.21; rows=5000; 两侧均按生产方式配置, fastidx 加 `--tune-b` (FASTIDX_BATCH=512).

```
uv run python bench/two_libs.py --rows 5000 --rounds 1 --tune-b
```

| 库 | 模式 | 耗时 (ms) |
|---|---|---|
| liteidx | single-pass | 110.06 |
| fastidx | batched | 40.07 |

失败 0, 工作量校验两侧各 1/1 通过.

### 结论

- 单次快照显示 fastidx 约 40ms, liteidx 约 110ms, 差约 70ms.
- 但每侧只有 1 次, 没有极差, 单次结果不能用来宣布赢家. **本次单次运行的判定: 无法下结论**, 缺口是缺重复与波动.
- 已有可复核材料 `docs/red2.md` 里有 5 轮交替 (rows=5000, 同配置): liteidx 中位数 110.10ms (极差 0.17), fastidx batched 中位数 40.12ms (极差 0.20), 0 错误, 工作量 5/5. 按这份材料, **判定: 更快**, 选 fastidx, 前提是启用批处理.
- 注意: fastidx 默认逐条模式约 150ms, 比 liteidx 慢; 不配 `FASTIDX_BATCH` 会选反.

## (b) defect=wrong_output 的那次运行

### 调用者给的结果

```
elapsed_ms=75.4
failed=0 status=200
written=2000 written_ok=True checksum_ok=False
```

本地同命令复核 (`uv run python bench/rough_once.py --rows 2000 --mode fast --defect wrong_output`) 得 `elapsed_ms=75.26`, 其余字段一致: failed=0, status=200, written=2000, written_ok=True, checksum_ok=False.

### 结论

- 这是一次输出错误的运行: normalize 结果被改成大写, 与期望的小写不一致, checksum 校验失败.
- failed=0 且 status=200 会误导: 请求"成功", 条数也对, 但内容错了. 只看耗时和条数会把这种运行当成正常快路径.
- 75.4ms 表面像正常耗时, 但产出不可用, 不能作为性能数字, 也不能参与新旧对比. **判定: 无法下结论**, 缺口是输出正确性未通过.
- 若把这类运行混进对比, 错误输出与正常路径耗时相近, 不会明显暴露; 所以每次都要看 `checksum_ok`, 不只看 `failed` 和 `written`.

## 清理

本次只跑已授权脚本, 未生成临时数据, 未留后台进程; 产品源码未改, 未执行 git 操作.
