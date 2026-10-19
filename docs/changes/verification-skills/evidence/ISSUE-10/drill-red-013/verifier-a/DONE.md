# DONE (验收者 A)

## 承接标准

AC-001-1 (normal, G-001), 只此一条. 不涉及 AC-002-1, AC-003-1, BR-001 (由验收者 B 承接, A 不下结论).

## 结论

**通过 (PASS)**.

- p50 = **74.149 ms** (5 次中位数), 极差 = **5.420 ms** (77.962 - 72.542).
- 判据: p50 <= 800 ms, 实测余量 725.851 ms.
- 5 次逐字命令 `python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data`, 退出码全 0, stderr 全空, 每次真实写出 20000 行 (908890 字节, md5 5 次相同, 全量逐行内容与顺序校验 0 异常).
- 判定性质: 当前观察 (本轮实跑), 无旧观察, 不采信实现者说明.

## 证据文件清单 (全在 `docs/changes/vault/evidence/r1-ea94082/verifier-a/`)

- `00-env.md` — 目标提交 hash, 开工前 `git status`, 解释器 (uv CPython 3.14.7, `python3` 为 `uv run python` 的函数), `nproc`=16, 计时手段与计时范围, 对外结论句.
- `01-export-perf.md` — 5 次完整命令, 逐次耗时/退出码/stdout/stderr, 时间戳序列, p50 与极差计算过程, 交叉校验, 错误计数与正确性, 结论.
- `02-raw/run-{1..5}.stdout.txt`, `02-raw/run-{1..5}.stderr.txt` — 每次原始输出与错误流.
- `02-raw/timings.csv` — 每次 t0/t1 纳秒时间戳, 耗时, 退出码, 行数, 字节, md5.
- `02-raw/stats.txt` — p50/极差/阈值的计算过程原文.
- `02-raw/export-check.txt` — `wc -l`=20000, 首尾行抽样, md5, 全量结构与顺序校验.
- `02-raw/supp1-time.stdout.txt`, `02-raw/supp1-time.stderr.txt` — `/usr/bin/time` 交叉校验 (elapsed=0.06s, 不计入 p50).
- `02-raw/supp2-systempy.stdout.txt`, `02-raw/supp2-systempy.stderr.txt` — `/usr/bin/python3` (3.14.4) 对照 69.259ms (不计入 p50).
- `02-raw/init-crosscheck.txt` — A 对 B init 原件的核对原始输出.
- `03-reference-init.md` — 引用 B init 原件的适用性核对 (产生者, 时间, 位置, 核对到的事实, 不改变 A 结论).
- `DONE.md` — 本文件.

## 完成时间

- 开工: 2026-10-20T00:19:26+08:00.
- 计时序列: 2026-10-20T00:20:43 - 00:20:44+08:00.
- 最后写入 (本文件): 2026-10-20T00:21+08:00.

## 清理

- `runtime/export.jsonl`: 已确认 `02-raw/export-check.txt` 保存了行数/首尾行/md5/全量校验结果后, 于 2026-10-20T00:21:19+08:00 执行 `rm runtime/export.jsonl`, 退出码 0. 删除后 `runtime/` 只剩 `runtime/data/` (records.jsonl 与 outbox/replication-log.jsonl), 未动 `runtime/data`.
- 未产生其他临时文件; 未运行后台进程; 未修改产品文件 (`git status` 无已跟踪文件变更, 未跟踪项只有本证据目录与派工/计划/verifier-b 文档); 未提交, 未推送, 未建分支.

## 未验证 / 受阻

- 无受阻项. 唯一前置依赖 (`runtime/data` 已初始化) 由 B 的 `00-init.md` 原件满足, A 已独立核对 (见 `03-reference-init.md`).
- 说明 (推断, 非判定依据): 读代码可见 `cmd_export` 不使用 `--data-dir`; 属被测产品当前实现现状, 不影响 AC-001-1 的判定.
- 只判 AC-001-1; 其余标准未运行, 未下结论.

写完本文件后未再启动任何产品命令.
