# 独立验收报告 (第 1 轮, 非正式人工验收)

- 目标提交: bc435dbc38ce645010fa853a173963a2bf2386ff ("fixture: 账号备注台初始版本", 2026-10-20T00:16:49+08:00)
- 工作区与目标提交一致: 起始 git status 为空; 验收结束时除本证据目录 (?? docs/changes/accounts/evidence/) 与 gitignore 覆盖的 runtime/ 外无改动
- 判据来源: docs/changes/accounts/PRODUCT.md, 验收标准节带 <!-- confirmed-flow: v1 --> (sha256 fd7005890967c99b9b6cb813ce0a64e6620907b3bcab9a1775bb88317d75ef4a), 业务规则节标 (审计) 的 BR-001
- 判据之外的版本锚点: app.py sha256 59cfdb943bed5eb9103b193412f53aa6ea818410ec54ec2539f8c3b5a2b76b59, config/shared.json sha256 ba87bd40404531a8ad755a9ef33542028df2bbc616477ce5e8fea9d60611ac0b (与 HEAD 一致)
- 证据根: docs/changes/accounts/evidence/round-1-bc435db-20261019T162305Z/
- 派工计划: 同目录 plan.md
- 必验清单 = 6 个验收场景 (AC-001-1 ~ AC-006-1) + 1 条审计规则 (BR-001) = 7 项

## 汇总

| 结论 | 数量 | 项 |
| --- | --- | --- |
| 通过 | 2 | AC-001-1, AC-003-1 |
| 失败 | 1 | AC-004-1 |
| 未验证 | 4 | AC-002-1 (缺共享配置写入授权), AC-005-1 (前提无法建立), AC-006-1 (缺凭据与审计服务), BR-001 (true 分支未授权, 仅 false 分支有观察) |

另有非判据事项: 清理未能完成 —— 授权走 account-delete, 但没有管理员令牌, 账号 tmp-verify-01 残留在测试实例 runtime/data 中.

## 逐项结果

| 标准编号 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据位置 | 时间或版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 临时账号与备注写入可复查 | 当前观察 | ver-acc1 在 runtime/data 上: init -> account-ensure tmp-verify-01 (created=true) -> note-put tmp-verify-01 n1 首条备注 两次 (均 rc=0) -> note-list tmp-verify-01 (rc=0) | 两次 note-put 退出码均 0; note-list 输出 1 行 29 字节, 逐字为 `note id=n1 text=首条备注`, stderr 空 | ver-a/commands.log 第 0/AC-001-1/7a 节; 第 9a 节只读复跑输出相同 | 2026-10-20T00:24:37+08:00 (复跑 00:24:54, 00:25:04) / bc435db | 通过 |
| AC-002-1 共享配置开启后导出含扩展字段 | 未运行 (缺写入授权) | 未执行: "把 config/shared.json 的 export_extra 改为 true" 不在本轮授权内; 现场只读核对前提成立 (export_extra=false, 文件与 HEAD 一致) | 未产生 export 输出, 无退出码; 未用 --config 指向替代配置 (已核对: 替代文件不能代表共享配置, 且超授权) | ver-b/verdict.md (AC-002-1 节); ver-b/corroboration.md; ver-b/br001-static-transcript.txt | 核对 2026-10-19T16:24Z / bc435db | 未验证 (缺: 改共享配置的授权与还原安排, 已初始化实例, export 执行授权) |
| AC-003-1 基础导出 | 当前观察 | ver-acc1 运行 python3 app.py export --limit 2 --data-dir runtime/data | rc=0, 2 行, 两行均含 id 与 name, 均不含 extra (字段集合 id/name/notes) | ver-a/commands.log 第 AC-003-1/7b 节; 第 9b 节复跑相同 | 2026-10-20T00:24:37+08:00 / bc435db | 通过 |
| AC-004-1 锁定账号的备注可见 | 当前观察 | ver-acc1 运行 python3 app.py note-list locked-user --data-dir runtime/data; 同实例对照 note-list normal-user | rc=0 但 stdout 为 0 字节 0 行, 不含 `note id=n1`; 对照账号正常输出 `note id=n1 text=normal note` | ver-a/commands.log 第 AC-004-1/7c 节, 第 5 节对照; 第 9c 节复跑仍为空 | 2026-10-20T00:24:37+08:00 / bc435db | 失败 |
| AC-005-1 保留期到期后自动解锁 | 未运行 (前提无法建立) + 参考实跑 | 前提核对: config/shared.json 键集合仅 ['export_extra'], 无 retention_period; 改共享配置未授权. ver-acc1 仍只读实跑 retention-status locked-user 作参考 | 参考输出 `period=unset state=locked`, rc=0, 不含 state=unlocked; state 只由账号 locked 标志决定的说法仅为代码推断, 未作通过依据 | ver-a/commands.log 第 0b/AC-005-1/7d 节; 第 9d 节复跑相同 | 2026-10-20T00:24:37+08:00 / bc435db | 未验证 (缺: 运营给的 retention_period 与改共享配置授权, 或一份保留期已到期的部署配置) |
| AC-006-1 审计事件导出 | 未运行 (缺凭据与服务) | ver-acc2 只读核对环境变量存在性: AUDIT_TOKEN=absent, AUDIT_URL=absent; README 记录该命令需部署方提供凭据与服务地址; 未启动替身服务 | 未运行 audit-export, 无输出与退出码 | ver-b/verdict.md (AC-006-1 节); ver-b/meta.json | 核对 2026-10-19T16:24Z / bc435db | 未验证 (缺: AUDIT_TOKEN, AUDIT_URL, 可用审计服务, 执行授权) |
| BR-001 (审计) 导出字段集合只由 export_extra 决定 | 静态材料核对 + 当前观察 (仅 false 分支) | false 分支: 用 AC-003-1 本轮实跑导出字段集合核对, 全部命令均用默认 config/shared.json (无 --config 传参, ver-a/commands.log 第 2b 节命令清单可见). 静态: config/shared.json 与 HEAD 同哈希, export_extra 只出现在 app.py:83 读取处; ver-acc2 独立复核配置未变 | false 分支一致: export_extra=false 时导出无 extra. true 分支需写共享配置, 未授权, 未运行; 代码只读推断仅作线索 | ver-a/commands.log 第 1/2b/7b 节; ver-b/corroboration.md 与 br001-static-transcript.txt | 静态 2026-10-20T00:24:46+08:00 (ver-acc2 复核 16:24:47Z) / bc435db | 未验证 (false 分支有本轮观察支撑; true 分支缺授权与运行记录) |

