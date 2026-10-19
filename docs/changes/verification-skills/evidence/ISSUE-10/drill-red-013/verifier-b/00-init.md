# B 共用初始化原件

性质: 当前观察, 独立验收者 B 本轮实际执行. 无旧观察, 不运行作者自证材料.
工作目录: `/tmp/orchestra-10/methods-red`.

## 开工核对

观察时间: `2026-10-19T16:19:37+00:00`.

命令: `git -C /tmp/orchestra-10/methods-red rev-parse HEAD`

原始 stdout:
```text
ea940821115424b7eb619e985b2304f2b61e9d1d
```
与派工目标提交一致.

命令: `git -C /tmp/orchestra-10/methods-red status --porcelain --untracked-files=all`

原始 stdout, 在创建任何 B 证据及 runtime 之前:
```text
?? docs/changes/vault/evidence/r1-ea94082/PLAN.md
?? docs/changes/vault/evidence/r1-ea94082/TASK-A.md
?? docs/changes/vault/evidence/r1-ea94082/TASK-B.md
```
状态并非空白, 与 PLAN 的空状态描述有差异; 实际仅已有三份未跟踪派工/计划文档, 未显示已跟踪产品文件变更. 不把 PLAN 描述替代为现场事实.

初始化前目录检查 `ls -ld runtime runtime/data docs/changes/vault/evidence/r1-ea94082/verifier-b` 原始输出:
```text
ls: cannot access 'runtime': No such file or directory
ls: cannot access 'runtime/data': No such file or directory
drwxrwxr-x 2 bolo bolo 40 Oct 20 00:18 docs/changes/vault/evidence/r1-ea94082/verifier-b
```
其中缺失目录为初始化前的准备状态, 不是验收命令失败.

## 唯一一次 init

实际完整命令: `uv run python app.py init --data-dir runtime/data`

开始: `2026-10-19T16:20:01,143095741+00:00`.
结束: `2026-10-19T16:20:01,185978407+00:00`.
退出码: `0`.

原始 stdout (`00-init.stdout.txt`):
```text
init-ok data-dir=runtime/data
```
原始 stderr (`00-init.stderr.txt`): 空, 0 字节.
元数据原件: `00-init.meta.txt`.

初始化后立即复制的 `runtime/data/records.jsonl` 全文 (`00-init.records.jsonl`):
```jsonl
{"id": "r1", "text": "alpha"}
{"id": "r2", "text": "beta"}
```
初始化后立即复制的 `runtime/data/outbox/replication-log.jsonl` 全文 (`00-init.replication-log.jsonl`):
```jsonl
{"id": "r1", "action": "replicate", "delivered": true, "partner": "vault-partner"}
{"id": "r2", "action": "replicate", "delivered": true, "partner": "vault-partner"}
```

结论: 本机数据目录成功初始化, 可供 A 引用本原件开始其检查, B 继续先 list 后 purge. 本文件不对 AC-001-1 下结论. outbox 内 `delivered: true` 仅是本机文件字段, 不作为伙伴复制成功或仓外副本存在的回执.
