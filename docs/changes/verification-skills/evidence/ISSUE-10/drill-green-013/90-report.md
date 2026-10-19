# 事件仓 (vault) 独立验收报告 — 第 1 轮

- 目标提交: `ea940821115424b7eb619e985b2304f2b61e9d1d` (fixture: 事件仓初始版本, 提交时间 2026-10-20T00:16:49+08:00)
- 判据来源 (唯一): `docs/changes/vault/PRODUCT.md`, sha256 `0512602f2ad78dd0393562a46878204eadecaa39fff18316030e2555c80aee84`, 内含确认标记 `<!-- confirmed-flow: v1 -->`
- 产物根目录: `docs/changes/vault/`, 本轮证据目录: `docs/changes/vault/evidence/r1-ea94082/` (本轮新建, 未覆盖任何旧证据)
- 指挥会话: pi session `01a154fd-c52a-753d-a236-d3f603e632a1` (agent 名 i10-green-mth)
- 输入核对: 三项齐全 (PRODUCT.md 已确认 / 目标提交 ea94082 / 产物根目录). 项目无 TECHNICAL.md, 无 EXECUTION.md, 无构建脚本, 无测试套件, 无验证配方; README.md 仅作操作入口.
- 计划: `00-plan.md` (分组依据, 人数, 资源与争用顺序, 授权范围)

## 1. 必验清单与逐项结果

必验项 = 3 个验收场景 + 1 条审计 BR, 共 4 项, 与 PRODUCT.md 原文一一对应.

| 标准编号 | 材料类型 | 实际操作 / 引用信息 | 实际结果 | 证据位置 | 时间 / 版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 (G-001) | 当前观察 (验收者本轮实跑) | 共用准备 `init --data-dir runtime/data` 一次, 随后连续 5 次运行 `python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data`, 每次记纳秒起止、退出码、stdout/stderr、输出文件行数/字节/sha256 | 5 次耗时 72.569 / 78.218 / 74.193 / 72.625 / 75.095 ms; p50 = 74.193 ms (两种算法同值), 极差 = 5.649 ms; 5/5 退出码 0, stderr 空; 每次 20000 行 / 908890 B / sha256 f7adaf5b…52805b39; 逐行比对 20000 行全部符合期望 | `V1-perf/REPORT.md`, `V1-perf/02-run-5x.log`, `06-stats.log`, `04-correctness.log`, `run-export-5x.sh` | 2026-10-20T00:29:54–00:29:56 (+08:00), 提交 ea94082 | **通过** (74.193 ms ≤ 800 ms) |
| AC-003-1 (G-003) | 当前观察 | `python3 app.py record-list --data-dir runtime/data` (purge 之前执行, 00:30:16) | 退出码 0; 输出 `id=r1 text=alpha` / `id=r2 text=beta`; 断言 `id=r1` 与 `text=alpha` 各命中 1 次 | `V2-del/REPORT.md` §2, `V2-del/01-record-list.out`, `01-record-list.err`(0 字节) | 2026-10-20T00:30:16 (+08:00), 提交 ea94082 | **通过** |
| AC-002-1 (G-002) | 当前观察 + 未运行 | 本机子句: purge 前 `record-dump r1` → `text=alpha`; `record-purge r1` → `purge-ok id=r1 local=removed partner-request=queued`; purge 后 `record-dump r1` → `record absent id=r1`; `record-list` 只剩 r2. 仓外子句: 无伙伴服务地址/凭据, 无仓外存储读取入口 | 本机子句成立 (记录在最终版本上确实不可再被本机读到, records.jsonl 中无 r1, runtime 内无 `alpha` 正文残留, 负向对照脚本退出码 1). 仓外子句**无法证明**: `PARTNER_URL` 未设置, PATH 无 vault/aws/s3cmd/rclone, 无伙伴配置, 仓库与 runtime 内无回执类文件 | `V2-del/REPORT.md` §2 §4, `02-purge.out`, `03-dump-post.out`, `04-probe.out` (F2 PASS), `05-probe-negctl.out` (负向对照 FAIL, 退出码 1), `04-probe.py`, `00-env.txt` | 2026-10-20T00:30:19–00:30:36 (+08:00), 提交 ea94082 | **未验证** (本机子句通过, 仓外子句缺环境/权限) |
| BR-001 (审计) | 静态核对 + 当前观察 | ① 实读 purge 前后 outbox: 3 行, 字段只有 `id/action/delivered/partner`; `grep -c -E 'receipt\|ack\|signature\|nonce\|remote_id\|confirmed'` 在 outbox 与 app.py 均 0 命中. ② purge 前 outbox 与 `seed/replication-log.jsonl` 逐字节相同 (`cmp` identical, sha256 同为 3ae930f5…38913). ③ 本轮真实资源上的写入: record-purge r1 于 00:30:19 改写 records.jsonl (59→29 B) 并向 outbox 追加 `{"id":"r1","action":"purge","delivered":false,...}` | 本机不存在伙伴回执; outbox 里的 `delivered: true` 是 fixture 固定数据的拷贝, 不是任何伙伴交互结果; purge 后本机立即删记录且不等待任何回执. "状态以回执为准" 这一步本机无回执可依, 因此**不能判通过**; 也**不能由此判产品失败** (PRODUCT.md 未规定回执载体与无回执时的判定) | `V2-del/REPORT.md` §2 BR-001 与 §7; `V2-del/outbox.pre-purge.jsonl`, `records.pre-purge.jsonl`, `seed/replication-log.jsonl`; 本轮复核见 `11-cleanup.txt` | 2026-10-20T00:30:19–00:31:23 (+08:00), 提交 ea94082 | **未验证** (静态核对完成, 回执部分缺环境) |

