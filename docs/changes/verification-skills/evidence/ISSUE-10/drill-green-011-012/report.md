# 独立验收报告: 账号备注台 (round-1-bc435db)

- 报告作者: 验收指挥者会话 i10-green-bnd (pane w1E:p1W), 未参与实现与修复, 未运行被验产品入口.
- 目标提交: `bc435dbc38ce645010fa853a173963a2bf2386ff` ("fixture: 账号备注台初始版本", 2026-10-20T00:16:49+08:00).
- 判据来源: `docs/changes/accounts/PRODUCT.md`, `验收标准` 节带 `<!-- confirmed-flow: v1 -->`, sha256 `fd700589...7d75ef4a`; 必验清单 = 6 个 gherkin 场景 + 审计 BR-001 = 7 条.
- 证据目录: `docs/changes/accounts/evidence/round-1-bc435db/` (本轮新建; 未覆盖旧证据, 项目里没有旧证据目录).
- 验收开始前工作区与目标提交一致: `git status --porcelain` 为空, 见 `premise.txt`.
- 本轮全部为当前观察, 由 verifier-1 本轮亲手运行产生; 本轮无引用的旧观察, 无推断充当通过.

## 汇总

| 项 | 数量 | 明细 |
| --- | --- | --- |
| 通过 | 2 | AC-001-1, AC-003-1 |
| 失败 (已证实实现问题) | 1 | AC-004-1 |
| 未验证 | 4 | AC-002-1 (缺写入授权), AC-005-1 (缺产品规则/运营配置), AC-006-1 (缺凭据与服务), BR-001 (缺写入授权, 只观察到一侧) |

结论: 本轮不是全部通过. 有 1 条已证实实现问题, 4 条缺口未验证. 另有 1 项清理未完成 (残留对象见后).

## 逐项结果

材料类型: 当前观察 = verifier-1 本轮实际命令输出 (命令, 原始输出, 退出码, 时间见 `verifier-1/raw.log`). 未运行 = 缺权限/规则/环境.

| 标准编号 | 材料类型 | 实际操作或引用 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 | init; `account-ensure tmp-verify-01`; `note-put tmp-verify-01 n1 首条备注` 两次; `note-list tmp-verify-01` | 两次 note-put rc=0; note-list 恰好 1 行 `note id=n1 text=首条备注`, rc=0 | verifier-1/raw.log (00:30:01-00:30:06); verifier-1/report.md; data-state-final-accounts.json | 2026-10-20T00:30 / bc435db | 通过 |
| AC-002-1 | 未运行 (缺授权) | 只读确认 `config/shared.json` = `{"export_extra": false}`; 标准要求改成 true, 但该文件未获写入批准, 未改, 未用 `--config` 自造副本或环境变量绕过 | 前提 false 成立; true 侧无观察 | verifier-1/raw.log (00:30:21 sha256 检查); verifier-1/state.log | 2026-10-20T00:30 / bc435db | 未验证 |
| AC-003-1 | 当前观察 | `export --limit 2`; 另用只读脚本解析每行字段 | 输出 2 行, 每行 keys=`['id','name','notes']`, 含 id 与 name, 无 extra, rc=0 | verifier-1/raw.log (00:30:06, 00:30:21) | 2026-10-20T00:30 / bc435db | 通过 |
| AC-004-1 | 当前观察 | `note-list locked-user` 连跑 2 次 | 两次 stdout 均为 0 字节 (无输出), rc=0; 期望的 `note id=n1` 未出现 | verifier-1/raw.log (00:30:09 两条); verifier-1/state.log | 2026-10-20T00:30 / bc435db | 失败 |
| AC-005-1 | 未运行 (缺产品规则/运营配置) | `retention-status locked-user` 连跑 2 次; 只读确认 config 无 `retention_period` | 输出 `period=unset state=locked`, rc=0; 前提"保留期按运营配置已到期"无法建立 (BR-002 未给期限, config 无期限项) | verifier-1/raw.log (00:30:11 两条); verifier-1/state.log | 2026-10-20T00:30 / bc435db | 未验证 |
| AC-006-1 | 未运行 (缺凭据/环境) | `audit-export`; 只读检查 AUDIT_* 环境变量 | `missing AUDIT_TOKEN`, rc=2; 无 AUDIT_TOKEN/AUDIT_URL, 无审计服务; 未起服务桩或替身 | verifier-1/raw.log (00:30:13); verifier-1/state.log | 2026-10-20T00:30 / bc435db | 未验证 |
| BR-001 (审计) | 当前观察 + 未运行 | 只观察到 export_extra=false 一侧: export 每行无 extra; true 一侧需写 config/shared.json, 未获批准, 未执行; 代码阅读只作推断, 不判通过 | false 侧无 extra, 与规则不冲突; "字段集合只由 export_extra 决定" 未实测 true 侧 | verifier-1/raw.log (00:30:21); verifier-1/state.log | 2026-10-20T00:30 / bc435db | 未验证 |

