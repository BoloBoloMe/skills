# B 清理记录

性质: 当前观察, 本轮实际操作. 工作目录: `/tmp/orchestra-10/methods-red`.

## A 完成标记门槛

先前于 `2026-10-19T16:23:28,072586663+00:00` 已观察到 A 的 DONE.md 存在. 清理前再次验证文件非空并 stat, 不引用其验收结论, 不对 A 承接标准下结论:

原始元数据 (含完整命令, 时间与退出码):
```text
command: bash -c test\ -s\ docs/changes/vault/evidence/r1-ea94082/verifier-a/DONE.md\ \&\&\ stat\ --printf=\"path=%n\\nsize=%s\\nmodified=%y\\n\"\ docs/changes/vault/evidence/r1-ea94082/verifier-a/DONE.md
start: 2026-10-19T16:23:56,740447498+00:00
end: 2026-10-19T16:23:56,745999687+00:00
exit_code: 0
```
原始 stdout:
```text
path=docs/changes/vault/evidence/r1-ea94082/verifier-a/DONE.md
size=3113
modified=2026-10-20 00:21:25.460093452 +0800
```
原始 stderr:
空, 0 字节.

A 文件修改时间带 `+0800`, 折算为 UTC 是 `2026-10-19T16:21:25.460093452+00:00`, 早于下面的清理. 无需等待 30 分钟, 清理没有搁置.

## 清理前状态与保留原件

原始元数据 (含完整命令, 时间与退出码):
```text
command: find runtime -printf %y\ %p\ %s\ bytes\\n
start: 2026-10-19T16:23:56,748061755+00:00
end: 2026-10-19T16:23:56,751380841+00:00
exit_code: 0
```
原始 stdout:
```text
d runtime 60 bytes
d runtime/data 80 bytes
d runtime/data/outbox 60 bytes
f runtime/data/outbox/replication-log.jsonl 246 bytes
f runtime/data/records.jsonl 29 bytes
```
原始 stderr:
空, 0 字节.

先完整复制 runtime 到本组证据目录, 再做逐文件比较:

原始元数据 (含完整命令, 时间与退出码):
```text
command: cp -a -- runtime docs/changes/vault/evidence/r1-ea94082/verifier-b/06-before-cleanup-runtime
start: 2026-10-19T16:23:56,753347981+00:00
end: 2026-10-19T16:23:56,756037767+00:00
exit_code: 0
```
原始 stdout:
空, 0 字节.
原始 stderr:
空, 0 字节.

原始元数据 (含完整命令, 时间与退出码):
```text
command: diff -rq -- runtime docs/changes/vault/evidence/r1-ea94082/verifier-b/06-before-cleanup-runtime
start: 2026-10-19T16:23:56,757456333+00:00
end: 2026-10-19T16:23:56,760570508+00:00
exit_code: 0
```
原始 stdout:
空, 0 字节.
原始 stderr:
空, 0 字节.

保留原件位置:
- `06-before-cleanup-runtime/data/records.jsonl`
- `06-before-cleanup-runtime/data/outbox/replication-log.jsonl`

清理前枚举没有 runtime/export.jsonl, 不声称保存了不存在的导出文件.

## 清理命令与原始结果

原始元数据 (含完整命令, 时间与退出码):
```text
command: rm -rf -- runtime/data
start: 2026-10-19T16:23:56,763070883+00:00
end: 2026-10-19T16:23:56,766310460+00:00
exit_code: 0
```
原始 stdout:
空, 0 字节.
原始 stderr:
空, 0 字节.

原始元数据 (含完整命令, 时间与退出码):
```text
command: rm -f -- runtime/export.jsonl
start: 2026-10-19T16:23:56,768960512+00:00
end: 2026-10-19T16:23:56,771674579+00:00
exit_code: 0
```
原始 stdout:
空, 0 字节.
原始 stderr:
空, 0 字节.

`rm -f` 对当时已不存在的 export 文件是无操作, 退出码如实为 0.

原始元数据 (含完整命令, 时间与退出码):
```text
command: rmdir -- runtime
start: 2026-10-19T16:23:56,773307111+00:00
end: 2026-10-19T16:23:56,777166167+00:00
exit_code: 0
```
原始 stdout:
空, 0 字节.
原始 stderr:
空, 0 字节.

## 清理后状态

原始元数据 (含完整命令, 时间与退出码):
```text
command: bash -c if\ test\ -e\ runtime\;\ then\ find\ runtime\ -printf\ \"%y\ %p\ %s\ bytes\\n\"\;\ exit\ 1\;\ else\ printf\ \"runtime\ absent\\nruntime/data\ absent\\nruntime/export.jsonl\ absent\\n\"\;\ fi
start: 2026-10-19T16:23:56,779565653+00:00
end: 2026-10-19T16:23:56,782965477+00:00
exit_code: 0
```
原始 stdout:
```text
runtime absent
runtime/data absent
runtime/export.jsonl absent
```
原始 stderr:
空, 0 字节.

## 目标版本与产品文件复核

原始元数据 (含完整命令, 时间与退出码):
```text
command: git -C /tmp/orchestra-10/methods-red rev-parse HEAD
start: 2026-10-19T16:23:56,784876451+00:00
end: 2026-10-19T16:23:56,788624004+00:00
exit_code: 0
```
原始 stdout:
```text
ea940821115424b7eb619e985b2304f2b61e9d1d
```
原始 stderr:
空, 0 字节.

原始元数据 (含完整命令, 时间与退出码):
```text
command: git -C /tmp/orchestra-10/methods-red diff --exit-code HEAD --
start: 2026-10-19T16:23:56,790856879+00:00
end: 2026-10-19T16:23:56,794541581+00:00
exit_code: 0
```
原始 stdout:
空, 0 字节.
原始 stderr:
空, 0 字节.

完整 git 状态原件另存 `06-final-status.meta.txt`, `06-final-status.stdout.txt`, `06-final-status.stderr.txt`. 此状态取于本文件与最终 DONE.md 写入前, 不冒充最终文件清单.

结论: 仅在 A 的完成标记出现后清理. 原始 records/outbox 已复制并经 diff 核对相同; runtime/data 与 runtime 均已删除. 目标提交未改变, 已跟踪产品文件与 HEAD 无差异. 未提交, 推送或创建分支.
