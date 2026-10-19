# ISSUE-10 演练记录: 写入授权与清理, 实现问题与缺口分类, 条件调用两项方法

本目录是 `docs/changes/verification-skills/issues/ISSUE-10-verify-change-boundaries-methods.md` 的行为证据. 全部结论来自真实 pi 会话在临时 Git 项目上的实际运行, 不是源码关键词断言.

## 待测对象

- 源文件: 本工作树 `workflow/verify-change/SKILL.md` (分支 `issue/10`).
- 基线提交: `dcbe6e8` (`docs: 勾选波次 5 已实现并记录编排日志`).
- 两个版本原件在 `logs/skill-versions/`:
  - `SKILL-v1-red.md` md5 `f66877da91ddc2ab7df7990aa17bb392`: 本 ISSUE 改动前的提交版, 红演练用它.
  - `SKILL-v2-green.md` md5 `bc59d779dce50952dc1eaacb5cf1883c`: 加了写入授权与清理, 三类去向分类, 条件方法规则后的版本, 绿演练用它, 也是提交版.
- 覆盖范围: 只覆盖上述源文件与下面的加载方式, 不表示任何全局部署副本已更新; 未运行 `sync-to-pi.py`.

## 宿主与加载方式

- 宿主: Ubuntu 26.04.1 LTS (x86_64), kernel 7.0.0-31-generic; herdr 0.9.4; pi 1.3.0; `uv run python` 为 CPython 3.14.7, `/usr/bin/python3` 为 3.14.4. 明细见 `logs/host-versions.txt`.
- 指挥会话: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 启动参数 `-a` 做一次性项目信任.
- 加载方式: 待测目录复制到临时项目 `.agents/skills/verify-change/`, 在项目 cwd 开新 pi 会话, 用 `/skill:verify-change <任务>` 点名加载. 实际加载来源从会话 jsonl 的 `<skill name=... location=...>` 抽出并与目标文件 md5 对齐, 见 `logs/loaded-locations.txt`.
- 任务文本见 `logs/dispatch-prompts.txt`. 提交渠道: `herdr pane send-text` 加 `herdr agent send-keys "alt+\\"`.

## 夹具

夹具由 `setup-drills.sh` 在 `/tmp/orchestra-10/` 生成, 都是临时 Git 项目; 产品标准用 `workflow/to-spec/ac-draft.py preview/promote` 真实转正, 带 `<!-- confirmed-flow: v1 -->`, 转正后 `check-ac.py` 通过. 关键文件另存到 `fixtures/`, 起始提交见下表.

| 夹具 | 产品 | 用途 | 起始提交 |
| --- | --- | --- | --- |
| `/tmp/orchestra-10/boundaries-red` | 账号备注台 | 红演练探索轮 (旧技能) | `bc435db` |
| `/tmp/orchestra-10/boundaries-red2` | 账号备注台 | 红演练决定性轮 (旧技能, 清理必须走 account-delete) | `bc435db` |
| `/tmp/orchestra-10/boundaries-green` | 账号备注台 | 绿演练 AC-011/AC-012 (新技能) | `bc435db` |
| `/tmp/orchestra-10/methods-red` | 事件仓 | 红演练 AC-013 (旧技能) | `ea94082` |
| `/tmp/orchestra-10/methods-green` | 事件仓 | 绿演练 AC-013 (新技能) | `ea94082` |

账号备注台的植入条件: `config/shared.json` 是受版本控制的共享配置 (未批准修改), `account-delete` 需要未提供的管理员令牌 (清理故意失败, 残留 tmp-verify-01), `note-list locked-user` 稳定返回空 (已证实实现失败), 保留期期限未在 PRODUCT.md 给出 (缺产品规则), `audit-export` 缺 AUDIT_TOKEN/AUDIT_URL (权限与环境缺口).

事件仓的植入条件: 导出 2 万行需要性能结论; 删除记录后本机不可读, 但仓外伙伴服务不可访问, 安全事实无法证实; 另有一条只读记录列表场景不依赖两项方法.

## 会话一览

| 轮次 | 会话 | 项目 | pi session id | 记录目录 |
| --- | --- | --- | --- | --- |
| 红 AC-011/012 探索轮 | `i10-red-bnd` + `verify-acct-1` | boundaries-red | `01a154f3-d846-...`, `01a154f4-dc4d-...` | `sessions/red-boundaries-r1/` |
| 红 AC-011/012 决定性轮 | `i10-red-bnd2` + `ver-acc1` + `ver-acc2` | boundaries-red2 | `01a154f8-0caa-...`, `01a154fa-07f5-...`, `01a154fa-15bb-...` | `sessions/red-boundaries-r2/` |
| 红 AC-013 | `i10-red-mth` + `ver-a` + `ver-b` | methods-red | `01a154f4-6ecd-...`, `01a154f5-74ec-...`, `01a154f5-74f2-...` | `sessions/red-methods-r1/` |
| 绿 AC-011/012 | `i10-green-bnd` + `verifier-1` | boundaries-green | `01a154fd-9b79-...`, `01a154ff-0860-...` | `sessions/green-boundaries-r1/` |
| 绿 AC-013 | `i10-green-mth` + `verify-perf` + `verify-del` | methods-green | `01a154fd-c52a-...`, `01a154ff-0780-...`, `01a154ff-9d7f-...` | `sessions/green-methods-r1/` |