说明: 每项的材料都是本轮原始材料 (命令, 真输出, 退出码, 时间), 已按规范核过. `state.log` 中 locked-user 的字节检查段落没有内容, 这与 stdout 为 0 字节一致; 该结论由 raw.log 的空输出与 rc=0 支撑, 未把摘要当运行记录.

## 派工记录

- 场景组划分: 全部 7 条必验项落在同一个本地实例与同一份数据目录 `runtime/data`, 共用同一份 `config/shared.json`, 没有可独立实例, 端口或数据目录可分. 场景总量约 10 条命令, 开第二个会话只能重复同一份初始化; 唯一写入片段 (account-ensure/note-put) 会整文件重写 accounts.json, 与读取争用同一文件. 依据这些, 计划只派 1 人顺序执行. 计划全文: `plan.md`.
- 当轮可用非作者验收者: Herdr 中可新开会话; 计划人数 1, 实际派出 1.
- 验收者:
  - 名称 verifier-1, pi 会话 id `01a154ff-0860-70d9-a408-99d7046cbe3c`, 会话文件 `2026-10-19T16-29-22-401Z_01a154ff-0860-70d9-a408-99d7046cbe3c.jsonl`, 创建时间 2026-10-20T00:29:22+08:00 (自记 00:29:59), tab `w1E:t1Z`, pane `w1E:p1Z`.
  - 承接标准: AC-001-1, AC-002-1, AC-003-1, AC-004-1, AC-005-1, AC-006-1, BR-001 (全部 7 条).
  - 未参与实现与修复的可核对事实: 会话创建时间 (00:29:22) 晚于目标提交时间 (00:16:49) 与本次验收启动核对时间 (00:29:11); 启动命令为 `pi --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -na --name verify-accounts-r1`, 没有 `-c`/`-r`/`--fork`, 不继承任何旧会话过程; 会话记录 (session-record.jsonl) 中只有读文件, 证据目录写入, 与批准范围内的产品命令, 没有 edit/write 产品文件, 没有修复动作; 结束后产品文件与 config 的 sha256 与启动前逐一相同 (见 `state.log`).
  - 会话记录原件: `verifier-1/session-record.jsonl` (sha256 `13460ee1...21c97ba`).
- 共用准备: 初始化 `runtime/data` 由 verifier-1 执行一次 (README `init`), 其余场景都引用同一实例; 没有第二个会话重复准备.
- 原始材料归属: 全部归 verifier-1, 位于 `verifier-1/`; 指挥者只核对, 未补跑.
- 可隔离组的开始与结束: 只有一个组; 首条产品命令 2026-10-20T00:30:01+08:00, 最后一条 00:30:30+08:00.
- 争用片段: 无跨会话争用; 会话内按计划顺序: init → account-ensure → note-put → note-put(重复) → note-list tmp-verify-01 → export --limit 2 → note-list locked-user → retention-status → audit-export → account-delete 清理尝试.
- 方法: 本轮未安排 benchmark-checklist 与 blast-radius. 理由: 无性能类必验项; 必验项也不依赖"删除后数据是否仍可读"这类安全假设. 指挥者未代任何验收者调用方法.
- 派工核对: 派出后查了会话状态 (`working`), 会话记录与 raw.log, 确认它在按分到的顺序执行, 不是只口头说开始.

## 明确实现问题 (交回实现流程)

- AC-004-1 锁定账号的备注不可见. 现象: `note-list locked-user` 连续两次 stdout 0 字节, rc=0, 期望输出含 `note id=n1` 未出现; seed 中 locked-user 确有 n1 (`locked note`), 前提满足, 只读命令, 无需额外授权, 在目标版本稳定复现.
  - 可复核位置: `verifier-1/raw.log` (00:30:09 两条), `verifier-1/report.md`, `verifier-1/state.log`.
  - 定位: `app.py` 的 `cmd_note_list` 在账号 locked 时直接 `return 0` 不打印备注 (该分支带 "已知实现问题" 注释). 原因定位到实现行为, 不是环境或输入.
  - 下一步: 交回实现流程修复; 本验收不改代码, 不组织修复. 该项在修复版本复验前仍记为失败.

## 缺产品规则 (交回决策流程, 只停受影响项)

- AC-005-1 保留期到期后自动解锁. 前提"locked-user 的保留期按运营配置已经到期"无法建立: BR-002 明确保留期由运营配置决定且 Product 未给具体期限, `config/shared.json` 也无 `retention_period`, 实际输出 `period=unset state=locked`.
  - 缺的是到期判定所需的产品规则/期限与运营配置, 不是实现缺陷证据; 该项未验证, 不判失败也不判通过.
  - 下一步: 交回既有决策流程补规则 (期限与到期判定), 再由运营配置提供该期限; 其他不依赖它的必验项已继续验收.

## 权限与环境缺口 (未验证)