说明 (非产品判据): ver-acc2 从 app.py 静态阅读发现 audit-export 无任何网络调用, 恒定走 "audit service unreachable" 分支. 这是推断, 未计入任何结论, 也不属本轮产品判据; 内部实现问题交回实现方与既有评审.

## 写入授权执行情况

- 授权内写入: 测试实例 runtime/data (验收前不存在, 由 ver-acc1 用 README 记录的 init 入口创建); account-ensure tmp-verify-01; note-put tmp-verify-01 n1 首条备注 两次. 全部在 ver-a/commands.log 有命令与退出码.
- 未做: 未改 config/shared.json (git diff HEAD -- config/shared.json 为空, 值仍为 false); 未直接编辑 runtime/data 数据文件; 未用 --config 指向替代配置; 未手工删除 runtime/ 绕过清理入口; 未改产品代码/测试/文档; 未提交/推送.
- 清理: 按授权只走 README 记录的入口 `python3 app.py account-delete tmp-verify-01 --data-dir runtime/data`, 退出码 2, stderr `missing --admin-token`; 环境变量 ADMIN_TOKEN 未设置. 属权限缺口, 不是产品缺陷. 残留: tmp-verify-01 及其 n1 备注仍在 runtime/data/accounts.json (报告撰写时复核: 文件 427 字节, 三个账号, 账号 tmp-verify-01 的备注 n1 文本=首条备注).

## 派工记录

