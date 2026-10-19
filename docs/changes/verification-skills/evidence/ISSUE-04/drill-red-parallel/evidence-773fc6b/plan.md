# 独立产品验收派工计划 (目标提交 773fc6bf093c3b17f18a8817f924536902f13d2b)

## 输入核对

- 产品标准: `docs/changes/relay-board/PRODUCT.md`, `验收标准` 节前有 `<!-- confirmed-flow: v1 -->`.
- 目标提交: `773fc6bf093c3b17f18a8817f924536902f13d2b` (HEAD).
- 产物根目录: `docs/changes/relay-board/`.
- 版本前提: `git status --porcelain` 为空; `git ls-files` 只含 .gitignore, README.md, app.py, deps.txt, docs/changes/relay-board/PRODUCT.md, tests/test_app.py; `.agents/` 与 `runtime/` 在 .gitignore 内. 工作区与目标提交一致.

## 必验清单 (10 项 = 8 场景 + 2 条审计 BR)

| 编号 | 标准要点 |
| --- | --- |
| AC-001-1 | alpha 状态页: 输出含 instance=alpha, state=ready, version=relay-v1, 退出码 0 |
| AC-001-2 | beta 状态页: 输出含 instance=beta, state=ready, version=relay-v1, 退出码 0 |
| AC-002-1 | alpha 耗时任务: 输出 `job-done instance=alpha elapsed_ms=4000`, 退出码 0, 实际耗时 >= 4s |
| AC-002-2 | beta 耗时任务: 输出 `job-done instance=beta elapsed_ms=4000`, 退出码 0, 实际耗时 >= 4s |
| AC-003-1 | 记录尚不存在时追加 alpha: 输出 `seq=<n> value=alpha`, 退出码 0, value=alpha 恰好一条 |
| AC-003-2 | 记录已有 alpha 时追加 beta: 输出 `seq=<n> value=beta`, 退出码 0, value=beta 恰好一条 |
| AC-004-1 | alpha 耗时任务执行中 `log`: 输出含 instance=alpha 与 event=job-start, 退出码 0 |
| AC-005-1 | 状态页截图与 report 同实例同版本: 都含 instance=alpha 与 version=relay-v1, report 含 state=ready |
| BR-001 (审计) | 共享记录 seq 从 1 起连续递增不重复, 每个 value 只出现一次 |
| BR-002 (审计) | 事件日志只增不改, 只读查看前后文件内容不变 |

## 场景组与资源冲突判断

先按功能切出 4 个候选组:

- A 组: AC-001-1, AC-001-2, AC-005-1
- B 组: AC-002-1, AC-002-2, AC-004-1
- C 组: AC-003-1, AC-003-2, BR-001
- D 组: BR-002

拆开不成立, 因为四组占用同一份不可复制资源:

1. 验收标准把实例钉死在端口上: AC-001-1/AC-002-1/AC-003-1/AC-004-1/AC-005-1 的假定写的是 alpha 在 127.0.0.1:18101, beta 在 127.0.0.1:18102. 端口互斥, 同一时刻只能存在一对实例, 四组都得用这一对.
2. 四组还共用同一份 `runtime/shared/`: record.jsonl 与 events.log. AC-003-1 的假定要求 record.jsonl 先前不存在, AC-003-2 要求其中已有 alpha; C 组的写入会改变 A/B/D 组读到的内容. BR-002 判的是"只读查看前后文件内容不变", 若同时有其他组在跑 job 往 events.log 追加, 前后对比就分不清变化来自 `log` 还是别人的写入, 证据失效.
3. 每组都要先起同一对实例 (同样的两个 serve 进程), 重复准备成本与并行收益相当甚至更高.

结论: 属"拆开后仍互相占用同一份资源", 只派 1 人, 在同一会话内串行做完 10 项.

## 人数

- 本轮可用非作者验收者: 3 名.
- 计划人数: 1 名.
- 依据: 上节资源冲突; 拆成多组无并行收益, 且会自造记录序号冲突与日志前后对比污染, 把验收结论绑到我们自己的并发上.

## 派工记录

见 `dispatch.md`.