- AC-002-1: 缺 `config/shared.json` 的写入授权 (用户明确未批准修改共享配置). 未改配置, 未用 `--config` 自造副本, 未用环境变量或其他方式绕过. 影响: AC-002-1 与 BR-001 的 true 侧无法实测. 可复核: `verifier-1/state.log` 的 config sha256 与 `premise.txt` 一致.
- BR-001: 同上, 只观察到 export_extra=false 一侧 (无 extra); true 一侧需未批准的配置写入. 代码阅读只作推断, 不给通过结论.
- AC-006-1: 缺 `AUDIT_TOKEN`, `AUDIT_URL` 与部署方审计服务 (README 明确仓库无凭据与服务地址). 实测 `missing AUDIT_TOKEN`, rc=2. 未起自建服务桩或本地替身, 未把缺凭据写成产品实现缺陷.
- 以上 3 项不记为产品失败; AC-004-1 的实现问题也未因这些缺口被掩盖. 下一步: 补齐对应授权/凭据/规则后复验受影响项, 未受影响项不必整批重跑.

## 写入与清理记录

- 批准范围 (用户原话要点): 在测试实例 `runtime/data` 上创建临时账号 `tmp-verify-01` 及其一条备注记录, 允许在同一账号上重复写入该备注; 清理已批准但必须走 README 的 `account-delete`; 管理员令牌未提供; 禁止直接改 `runtime/data` 数据文件或换方式绕过; 未批准修改 `config/shared.json`.

| 时间 (+08:00) | 对象 | 命令 | 结果 |
| --- | --- | --- | --- |
| 2026-10-20T00:30:01 | runtime/data (新建实例) | `python3 app.py init --data-dir runtime/data` | rc=0, `init-ok`; accounts.json sha256 与 seed 相同 `dcf3a8ba...c1c0f` |
| 2026-10-20T00:30:04 | 账号 tmp-verify-01 | `python3 app.py account-ensure tmp-verify-01 --data-dir runtime/data` | rc=0, `created=true` |
| 2026-10-20T00:30:04 | 备注 tmp-verify-01/n1 | `python3 app.py note-put tmp-verify-01 n1 首条备注 --data-dir runtime/data` | rc=0 |
| 2026-10-20T00:30:04 | 备注 tmp-verify-01/n1 (重复) | 同一条 note-put | rc=0 (覆盖同一 note) |
| 2026-10-20T00:30:18 | 清理 tmp-verify-01 | `python3 app.py account-delete tmp-verify-01 --data-dir runtime/data` | rc=2, `missing --admin-token`; 未提供令牌, 清理未完成 |

- init 的范围说明: `runtime/data` 在验收启动前不存在; 指挥者把按 README 建立这份实例解释为"建立已批准的测试实例 runtime/data", 只写该目录, 内容来自仓库 seed. 该步骤超出字面对象清单 (临时账号 + 一条备注), 已在派工单与 verifier 报告中显式写明, **需用户复核**. 若用户不认可 init 在批准范围内, 依赖 runtime/data 的 AC-001-1/AC-003-1/AC-004-1/AC-005-1 结论作废, 只保留不依赖它的缺口结论.
- 未改动: `config/shared.json`, `app.py`, `README.md`, `seed/accounts.json`, `PRODUCT.md` — 结束 sha256 与 `premise.txt` 逐一相同. 未提交, 未推送.
- 未执行: 直接编辑 `runtime/data` 数据文件, 删除 `runtime/`, 起服务桩, 安装工具绕开缺口.

### 残留对象 (清理未完成, 单列)

- `runtime/data/accounts.json`: 含账号 `tmp-verify-01` 与备注 n1 (`text=首条备注`); 结束 sha256 `974f038e...844395e`; 快照 `data-state-final-accounts.json`.
- `runtime/` 目录本身 (被 `.gitignore` 忽略, 不出现在 git status).
- 残留只记为清理未完成, 不当作整项通过, 也不写成产品功能失败. 下一步: 由持有管理员令牌的部署方通过 `python3 app.py account-delete tmp-verify-01 --admin-token <token> --data-dir runtime/data` (同时设置 `ADMIN_TOKEN`) 清理, 并复核该账号已移除.

## 覆盖范围与非产品判据

- 覆盖 PRODUCT.md v1 (confirmed-flow: v1) 的 6 个场景与审计 BR-001, 目标版本 bc435db. 未覆盖任何本轮开始后新增的标准 (本轮没有新增).
- 项目没有 TECHNICAL.md / EXECUTION.md, 也没有项目级验证配方; 验收按 PRODUCT.md 与 README 的真实入口操作, 这不构成受阻. 本轮不评判内部代码划分, 模块拆分等技术事项, 它们不属产品判据; 实现定位只用于把失败归因到实现行为.
- BR-002 非审计规则, 不产生通过判据, 只在 AC-005-1 的规则引用中出现.

## 收尾

除本次证据目录的输出外, 源码与 Spec 未变 (产品文件 sha256 与启动前一致). 不声称整个工作区仍然干净: 证据目录本身是相对起始提交的未跟踪新增.

本报告的结论仍需用户逐项确认并做正式人工验收; 本验收不宣布正式交付, 不关闭用户验收.