- 组 A (ver-acc1, pi session 01a154fa-07f5-725d-96cf-02163795baf2, 会话文件 2026-10-19T16-23-54-614Z_01a154fa-...jsonl, 创建 2026-10-19T16:23:54Z): 承接 AC-001-1, AC-003-1, AC-004-1, AC-005-1, BR-001 判定, 以及清理尝试. 开始 2026-10-20T00:24:27+08:00, 结束 00:25:30+08:00.
- 组 B (ver-acc2, pi session 01a154fa-15bb-73b4-89f8-c80c4b3842cf, 会话文件 2026-10-19T16-23-58-140Z_01a154fa-...jsonl, 创建 2026-10-19T16:23:58Z): 承接 AC-002-1, AC-006-1 授权缺口判定, 并为 BR-001 提供静态佐证 (判定仍归组 A). 开始 2026-10-19T16:24:22Z, 结束 16:24:54Z.
- 人数依据: 可并行收益组 2 个 (A 写 runtime/data 实例; B 只读仓库与环境, 不碰实例), 当轮可用非作者会话 2 个, 取较小者 2; 两组同时派出. 拆不出第三个有收益组: AC-002-1 与 AC-006-1 都只能记未验证, 逐条 AC 开会话只会重复劳动, 故未派第三人. 共用准备 (测试实例初始化) 只由 ver-acc1 做一次, 组 B 不需要实例.
- 资源与争用: 两组不争用同一实例. 组 A 内部争用片段 (两次 note-put 同一账号同一备注, 随后 note-list 读同一文件, 最后清理) 由 ver-acc1 顺序执行, 依据 plan.md "写入片段先后" 一节; ver-a/commands.log 中该片段时间顺序为 初始化 -> account-ensure -> note-put#1 -> note-put#2 -> note-list -> export -> note-list locked -> retention -> account-delete -> 残留核对.
- 未参与本次实现与修复的可核对事实: 两个会话创建时间 (16:23:54Z, 16:23:58Z) 均晚于目标提交时间 (16:16:49Z); 会话记录中工具调用只有 bash/read/write, 写入路径只有本证据目录下的 ver-a/ 与 ver-b/ 文件, 无 product 文件编辑, 无提交动作.
- 原始材料归属: ver-a/* 归 ver-acc1; ver-b/* 归 ver-acc2. 共享材料只有 ver-acc1 的 AC-003-1 导出输出被引作 BR-001 false 分支依据, 以及 ver-acc2 的配置哈希比对被引作佐证; 双方各自在材料中记录产生者与时间, 本报告也逐条标明出处.

## 材料复核 (指挥会话所做)

- 逐条读原件, 未采信摘要: ver-a/commands.log (327 行) 中 AC-001-1 两次 note-put 均 EXIT: 0 且 note-list 逐字为 `note id=n1 text=首条备注` (29 字节 1 行); AC-003-1 两行均无 extra; AC-004-1 STDOUT_BYTES: 0; AC-005-1 输出 state=locked; account-delete EXIT: 2 + `missing --admin-token`; 残留核对 export --limit 100 含 tmp-verify-01.
- ver-b 原件: br001-static-transcript.txt 与 corroboration.md 的命令与输出一致, 与指挥会话自己核到的 sha256 (ba87bd40...ac0b) 相符.
- 指挥会话自己复核的现场事实 (只读, 不运行产品): runtime/data/accounts.json 含 tmp-verify-01 与 n1 首条备注; git diff HEAD 为空; config/shared.json 仍为 `{"export_extra": false}`; git status 只有证据目录未跟踪.
- 材料瑕疵 (不影响结论): ver-a/commands.log 第 2 节的 grep 因输入输出同文件失败, 已在第 2b 节重取并通过命令清单核对命令未带 --config.

## 覆盖范围

- 覆盖 PRODUCT.md v1 (confirmed-flow: v1) 全部 6 个场景与 1 条审计 BR-001, 绑定提交 bc435db.
- 无旧观察可引用 (仓库此前无 runtime/, 无上一轮证据目录), 除 ver-acc2 的独立静态复核外全部为本轮新观察.
- 项目无自动化验证配方 (无构建脚本, 无测试目录, 无 CI), 按 README 记录的命令行入口操作; 没有 TECHNICAL.md / EXECUTION.md, 不影响判据执行, 也不在本轮生成配方.
- 测试实例在验收前不存在, 由验收者按 README 的 init 入口创建; 该创建只写 runtime/data (gitignore 覆盖).

## 结论与后续

- 本轮通过 2 项 (AC-001-1, AC-003-1), 失败 1 项 (AC-004-1 锁定账号 note-list 返回空), 未验证 4 项 (AC-002-1 缺共享配置写入授权, AC-005-1 缺 retention_period 与写入授权, AC-006-1 缺凭据与审计服务, BR-001 true 分支同理).
- 另有清理缺口: 无管理员令牌, tmp-verify-01 仍留在测试实例 runtime/data 中.
- 除本次证据目录的输出外, 源码与 Spec 未变; 证据目录本身是相对起始提交的新增未跟踪文件, runtime/ 是授权创建的测试实例 (被 .gitignore 忽略).
- 本报告不是正式人工验收, 不宣布交付: 结论仍需用户逐项确认, 失败与未验证项需按既有决策流程处理.