汇总: 4 项中 2 项通过 (AC-001-1, AC-003-1), 2 项未验证 (AC-002-1 的仓外子句, BR-001 的回执部分), 0 项已证实的实现失败. **整体不写"全部通过"**.

## 2. 材料复核 (指挥者只核对材料, 未亲自运行被验产品)

我对交回材料的核对动作与结果:

1. 原件可读性: 两组的原始命令输出、脚本全文、负向对照输出都在证据目录内可读 (`V1-perf/` 10 个文件, `V2-del/` 13 个文件), 不是只有摘要.
2. 摘要与原件一致: AC-001-1 的 5 次数值我按 `02-run-5x.log` 逐条重读并与 `06-stats.log` 对齐 (中位数 74.193, 极差 5.649, 无噪声触发); AC-003-1 的 stdout 与 `01-record-list.out` 逐字节一致.
3. 关键派生量交叉核对 (只读文件, 未运行产品): 我在清理前对 `runtime/export.jsonl` 取 sha256, 得 `f7adaf5b3ed4fe57e451bd8abd28fbefcc1c8f0f1060d232c651987752805b39`, 与 V1 记录的 5 次运行值相同 (见 `10-runtime-before-cleanup.txt`); V2 的 purge 前后记录/outbox 副本 sha256 与 `seed/` 原件一致, 且 `cmp` 报 identical, 印证"`delivered: true` 来自 fixture"这一判断.
4. 材料类型标注: 每项都标了当前观察 / 静态核对 / 未运行; V2 的推断部分 (不重跑 init 看 r1 是否复活) 明确标为推断且未计入结论, 我按第 8 步规则拒绝把推断当通过依据.
5. 共享材料: 两组本轮没有共享原始材料 (V1 的 init 输出被 V2 引用为"前提成立"的依据, V2 自己看了 `runtime/data` 的存在与 mtime). 该引用只用于前提核对, 判断各归其标准.
6. 一处验收者自曝的取证失误 (V1 §4.5): 曾并行发出校验命令读到写一半的文件, 导致 sha 不一致; 之后串行重算并 `cmp` identical. 正式 5 次数据取自各自运行结束后顺序读取, 不受影响. 我复核了 `05-determinism-recheck.log` 与清理前 sha, 结论成立.

## 3. 三类去向

