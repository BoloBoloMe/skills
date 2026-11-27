# m07-chk-02 / ISSUE-02 非作者核对证据索引

- 任务标识: m07-chk-02; 回信地址: 01a21b35-1a38-779a-b0e7-7a28184df3ec
- 检查者: 非作者独立检查会话, pi session `01a21b49-1a7d-731e-97db-8d6ff3fac9f8` (mailbox session 同 id, 取信守护 running=true), 未参与候选条文编写
- 现场: 工作树 `/home/bolo/Workspace/improve.worktrees/ISSUE-02`, 分支 `issue/02`, 顶端 `34ae05961d5d319b73849a7fd94d7963613eb918`, 工作树干净
- 候选: 提交 `b260081db4461c58644a36189e1fd96f5b2a95c6`, 只改 `workflow/verify-change/SKILL.md` 与 `workflow/verify-change/REVERIFY.md`
- 时间: 开始 `2026-11-27T04:37:51Z` (见 `started-at.txt`), 完成见 `finished-at.txt`
- 性质: 只读作业. 未写仓库, 无 git 写操作, 未提交/推送. `git-status-before.txt` 与 `git-status-after.txt` 均 0 字节, `head-commit.txt` 与 `head-commit-after.txt` 同为 `34ae0596...`

## 1. 结论摘要

- 21 个场景 (验收31-40 全部 normal/failure/edge, 验收41 的 verify-change/REVERIFY 部分) 逐条核对: 43 条 `那么`/`而且` 预期全部有承接, **无已证实缺陷**, 4 条非阻塞疑点 (见 CHECKS 第 9 节).
- 规则16-22, 技术规格验证方案接口/关键流程5/接缝/安全, verification-contract 与 SAFETY 边界, 通用账本与 handoff 续问: 均有承接, 未发现放宽或新增判据.
- 全表 70 产品行 + 3 工程行未被删减; 本切片逐行登记 21 行, 其余行承接属其他切片/里程碑, 未在本报告判通过.
- 格式检查: `workflow/verify-change/SKILL.md: OK`, stderr 空, 退出码 0 (只作格式证据).
- 总体: **无阻塞**; 未验证项与局限见 CHECKS 第 10 节.

## 2. 输出文件

| 文件 | 作用 |
| --- | --- |
| `CHECKS-ISSUE-02.md` | 核对报告: 21 场景逐项结论, 规则/技术/契约承接, 全表追溯, 缺陷与疑点, 格式检查, 总体结论 |
| `originals/SKILL.md`, `originals/REVERIFY.md` | 被查候选条文快照 (只读副本, 绑定 `originals/candidate.sha256`) |
| `originals/candidate.sha256` | 两份候选条文的 sha256 |
| `inputs.sha256` | 全部权威输入与边界文件的 sha256 (PRODUCT/TECHNICAL/VERIFICATION-PLAN/DECISIONS/工单, verify-change reference, verification-contract 三件, decision-ledger, handoff, grilling, opposing-viewpoint, llm-select, use-herdr, README, navigate 两件) |
| `check_skill.command.txt`, `check_skill.stdout`, `check_skill.stderr`, `check_skill.exit-code.txt` | 格式检查命令, 完整输出, 退出码 |
| `git-diff-check.txt` | `git diff --check` 输出与退出码 (0, 空) |
| `git-log.txt`, `head-commit.txt`, `head-commit-after.txt` | 核对时顶端提交 (前后一致) |
| `git-status-before.txt`, `git-status-after.txt` | 作业前后工作树状态 (均空, 证明只读) |
| `started-at.txt`, `finished-at.txt` | 起止时间 (UTC) |

## 3. 权威输入原件 (路径 + 摘要, 只读引用)

正文引用行号绑定下列摘要; 摘要或行号变化时本报告结论不自动沿用.

