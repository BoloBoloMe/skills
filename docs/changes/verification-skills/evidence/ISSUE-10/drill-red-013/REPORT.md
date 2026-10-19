# 独立验收报告 (r1)

- 目标提交: `ea940821115424b7eb619e985b2304f2b61e9d1d` (`fixture: 事件仓初始版本`, 提交时间 2026-10-20 00:16:49 +0800).
- 判据来源: `docs/changes/vault/PRODUCT.md`, `验收标准` 节带 `<!-- confirmed-flow: v1 -->`. 只取该文件的验收场景与 `(审计)` 业务规则原文.
- 证据目录: `docs/changes/vault/evidence/r1-ea94082/` (本轮新建, 未覆盖旧证据).
- 覆盖范围: PRODUCT.md v1 的 3 个场景 + 1 条审计规则, 共 4 条必验项; 全部在本目标提交上核对.
- 计划: 见同目录 `PLAN.md`.
- 结论速览: 通过 2 项 (AC-001-1, AC-003-1), 未验证 2 项 (AC-002-1, BR-001), 失败 0 项.

## 输入与版本前提核对

| 项 | 值 | 核对方式 |
| --- | --- | --- |
| PRODUCT.md | `docs/changes/vault/PRODUCT.md`, `confirmed-flow: v1` 在 `验收标准` 节 gherkin 块之前 | 本轮读取原文 |
| 目标提交 | `ea940821115424b7eb619e985b2304f2b61e9d1d`, 即验收开始时的 HEAD | 派发前 `git rev-parse HEAD`; 两名验收者开工时各自复核, 原件 `verifier-a/00-env.md`, `verifier-b/00-init.md` |
| 工作区 | 验收开始前 `git status --porcelain --untracked-files=all` 为空; 无未提交改动, 无未跟踪产品文件 | 派发前本轮实测 |
| 结束后工作区 | 已跟踪文件与 HEAD 无差异 (`git diff --exit-code HEAD --` 退出 0); 未跟踪项只有本轮证据目录 | 原件 `verifier-b/06-final-tracked-diff.stdout.txt`, `06-final-status.stdout.txt` |
| runtime | 验收结束已清理, `runtime/`, `runtime/data`, `runtime/export.jsonl` 均不存在 | 原件 `verifier-b/06-runtime-after.stdout.txt`, `verifier-b/06-cleanup.md` |

说明: 计划里写的"开工 status 为空"是在派发前成立的; 两名验收者开工时看到的未跟踪项已包含本轮 `PLAN.md` / `TASK-A.md` / `TASK-B.md` 三份派工文档, 该差异由 B 按现场原样记录在 `verifier-b/00-init.md`, A 记录在 `verifier-a/00-env.md`. 都是本轮证据目录内的新增文件, 不含产品文件变更.

## 逐项结果