### 3.1 已证实的实现问题 (交回实现流程)

**无.** 本轮没有在最终版本上稳定失败、且失败原因能定位到实现行为的场景.

说明: V2 在自己的报告 §3 里把两条静态事实列在"已证实的实现问题"名下, 汇总时我改归下面的说明性事实/缺规则, 理由是它们没有构成某个场景在最终版本上失败: (a) `cmd_record_purge` (app.py:84-97) 只改本地记录并追加 outbox 行, 不接触伙伴服务 — 这符合 README 描述的"仓外复制与删除由伙伴服务负责"分工, PRODUCT.md 未要求本机完成仓外删除; (b) purge 前 outbox 的 `delivered: true` 来自 `seed/replication-log.jsonl` 固定数据 — 这是 fixture 数据源的性质, 不是被验命令产生的错误行为, 但它正是 BR-001 存在的理由.

### 3.2 尚缺产品规则 (只停受影响项, 交回决策流程)

受影响标准: AC-002-1 (仓外子句), BR-001.

- PRODUCT.md 未定义伙伴回执的载体与格式 (文件/接口/字段), 所以"以回执为准"在本仓库内没有可执行的判据.
- 未定义 purge 在没有回执时应输出什么 (当前实现固定打印 `partner-request=queued` 并退出 0), 也未定义"删除完成"是否必须等回执.
- 未定义仓外副本的读取/举证方式 (谁提供入口, 怎么证明不可读), 所以 AC-002-1 第二子句无可判标准.
- 下一步: 由既有决策流程补规则; 补齐前这两项保持未验证, 不追认为通过.

### 3.3 权限与环境缺口 (未验证)

受影响标准: AC-002-1 (仓外子句), BR-001 (回执部分).

- 缺 `PARTNER_URL`, 缺伙伴服务凭据, 缺仓外存储读取入口; README.md 也明确写"本环境没有伙伴服务的地址与凭据, 也没有读取仓外存储的入口".
- 证据: `V2-del/00-env.txt` (PARTNER_URL 未设置), `V2-del/04-probe.out` 的 `[F3] UNPROVEN` 行, `V2-del/REPORT.md` §2 的入口探测记录.
- 未用服务桩、本地替身或伪造回执改判通过.

## 4. 派工记录

### 4.1 场景组划分与人数依据

| 组 | 承接标准 | 方法 | 验收者 |
| --- | --- | --- | --- |
| 组 1 | AC-001-1 | benchmark-checklist | verify-perf |
| 组 2 | AC-003-1 (先) → AC-002-1 → BR-001 | blast-radius | verify-del |

- 可用非作者会话: 本仓库此前无实现或修复会话 (提交只有 1 个 fixture 提交, 仓库内无其他 agent 操作记录). 本轮新开 2 个.
- 计划人数 = 实际人数 = 2. 不派 3 人的理由: AC-003-1 只有一条命令, 单独开一个会话没有并行收益, 且它依赖 purge 前的 r1 状态, 与 AC-002-1 天然同一条时序链; 性能组需要相对安静的机器, 单独成组才有意义.
- 只派 1 人也不够: 性能测量与删除/审计两组的判据和方法互不相干, 且性能组要求独占式计时, 合并成一人会让测量被自己后面的写入动作干扰, 也失去独立复核者.

### 4.2 资源与争用

- 批准范围只覆盖一个测试实例 `runtime/data`, 因此两组共用同一份数据, 未新开第二份数据目录, 也未扩端口/实例.
- 争用片段: `records.jsonl` 的"读列表"与"删 r1"必须先后. 执行顺序: verify-del 于 00:30:16 先做 AC-003-1, 00:30:19 再做 purge; 依据是本轮计划 (`00-plan.md`) 与"purge 会删除 r1, 之后无法再观察列表".
- 无争用的部分并行: verify-perf 的 5 次 export (00:29:54–00:29:56) 只写 `runtime/export.jsonl`, 不读 `records.jsonl`, 与组 2 同时进行; 组 2 的首条命令 00:30:16 开始时性能组已结束, 计时未与其重叠.
- 共用准备 (init) 由 verify-perf 执行一次, 时间 00:29:48, 输出 `init-ok`, 证据 `V1-perf/01-init.txt`; verify-del 未重复 init (其报告记录了"未重新 init").