| 文件 | sha256 |
| --- | --- |
| `docs/changes/to-spec-grilling-and-chinese-ids/PRODUCT.md` | `c8823e0edf27e86a05f81acf89e5fea6027db3524afd6c88512326cda3e239d5` |
| `.../TECHNICAL.md` | `e825dd5799fb6fa725216e140a3a1bb240b868753bf6c850ccfc615f39340f1e` |
| `.../VERIFICATION-PLAN.md` | `7c4c450f1bfdf630f133f20435b9000cd76ab76a06c5538b1fa4f9a15fc49583` |
| `.../DECISIONS.md` | `b4f1ec514cffad1c62874746647b7fdfdac5248fc46f40e990a51c6315b0b0ef` |
| `.../issues/ISSUE-02-verify-change-method-flow.md` | `3075f4ef9520ebaadeb3328274899fe8145fab2550aeedfae44c833f4c13fd79` |
| `workflow/verify-change/reference/SCENARIO-CHECK.md` | `4fc784624547bc8f129b65fe02c31edac3f2eef072c7ef4927256e9f124e87da` |
| `workflow/verify-change/reference/EVIDENCE.md` | `2d051fa47a20be76c50d6a2fa6274a01d3662c780df99d0586ae9857e2849ff4` |
| `workflow/verification-contract/SKILL.md` | `b534590269476ee3552ca722a690b1adace1c5648647033fd0f3d0baf4a1bc56` |
| `workflow/verification-contract/SAFETY.md` | `b6ecdcbf28cdf27341cc3b73f33cd2ad0f6b03669c585081b8014d0ad6ec689b` |
| `workflow/verification-contract/reference/tests.md` | `e9b7cb203f919d849b0dfc46afb9ebb1a312916ef12b2a7a09311b395b672824` |
| `workflow/decision-ledger/SKILL.md` | `dfa3843bd04d7af06acc333a852996f19803ebdae36bffa4886471718efe359c` |
| `general/handoff/SKILL.md` | `bd14dc448793ac89628897da95f2d2a5eabf061a38e2019c084fe8620eaef03a` |
| `general/grilling/SKILL.md` | `a8880188dbbf64ba8736420bfdb762782b359df1672034fabea4b620294bc2b5` |
| `general/opposing-viewpoint/SKILL.md` | `35769de7b7098b35dcbb488615951e93cad9d10b891d6c57881e77d657fc2067` |
| `general/llm-select/SKILL.md` | `0dfa29512bf265c4ee4d60846b57ff506fed71e4d8440e433be88cfe0ae85c89` |
| `general/use-herdr/SKILL.md` | `0a9ea8968019d3a0b5735d637122c786558947cc99bfd1dc1ff1a7df0a607459` |
| `README.md` | `2c007b94dc7515074e96ca8240b898b67379b0b98a02322cfe3cadcad6dc4105` |
| `workflow/navigate/SKILL.md` | `50616b11be8722ef0d89266db5b30fbe8c733f8bfc9f691576e810c8639a375a` |
| `workflow/navigate/reference/VERIFICATION.md` | `e61ed54303d619af2e00f596c11c1bde08d8a5980c0f8b1ad0b6886b7ee6c8cd` |

## 4. 作者的待验证线索 (不作通过证据)

- `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-02/run1/` (首次格式检查) 与 `run2/` (候选交付, 含 `INDEX.md` 定位表, `candidate.diff`, `candidate.sha256`).
- 作者 run2 声明的候选摘要与本报告 `originals/candidate.sha256` 一致; 其定位表只作线索, 每条判断均由本报告按权威原文独立作出. 作者自述"未取得非作者报告"与本报告出具的事实相符.
- 作者 run2 提到的跨切片残留 (README:65, navigate/SKILL.md:56, navigate/reference/VERIFICATION.md:9 旧确认措辞) 经本检查者复核确实存在, 属 ISSUE-03/集成范围, 未在本切片判缺陷.

## 5. 未做的事 (局限)

- 未运行候选 skill, 未运行真实需求, 未运行 to-spec 测试与全量 pytest, 未做成品独立验证.
- 未核对 ISSUE-01/ISSUE-03 条文, 未判其余 49 产品行与 2 工程行的通过.
- 未代用户验收; 未声称跨切片一致; 未判 milestone-12/13 的用户审改与集成完成.