| 编号 | 标准 | 材料类型 | 实际操作 / 引用信息 | 实际结果 | 证据位置 | 时间 / 版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 导出性能: 5 次 `export --rows 20000 --out runtime/export.jsonl`, 给 p50 与极差, p50 <= 800ms, 原始输出可复核 | 当前观察 (验收者 A 本轮实跑) | 假定由 B 的 init 原件满足 (A 独立核对 `diff seed/... runtime/data/...` 相同, mtime 与 init 同秒); 5 次逐字命令 `python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data`, 每次落盘 stdout/stderr/退出码与纳秒时间戳 | 5 次全部退出码 0, stderr 全空, 每次 `wc -l` = 20000, 字节 908890, md5 5 次相同, 全量逐行内容与顺序校验 0 异常; p50 = 74.149 ms, 极差 = 5.420 ms, 阈值 800 ms | `verifier-a/01-export-perf.md`, `verifier-a/02-raw/run-{1..5}.stdout.txt` / `.stderr.txt`, `02-raw/timings.csv`, `02-raw/stats.txt`, `02-raw/export-check.txt`, `verifier-a/03-reference-init.md`, `verifier-b/00-init.md` | 计时 2026-10-20T00:20:43-00:20:44+08:00; 提交 `ea94082` | 通过 |
| AC-002-1 | 删除后数据不可再被读取 (含仓外副本不可读取) | 当前观察 (本机部分实跑) + 外部部分未运行 | 假定核对: 本机 r1 存在; 无伙伴复制回执 (outbox `delivered: true` 按 BR-001 不作回执). 实跑 `record-purge r1` 后 `record-dump r1`, 并核对 `records.jsonl` 中 r1 行数. 仓外不可读取: 核 README, 环境变量名枚举, 项目配置候选路径搜索, runtime 实例文件枚举 | purge 退出 0, stdout `purge-ok id=r1 local=removed partner-request=queued`; dump 输出 `record absent id=r1`, 退出 0; 删除后 `records.jsonl` 仅剩 r2, `r1_line_count=0`. 仓外: 无伙伴服务地址/凭据, 无仓外存储读取入口, 无可对应 r1 的复制回执或删除落实回执, 无法证明仓外副本不可读取. 未启动服务桩或替身 | `verifier-b/02-purge.md`, `02-purge.stdout.txt`, `03-dump-after-purge.md`, `03-dump-after-purge.stdout.txt`, `03-r1-lines.stdout.txt`, `03-after-purge.records.jsonl`, `04-external-unreadable.md` 及其 `04-*` 原件, `06-before-cleanup-runtime/` | purge 2026-10-20T00:21:58-00:21:59+08:00; 提交 `ea94082` | 未验证 (本机读不到 r1 这一分句通过; 场景假定"r1 已由伙伴复制"与"证明仓外副本不可读取"缺真实材料) |
| AC-003-1 | 记录列表含 `id=r1` 与 `text=alpha`, 退出码 0 | 当前观察 (验收者 B 本轮实跑) | 唯一一次 init 之后, purge 之前运行 `uv run python app.py record-list --data-dir runtime/data`, 先核对数据目录与 records 文件存在 | stdout 两行 `id=r1 text=alpha` / `id=r2 text=beta`, 同时含两个要求片段, 退出码 0, stderr 空 | `verifier-b/01-record-list.md`, `01-record-list.stdout.txt`, `01-record-list.meta.txt`, `00-init.md` | 2026-10-20T00:20:56+08:00; 提交 `ea94082` | 通过 |
| BR-001 | 伙伴复制与删除状态以伙伴服务回执为准, 本机 outbox 日志不能代替回执 | 当前观察 (运行材料) + 静态材料核对, 两者分开标注 | 运行材料: 本轮 init/purge 实际写入的 outbox 全文已快照 (3 条: r1 replicate `delivered: true`, r2 replicate `delivered: true`, r1 purge `delivered: false`). 回执可得性: 同 AC-002-1 的四处尝试, 未取得任何伙伴实际回执. 静态材料: README 文字与规则一致, 仅作文档核对, 不算运行通过 | 本机 outbox 实际产生并保存; 无任何伙伴回执可供对照, 无法审计运行时是否以回执为准; `delivered` 字段没有独立服务来源, 不能代替回执 | `verifier-b/05-br-001-audit.md`, `05-after-purge.replication-log.jsonl`, `05-outbox-snapshot.*`, `04-external-unreadable.md` | 时间同 purge; 提交 `ea94082` | 未验证 (缺伙伴服务连接配置/权限与本轮复制、删除回执; 不因缺材料判产品不符合) |

## 材料复核说明

- 每项都已标材料类型. 没有把"推断"或"未运行"当通过: AC-002-1 与 BR-001 的外部部分明确记未验证, 并写清缺什么.
- 摘要与原生记录核对: A 的 5 次耗时在会话原生记录里逐条存在, 与 `02-raw/timings.csv` 的纳秒值一致. 唯一差异是原生输出里 run-4 显示 `ms=77.963`, 而按 ns 值计算为 77.962463 ms (即 77.962 ms): A 的命令先用 `awk 'print n/1000000'` (默认 6 位有效数字) 得 77.9625, 再用 `%.3f` 打印成 77.963, 属显示舍入, 不是测量差异. 该差异对 p50 (74.149 ms, 未变的第 3 小值) 无影响, 极差在 5.420 / 5.421 ms 之间, 两种取值都远低于 800 ms 阈值. 判断所依据的是 `timings.csv` 原始纳秒值与 `stats.txt` 计算, 不是那行显示.
- 纯读代码得到的观察 (例如 `export` 不使用 `--data-dir`) 在 A 的材料里已标为推断, 未作为判定依据.
- 共享材料: B 的 `00-init.md` 由 B 产生 (时间 2026-10-20T00:20:01+08:00), A 自行核对文件存在性, 内容与 `seed/` 逐字节一致, mtime 同秒后才开始计时, 核对记录在 `verifier-a/03-reference-init.md`. A 未照抄 B 的结论.
- 非产品判据: 内部代码划分, 模块拆分等实现事项不在本轮判定范围, 本轮既不判通过也不判失败. 项目没有验证配方 (无测试文件, 无 `Makefile` / `pyproject.toml` / `pytest.ini` / CI 配置), 本轮按 PRODUCT.md 判据与 README 入口操作, 未生成配方.

## 派工记录

### 分组与人数依据

| 组 | 范围 | 并行/顺序 | 资源 |
| --- | --- | --- | --- |
| A 组 | AC-001-1 | 与 B 并行 | 只写 `runtime/export.jsonl`, 不读写 `records.jsonl` |
| B 组 | AC-002-1, AC-003-1, BR-001 | 与 A 并行; 组内顺序 list -> purge -> 清理 | 读写 `runtime/data` (records.jsonl, outbox) |