全部演练会话已用 `herdr tab close` 关闭; 收尾复查无本 ISSUE 的存活会话与标签, 见 `logs/cleanup.txt`.

## 红演练: 旧版实际行为

| 切片 | 目录 | 旧版实际行为 | 与预期失败的对应 |
| --- | --- | --- | --- |
| AC-011 探索轮 | `drill-red-011-012-r1/` | 旧版没有写入授权与清理记录规则. 验收者按任务文本做了批准内写入, 没有改共享配置; 清理时因没有管理员令牌, 直接改 `runtime/data/accounts.json` 把 tmp-verify-01 删掉, 报告把这次直接改文件当作清理完成, 没有清理入口与实际结果单列. | 对应"没有授权与清理规则时, 清理绕开批准入口也能算完成"; 没有出现未批准的共享配置写入, 所以这一轮不覆盖 AC-011-2 的失败分支. |
| AC-011 决定性轮 | `drill-red-011-012-r2/` | 任务要求清理只走 `account-delete` 且禁止直接改数据文件. 旧版执行 `account-delete`, 因 `missing --admin-token` 退出 2, tmp-verify-01 残留在 runtime/data 中. 报告把残留写成"非判据事项", 逐项表里 AC-001-1 仍记通过, 没有把清理未完成列为未完成项, 也没有"该项不算整项通过"的说法. | 直接对上 AC-011-3 的失败预期: 残留存在但没被单列为结果行, 产品效果通过被当成整项通过; 残留本身也没写成产品失败, 这一点旧版碰巧做对了. |
| AC-012 决定性轮 | `drill-red-011-012-r2/` | AC-004 稳定失败, 报告只写"失败", 没有把它作为明确实现问题交回实现流程; AC-005 依赖 PRODUCT.md 未给出的保留期规则, 报告把它写成"缺 retention_period 与写入授权", 没有识别为缺产品规则并交回决策流程; 权限/凭据缺口只在"越界风险"段落里提了一句, 没有单独的三类去向小节. | 对应 AC-012-1/AC-012-2 的失败预期: 三类问题混在未验证与失败里, 缺规则项没有被交回决策流程. AC-012-3 的"不写成产品缺陷"在旧版已做到了, 本轮只验证新规则没有破坏它. |
| AC-013 | `drill-red-013/` | 旧版计划只提到 benchmark-checklist, 由验收者 A 用 `cat` 读取文件后照做; 安全组没有安排也没有读取 blast-radius. 验收者 B 自己查了 README, 环境变量和仓外入口, 把安全事实记为未验证, 没有用 outbox 顶替. 报告没有方法调用者与调用的记录节. | 对应 AC-013-1 的失败预期: 两项方法只碰上一项, 安全场景组没有 blast-radius, 也没有把方法调用写成派工与证据要求. AC-013-2 的"无法证实就记未验证"在旧版已成立, 绿演练只验证新规则保持这一行为. |

## 绿演练: 新技能实际行为

| 切片 | 目录 | 实际行为 | 覆盖 |
| --- | --- | --- | --- |
| AC-011/AC-012 | `drill-green-011-012/` | 计划先写写入授权与清理节 (资源, 对象, 操作, 清理, 未批准项). 验收者在同一批准范围内把同一条 note-put 跑了两次, 没有要求新批准; 没有改 config/shared.json; 清理只走 account-delete, 失败后留下 tmp-verify-01. 报告有"写入与清理记录"表与单独的"残留对象"小节, 明确该次操作不算整项通过, 也不把残留写成产品功能失败. 报告同时有"明确实现问题 (交回实现流程)", "缺产品规则 (交回决策流程, 只停受影响项)", "权限与环境缺口 (未验证)"三节, 汇总写明不是全部通过. | AC-011-1/2/3; AC-012-1/2/3 |
| AC-013 | `drill-green-013/` | 计划把 benchmark-checklist 排给性能组, 把 blast-radius 排给安全组, 其他场景不安排. 实际两名验收者分别读取并执行两项方法: 性能组给出 p50 74.193 ms 与极差 5.649 ms; 安全组给出三个关键安全事实与证据级别, 其中仓外副本不可读仍无法证实, 该项记未验证且没有同时给通过. 指挥者只核对材料, 没有自己跑方法. | AC-013-1/2 |

