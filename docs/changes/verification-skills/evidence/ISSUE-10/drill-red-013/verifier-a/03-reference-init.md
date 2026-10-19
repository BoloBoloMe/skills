# 03 引用 B 的 init 原件的适用性核对

性质: 当前观察 (A 侧本轮实跑核对) + 对 B 原件的引用. 原件由 B 产生, A 未参与, 不采信其文字结论, 只核对可观察事实.

## 原件

- 产生者: 独立验收者 B (本轮, 未参与实现).
- 位置: `docs/changes/vault/evidence/r1-ea94082/verifier-b/` (`00-init.md`, `00-init.meta.txt`, `00-init.stdout.txt`, `00-init.stderr.txt`, `00-init.records.jsonl`, `00-init.replication-log.jsonl`).
- 原件记录的命令: `uv run python app.py init --data-dir runtime/data`
- 原件记录的时间 (UTC): start `2026-10-19T16:20:01,143095741+00:00`, end `2026-10-19T16:20:01,185978407+00:00`, 即本机 `2026-10-20T00:20:01+08:00`.
- 原件记录的退出码: 0; stdout `init-ok data-dir=runtime/data`; stderr 0 字节.

## A 等待与开工

- A 开工 (2026-10-20T00:19:26+08:00) 时 `verifier-b/` 为空, `runtime/` 不存在. A 未自行 init, 轮询等待原件出现.
- 2026-10-20T00:20:36+08:00 观察到 `00-init.md` 等原件出现 (约 50 秒), 满足派工单的 15 分钟等待上限. A 的 5 次计时从 2026-10-20T00:20:43+08:00 开始, 晚于 init 完成时间 (00:20:01), 满足 AC-001-1 的"runtime/data 已初始化"假定.

## A 独立核到的事实 (`02-raw/init-crosscheck.txt` 原文)

核对时间 `2026-10-20T00:21:09+08:00`, 命令与原始输出摘要:

```
$ diff seed/records.jsonl runtime/data/records.jsonl
identical
$ diff seed/replication-log.jsonl runtime/data/outbox/replication-log.jsonl
identical
$ cat runtime/data/records.jsonl
{"id": "r1", "text": "alpha"}
{"id": "r2", "text": "beta"}
$ stat -c '%n size=%s mtime=%y' runtime/data/records.jsonl runtime/data/outbox/replication-log.jsonl
runtime/data/records.jsonl size=59 mtime=2026-10-20 00:20:01.178168919 +0800
runtime/data/outbox/replication-log.jsonl size=166 mtime=2026-10-20 00:20:01.178214126 +0800
```

- 路径一致: 原件写的是 `--data-dir runtime/data`, 现场确为 `/tmp/orchestra-10/methods-red/runtime/data` (工作目录 `/tmp/orchestra-10/methods-red`).
- 时间一致: 两个文件 mtime 与原件 end 时间同一秒; `00-init.meta.txt` 的 start/end 与 `00-init.md` 正文一致.
- 内容一致: `records.jsonl` (59 字节) 与 `seed/records.jsonl` 逐字节相同; outbox 日志 (166 字节) 与 `seed/replication-log.jsonl` 逐字节相同. 与原件复制的 `00-init.records.jsonl` / `00-init.replication-log.jsonl` 内容相同.
- 解释器: 原件用 `uv run python`, 与 A 计时用的 `python3` (落同一 uv CPython 3.14.7) 一致; 对 export 的计时无可比性影响, 记录备查.

## 适用性判断

- 覆盖条件: 同一仓库路径, 同一目标提交 `ea94082`, 同一 `data-dir`, init 在 A 计时之前完成且只执行一次 (现场 `runtime/data` 目录创建时间 00:20, 与 init 时间吻合).
- 不采信的部分: 原件对 outbox `delivered: true` 的说明与 AC-001-1 无关; A 不据此对 BR-001 或 AC-002 下任何结论.
- 后续变化: B 在 init 后继续执行 record-list / purge 等操作, 可能改变 `runtime/data/records.jsonl` 内容. 这不影响 A 的结论: A 的 5 次 export 在 00:20:43-00:20:44 完成, 且 AC-001-1 的 export 命令只要求 `runtime/data` 已初始化, A 已观察到该前提成立 (产物行数/内容 5 次全同, 见 `01-export-perf.md`).
- 结论: B 的 init 原件对 AC-001-1 的"假定"部分适用, A 直接引用, 不改变 A 自己实跑得到的判定.