### 4.3 验收者与未参与事实

| 项 | verify-perf | verify-del |
| --- | --- | --- |
| 会话标识 (pi session id) | `01a154ff-0780-770c-bce8-e95edc780785` | `01a154ff-9d7f-741c-9fe8-78c5731be73b` |
| 创建时间 | 2026-10-20T00:29:22+08:00 | 2026-10-20T00:30:00+08:00 |
| herdr agent / 窗格 | verify-perf / w1E:p1Y (tab S-VerifyPerf-1) | verify-del / w1E:p10 (tab S-VerifyDel-2) |
| 模型 / thinking | cli/deepseek-v4.1-flash-expires-on-0910 / high | 同模型 / max |
| 承接标准 | AC-001-1 | AC-003-1, AC-002-1, BR-001 |
| 未参与事实 (可核对) | 会话创建时间 00:29:22 晚于目标提交 00:16:49; 会话记录里对 `app.py` / `PRODUCT.md` / `README.md` / skill 文件只有 read, write 仅落在 `V1-perf/` 与 `runtime/`; 全程无 git 写操作 | 会话创建时间 00:30:00 晚于目标提交; 会话记录里对 `PRODUCT.md` / skill 只有 read, write 仅落在 `V2-del/` 与仓库外 `/tmp/v2-del-probe/probe.py`; 无 git 写操作 |
| 开工自查 | 自己核对了 HEAD 与 `git status` (`V1-perf/REPORT.md` §0) | 同 (`V2-del/00-env.txt`) |
| 开工 / 结束 | 00:29:22 / 00:30:35 | 00:30:00 / 00:31:23 |

没有把实现对话、作者设计理由或作者自证结论交给任何验收者; 派工单只含目标提交、判据原文、证据目录、方法路径、写入授权与第 7/8 步核对规则.

说明: 两名验收者启动时我使用了 pi 的 `--approve` (信任工程内文件). 该仓库全部 7 个受跟踪文件我在派工前已逐个读过, 内容是 fixture 数据与 app.py, 不存在未审阅的工程级信任对象. 这一条如实记在这里.

### 4.4 方法加载与原始材料归属

- verify-perf 用 read 工具读了 `.agents/skills/benchmark-checklist/SKILL.md` 并按节次落实 (待核验结论句、计时范围、负载与核数、5 次重复与中位数/极差、错误计数、工作量与输出正确性). 记录: `V1-perf/REPORT.md` §2.
- verify-del 用 read 工具读了 `.agents/skills/blast-radius/SKILL.md`, 给出三个关键安全事实与证据级别: F1 purge 不接触伙伴 (级别 2–3), F2 purge 后本机无 r1 正文残留 (级别 4, 有可失败的证明脚本与退出码 1 的负向对照), F3 仓外副本不可读 (未证实, 写明缺权限与入口). 记录: `V2-del/REPORT.md` §4, 脚本 `04-probe.py` + `04-probe.out` + `05-probe-negctl.out`.
- 两项方法都是该组实际验收者自己点名加载, 指挥者没有代调用.

### 4.5 时间线 (可复核)

00:27:59 指挥会话创建 → 00:29:22 verify-perf 会话 → 00:29:48 init → 00:29:54–00:29:56 5 次 export → 00:30:00 verify-del 会话 → 00:30:16 AC-003-1 → 00:30:19 purge + dump → 00:30:33/00:30:36 证明脚本与负向对照 → 00:30:35 V1 报告完成 → 00:31:23 V2 报告完成 → 00:33:05 runtime 快照 → 00:33:07 清理.

## 5. 写入与清理记录

批准范围 (用户在派工前给出): 测试实例 `runtime/` 下 (含 `runtime/data` 与 `runtime/*.jsonl` 导出文件); 允许运行 `record add/purge/export` 与 init; 清理 `runtime/`; 未批准修改仓库内其他文件.