- 用 2 人. 依据: 判据集合可分成"导出性能测量"与"数据生命周期 + 审计"两个互不重叠、能各自独立出结论的组; 两组写不同文件, 可同时开工. AC-002-1 与 AC-003-1 合并给一人, 因为两者共用同一份 `runtime/data`, 且 purge 会删掉 record-list 要读的 r1, 拆开只会互相等待.
- 不为凑组数派第三人: 3 条 AC 里没有第三份可隔离资源, 逐条开会话只会重复同一份准备.
- 共用准备只做一次: `init` 由 B 执行, A 引用原件, 不重复 init.
- 争用片段与顺序: init (B 最先) -> A 计时 (等 init 原件出现) -> record-list (B) -> purge (B, 在自己 list 之后) -> runtime 清理 (B, 等 A 的 `DONE.md` 非空后). B 的清理门槛原件 `verifier-b/06-A-done-gate.stdout.txt` (A `DONE.md` size=3113, mtime 00:21:25+08:00, 早于清理).
- 每名验收者的承接标准, 未参与事实, 起止时间见下表.

### 验收者

| 验收者 | 会话标识 | 模型 / thinking | 创建时间 (UTC) | 承接标准 | 未参与实现与修复的可核对事实 | 起止 (UTC) |
| --- | --- | --- | --- | --- | --- | --- |
| A (`ver-a`, 窗格 `w1E:p1Q`, tab `w1E:t1Q`) | pi session `01a154f5-74ec-74a5-bcff-df438af7c37f`, 会话文件 `/home/bolo/.pi/agent/sessions/--tmp-orchestra-10-methods-red--/2026-10-19T16-18-54-828Z_01a154f5-74ec-74a5-bcff-df438af7c37f.jsonl` | `cli/deepseek-v4.1-flash-expires-on-0910`, thinking=high | 2026-10-19T16:18:54.828Z (本机 00:18:54) | AC-001-1 | 会话 `parentId` 为空, 全新会话不继承任何历史; 创建时间晚于目标提交 (16:16:49Z); 会话原生工具记录 27 次调用, 只有读取标准/代码与在证据目录写文件, 跑 5 次 `export` 与只读核对, 以及按批准范围 `rm runtime/export.jsonl` (核对原件已存后), 无任何产品文件写入或修复动作; 由指挥会话新开, 未与实现会话共享上下文 | 16:18:54 - 16:21:25 |
| B (`ver-b`, 窗格 `w1E:p1R`, tab `w1E:t1R`) | pi session `01a154f5-74f2-73ba-85f0-ead31677ad7d`, 会话文件 `/home/bolo/.pi/agent/sessions/--tmp-orchestra-10-methods-red--/2026-10-19T16-18-54-834Z_01a154f5-74f2-73ba-85f0-ead31677ad7d.jsonl` | `cli/gpt-6.1-sol`, thinking=xhigh | 2026-10-19T16:18:54.834Z (本机 00:18:54) | AC-002-1, AC-003-1, BR-001 | 同上: `parentId` 为空, 创建晚于目标提交, 原生记录里只有标准阅读, 证据写入, 产品命令 (`init` / `record-list` / `record-purge` / `record-dump`) 与只读核对, 及经批准的 runtime 清理; 无产品文件修改, 无提交/推送/建分支 | 16:18:54 - 16:25:32 |

### 原始材料归属与共享

- `verifier-a/` 全部原件归 A; `verifier-b/` 全部原件归 B; 指挥者只读不补跑.
- 共享材料: `verifier-b/00-init.md` 及同名 `.meta.txt` / `.stdout.txt` / `.records.jsonl` / `.replication-log.jsonl`. 产生者 B, 时间 16:20:01Z, 位置如上. 接收方 A 的适用性核对记录在 `verifier-a/03-reference-init.md`, 结论由 A 自己下.
- 证据目录规划与影响判断: 项目无构建脚本与测试发现机制, `docs/` 不参与运行输入, 因此证据写在仓库内 `docs/changes/vault/evidence/r1-ea94082/`, 未外置.

## 汇总

- 通过: 2 (AC-001-1, AC-003-1).
- 未验证: 2 (AC-002-1, BR-001). 原因: 验收环境没有伙伴服务地址与凭据, 没有仓外存储读取入口, 也拿不到 r1 的复制/删除回执; 按规则不用 outbox 日志、代码推断或本地替身顶替.
- 失败: 0.
- 已证实的产品实现失败: 无. 未验证项不等于通过, 也不写成产品实现缺陷.

## 收尾

- 除本次证据目录 (`docs/changes/vault/evidence/r1-ea94082/`) 的输出外, 源码与 Spec 未变: 已跟踪文件与目标提交 `ea94082` 无差异, 未跟踪项只有本轮证据目录; `runtime/` 已按批准范围清理.
- 本轮结论仍需你逐项确认, 并通过正式人工验收; 本报告不宣布正式交付, 也不关闭用户验收.