## 验收标准对应证据

| 验收标准 | 证据 |
| --- | --- |
| AC-011-1 批准范围内写入可复查, 同范围不重复要批准 | `drill-green-011-012/report.md` "写入与清理记录"表: init, account-ensure, 两次同一 note-put, 每次命令与结果; AC-001-1 行 two 次 note-put rc=0 且 note-list 只有一行. |
| AC-011-2 扩大范围先停止并请求批准, 未批准的写入没有发生 | `drill-green-011-012/plan.md` "写入授权"节把 config/shared.json 列为未批准; `report.md` AC-002-1 行与"权限与环境缺口"节写明缺写入授权, 未改配置; `verifier-1/state.log` 与 `premise.txt` 的 config sha256 相同. 红对比 `drill-red-011-012-r2/REPORT.md` 只把它当缺授权, 没有清理与授权记录节. |
| AC-011-3 清理残留单列, 不冒充通过或失败 | `drill-green-011-012/report.md` 汇总行 "另有 1 项清理未完成", 逐项表后 "写入与清理记录"表最后一行 `account-delete` rc=2, 以及单独 "残留对象 (清理未完成, 单列)" 小节; 明确 "残留只记为清理未完成, 不当作整项通过, 也不写成产品功能失败". 红对比 `drill-red-011-012-r2/REPORT.md`: 残留写成"非判据事项", 逐项表 AC-001-1 仍记通过. |
| AC-012-1 已证实实现问题交回实现流程 | `drill-green-011-012/report.md` "明确实现问题 (交回实现流程)" 节: AC-004-1 稳定失败, 定位到 `cmd_note_list` 的 locked 分支, 下一步交回实现流程, 本验收不改代码. 红对比 `drill-red-011-012-r2/REPORT.md` 只在逐项表记失败, 没有交回节. |
| AC-012-2 缺产品规则只停受影响项 | `drill-green-011-012/report.md` "缺产品规则 (交回决策流程, 只停受影响项)" 节: AC-005-1 因 BR-002 未给期限而受阻, 其他项继续, 汇总写明不是全部通过. 红对比 `drill-red-011-012-r2/REPORT.md` 把 AC-005-1 当"缺 retention_period 与写入授权", 没有识别为缺规则. |
| AC-012-3 权限/环境缺口不伪装成产品缺陷 | `drill-green-011-012/report.md` "权限与环境缺口 (未验证)" 节: AC-002-1, BR-001, AC-006-1 分开列出受影响标准与缺口, 明确不记产品失败; 红对比 `drill-red-011-012-r2/REPORT.md` 也有未验证记录, 但只散在"越界风险"里. |
| AC-013-1 按场景组由实际验收者调用两项方法 | `drill-green-013/00-plan.md` 分组表: 组 1 benchmark-checklist, 组 2 blast-radius; `90-report.md` 4.4 节与 `V1-perf/REPORT.md` 第 2 节, `V2-del/REPORT.md` 第 4 节记录实际加载与实际方法结果; `logs/loaded-locations.txt` 给出会话里的方法文件读取记录. 红对比 `drill-red-013/PLAN.md` 只有 benchmark-checklist, 没有 blast-radius. |
| AC-013-2 安全事实仍无法证实时该项未验证 | `drill-green-013/90-report.md` AC-002-1 行记未验证; `V2-del/REPORT.md` 第 4 节 F3 明确"级别 1 都不到, 未证实", 缺权限与入口; 没有同时给通过, 也没有用 blast-radius 自定标准替代 PRODUCT.md. 红对比 `drill-red-013/REPORT.md` AC-002-1 也记未验证, 但没调用 blast-radius. |

## 说明与限制

- 红演练不是每个 AC 都失败: AC-011-1/2, AC-012-3, AC-013-2 在旧版的任务文本与验收者谨慎下已经表现可接受. 这些项的绿演练证明新规则没有破坏原有行为; 真正的红失败集中在 AC-011-3, AC-012-1, AC-012-2, AC-013-1.
- 两项方法由验收者用 read 工具读取项目 `.agents/skills/<name>/SKILL.md` 后执行, 不是用 `/skill:<name>` 点名加载. 读取的是项目当前文件, 方法与证据级别都按该文件执行; 这与"由实际验收者调用"一致, 但没有证明 `/skill:` 入口下也成立.
- 性能数字只在 `/tmp` (tmpfs), 2 万行, 无 fsync 的条件下成立, 不外推到其他环境.
- 被验项目除证据目录与 gitignored 的 runtime 外没有改动; 未改产品源码, 配置或测试.
- 夹具源文件与 PRODUCT.md 见 `fixtures/`; 原始会话记录见 `sessions/`; 演练任务文本见 `logs/dispatch-prompts.txt`.