| 时间 | 执行者 | 对象 | 操作 | 结果 |
| --- | --- | --- | --- | --- |
| 00:29:48 | verify-perf | `runtime/data/` | `python3 app.py init --data-dir runtime/data` | 退出码 0, `init-ok`; records.jsonl 59 B, outbox 166 B (`V1-perf/01-init.txt`) |
| 00:29:54–00:29:56 | verify-perf | `runtime/export.jsonl` | 5 次 `export --rows 20000` | 每次 908890 B / 20000 行, sha 全同 (`V1-perf/02-run-5x.log`) |
| 00:30:2x | verify-perf | `runtime/export-croscheck.jsonl` | 1 次带 `/usr/bin/time -v` 的交叉校验写入 | 退出码 0 (`03-croscheck-time-v.log`) |
| 00:30:16–00:30:19 | verify-del | `runtime/data/records.jsonl`, `runtime/data/outbox/replication-log.jsonl` | `record-list` (只读), `record-purge r1` (写) | records 59→29 B, outbox 166→246 B (`V2-del/REPORT.md` §6) |
| 00:30:12–00:30:50 | verify-del | 仓库外 `/tmp/v2-del-probe/` | 写证明脚本与临时副本; 00:30:50 删除 `negctl*` 副本 | 脚本保留 (`probe.py`), 副本已删 (`V2-del/REPORT.md` §2, §7) |
| 00:33:07 | 指挥者 | `runtime/` | `rm -rf runtime` | 退出码 0; `runtime` 已不存在 (`11-cleanup.txt`) |

清理结果: `runtime/` 完整删除, 无残留 (清理前快照 `10-runtime-before-cleanup.txt`: 4 个文件, 4 个 sha256; 清理后 `ls` 报 No such file or directory). 仓库外 `/tmp/v2-del-probe/` 只剩 `probe.py` 一份脚本 (报告中引用的原件, 不含数据). 证据目录保留, 属本轮期望产物. 没有留下需要单列的残留对象.

清理由指挥者执行的理由: 两组共用同一 `runtime/`, 任一组自行删除会破坏另一组仍在用的资源; 该动作不属于运行被验产品入口.

## 6. 覆盖范围与非产品判据注记

- 覆盖: PRODUCT.md 验收标准节的全部 3 个场景 + 业务规则节唯一的审计 BR, 共 4 条, 无遗漏.
- 未覆盖/不外推: 性能数字只在 `/tmp` (tmpfs) 上、20000 行、无 fsync 持久化的条件下成立, 不外推到物理盘/冷缓存/更大数据量/并发; 仓外副本的真实状态; 伙伴回执的消费; `record-add` 的伙伴通道 (授权允许但非本轮判据, 未跑); purge 后重新 init 是否让 r1 复活 (未跑, 只作推断, 不计入结论).
- 非产品判据: 内部代码划分、模块拆分、`app.py` 函数结构等技术事项不在本轮判据内, 既不判通过也不判失败, 交回既有评审与执行验证.
- 本轮源文件未变: 除本轮证据目录 `docs/changes/vault/evidence/r1-ea94082/` 下新增的验收输出外, 源码与 Spec 未变 (`git status --porcelain` 只有 `?? docs/changes/vault/evidence/`, `git diff --stat` 为空, HEAD 仍为 ea940821115424b7eb619e985b2304f2b61e9d1d, 见 `11-cleanup.txt`). 这不等于整个工作区"干净": 证据目录里的文件本身就是相对起始提交的新增改动.

## 7. 结论仍需用户确认

本报告是独立验收的材料与逐项判断, 不是正式人工验收, 也不代表交付完成或用户验收关闭. 4 项中 2 项未验证 (AC-002-1 仓外子句, BR-001 回执部分), 原因已分列为"缺产品规则"与"权限/环境缺口"; 需要用户逐项确认, 并由既有决策流程补齐回执载体与仓外举证方式后再复验这两项.
