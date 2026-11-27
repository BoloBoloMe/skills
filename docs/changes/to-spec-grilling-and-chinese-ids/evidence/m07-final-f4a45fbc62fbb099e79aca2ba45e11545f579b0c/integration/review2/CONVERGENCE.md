# milestone-07 返工收敛核对报告 (review2)

- 任务标识: m07-rev-conv; 回信地址: 01a21b35-1a38-779a-b0e7-7a28184df3ec.
- 角色: 返工收敛核对审核者, 独立上下文, 未参与任何返工实现. 只读: 未改仓库任何文件, 未提交, 未推送. 本报告写在仓库外证据根.
- 现场: 仓库 /home/bolo/Workspace/improve, HEAD = a13085ab9e10eacbc726b90e0d8ccfb731447c0d (git rev-parse 实取, 与派工口径一致).
- 返工轮差异: `git diff 783a528..a13085a` 共 11 文件 (workflow/ 4 文件 57+/6-, docs/changes/.../ 7 文件). 返工提交链: dd40f98 (ISSUE-05), bbc038d (ISSUE-04), 42456c4/e6b7962 (工单回填), 676311a (ISSUE-06), 68a5f09/ca9f7c3/c055e5e (三次 --no-ff 合并), a13085a (返工集成记录 4 行).
- 原始发现: /home/bolo/evidence/to-spec-grilling-and-chinese-ids/integration/review1/{STANDARDS.md (H1-H5, J1-J9), SPEC.md (F1-F8, Q1-Q4)}; docs/changes/to-spec-grilling-and-chinese-ids/IMPACT-REVIEW.md (R1-R10).
- 返工证据: /home/bolo/evidence/to-spec-grilling-and-chinese-ids/{issue-04,issue-05,issue-06}/run1/, integration/run2/.

## 0. 结论摘要

逐项结论一行汇总:

| 项 | 结论 |
| --- | --- |
| H1 五步完成标准 | 已收敛 |
| H2/H3 标点半角 | 已收敛 (0 残留, U+2192 无新增) |
| H4 check-ac v1 文案与行为 | 已收敛 |
| R4-自动化 | 已收敛 (HEAD 复跑 40 passed + 50 subtests, exit 0) |
| Q4 verify-change 术语 | 已收敛 (语义零变化) |
| F 工单回填/勾选/EXECUTION 摘要 | 已收敛 (所引归档证据真实存在且支撑) |
| 附加: 范围外混入 | 有偏差 (2 处轻微, 均为记录层, 无产品影响, 详见第 8 节) |

总体: 全部核对项实质已收敛, 无未收敛项; 偏差仅 2 处轻微记录层事项, 不阻塞交付, 是否处理由用户决定.

## 1. H1 to-spec 五步完成标准 — 已收敛

- 原发现 (STANDARDS.md H1): "workflow/to-spec/SKILL.md 五个编号步骤全部丢失'完成标准'... 这五段是约束或理由, 不是'何时算做完'的可判定条件... 建议按 verify-change 的写法为 5 步各补一句可检查的完成标准."
- 现场: `workflow/to-spec/SKILL.md` HEAD 行 25/37/55/71/96 各有一句 `完成标准:` 段, 与派工核对行号 (约 25/37/55/71/96) 一致. 逐句与该步骤现行要求对照:
  - :25 (§1 盘问): 已问/未碰状态与理由呈现, 盲区扫描, 待裁决项关闭, chat 明确结束, 入账; 未满足停盘问不写稿 — 对应该步"闭环"与"入账"两条目的全部要求, 可判定.
  - :37 (§2 反方与落笔): 反方发现逐项核实收敛, 三份临时原件按位置与内容约束就位; 未决或缺依据停下补问, 不进机检 — 对应该步反方核实与三份原件放置要求.
  - :55 (§3 机检与机械落正式): 闭环确认核实到本次范围, 转正退出 0 且 success true, cmp 与两份正式稿机检退出 0; 失败按整组未完成保留现场 — 对应该步命令清单与失败处理段.
  - :71 (§4 写后检查): 三项检查有结论, 发现分流为驳回/修文/补问, 整份规格覆盖; 未关闭不进预览 — 对应该步三项检查与分流要求.
  - :96 (§5 预览交付): 预览 success true 且只挂本次 review 目录, 路径与结论已汇报; 失败只交文件不声称交付 — 对应该步汇报与交付条件.
- 写法: 符合 general/writing-for-llm/SKILL.md "步骤 与 完成标准" 节约定 (每步以一句可判定带要求量的完成标准结尾, 边界写清 done/not-done); 均含正向条件与"未满足时停"的反向边界. `uv run python general/writing-for-llm/check_skill.py workflow/to-spec/SKILL.md` 实跑 OK, exit 0.
- 工单声明与证据一致 (ISSUE-04 验收标准第 1 项勾选, 引 issue-04/run1/INDEX.md 第 2 节, 该表逐行给出提炼依据).

## 2. H2/H3 标点半角 — 已收敛

- 原发现: H2 = ISSUE-02:64 一行 3 处 U+3001; H3 = ISSUE-01:62-64 三处 U+2014; 附注 U+2192 箭头属允许用法.
- 现场: `grep -c` U+3001 于 ISSUE-02 工单 = 0, U+2014 于 ISSUE-01 工单 = 0. 对返工全差异 (workflow/ + docs/changes/) 全部新增行按 Unicode 类扫描 (U+2014, U+3000-303F, FF00-FFEF, 弯引号): 0 命中. U+2192 在差异新增行 0 处 (无新增, 既有用法保持). STANDARDS 引用的行均以实测为准, 现场 0 残留.
- ISSUE-06 工单 (e) 声明与证据一致 (`issue-06/run1/logs/punct-{before,after}.*` 在场, punct-after TOTAL 0).

## 3. H4 check-ac.py v1 文案统一且行为未变 — 已收敛

- 原发现 (STANDARDS.md H4): "文档说'固定 v1', 代码文案与实现按 vN ... :175 报错文案仍写 vN ... 建议统一成 v1 常量, 若真要容忍历史 vN, 写明'机检接受 vN, 现行写 v1'".
- 现场 HEAD `workflow/to-spec/check-ac.py`:
  - docstring 校验项 0 改为 "必须在 Gherkin 块前含固定标记 `<!-- confirmed-flow: v1 -->` ... 机检按 `v数字` 匹配以兼容旧文件, 现行只写 v1" — 即采纳了原发现的建议写法, 两层口径合一.
  - 两处报错 (缺标记 :172, 标记位置 :177) 均用 `CONFIRMATION_MARKER` 常量 (= v1 原文, :43), 不再出现 vN 字样.
  - `MARKER_RE` (:45, `v\d+`) 与基线 783a528 逐字符相同, 未在差异中触碰; 接受范围行为未变.
- 行为不变证据: issue-04/run1/logs/marker-*, 基线/目标同输入退出码逐例一致 (缺标记 2/2, 标记在围栏后 2/2, v1 0/0, v2 0/0 — 兼容 vN 的接受行为两侧相同, 与工单"只统一文案不改行为"声明一致). 我未重跑 probe04, 以其原始 .cmd/.exit 原件为据.

## 4. R4-自动化坏输入回归 — 已收敛

- 原发现 (IMPACT-REVIEW.md R4): 三条转正过程保护只留一次性证据, 无仓库自动化回归; 检查方法建议"把 trace 场景落成仓库内真实进程用例".
- 现场 HEAD `workflow/to-spec/tests/test_ac_draft.py` 新增 `test_promote_rejects_bad_format_and_bad_numbering_inputs_keeping_output` (11 个 subTest): 走 `self.promote()` 即 `subprocess.run` 真实 `ac-draft.py promote` 进程 (helper :100-121, 文件级 grep mock/patch 0 命中), 输入为临时目录内真实隔离文件; 每例断言 期望退出码 (1/2), JSON success false, 报错命中规则名, 已转正正式稿字节不变, 输出目录无临时文件残留. 覆盖坏关键字/同义关键字/缺功能行/功能级标签/草稿带标记/围栏外正文/未知目标/未知规则/审计规则/场景双AC/重复目标.
- 与用例22 意图一致性: EXECUTION.md 验证策略 "用例19至用例24分别保护公开预览,转正,参数移除,失败/并发输入,编号对账和 AC-024 的七种违规输入" — 用例22 为失败/并发输入; 本测试承担其中"失败输入"自动化部分, 并发窗口按工单明确保持 issue-01 run5 一次性真实进程证据不强行自动化, 分工与声明一致. 覆盖对象为公开 CLI 与可观察输出, 不绑定内部函数, 符合验证策略"只通过公开 CLI/真实隔离文件"要求.
- HEAD 复跑 (本审核者实跑, 2026-11-27): `uv run --with gherkin-official pytest -p no:cacheprovider -q workflow/to-spec/tests` → `40 passed, 50 subtests passed in 4.13s`, exit 0; 与 issue-04 `logs/final-pytest.*` 及 `logs/post-commit-pytest.*` (40 passed + 50 subtests, exit 0) 一致, 基线 39+39 不回退属实. 另实跑 `uv run --with gherkin-official pytest workflow/to-spec/tests` (integration/run2 同命令) → 40 passed, exit 0, 与 run2/pytest.stdout 一致.

## 5. Q4 verify-change 术语统一 — 已收敛

- 原发现 (SPEC.md Q4): verify-change SKILL.md :45,51,79 用 "设计方式" 而文件内小节名是 "设计验证方案", 建议统一.
- 现场 HEAD: `grep -c 设计方式 workflow/verify-change/SKILL.md` = 0; :45, :51, :79 三行均改为 "设计验证方案", 与 :11 调用方式名和 :18 标题一致. 差异逐行核对: 三行新内容与旧行仅做该词替换, 其余逐字节一致, 无任何语义变化. check_skill.py 实跑 OK exit 0.
- 注: 同类用法仍在 `workflow/navigate/SKILL.md:71`, `workflow/verification-contract/SKILL.md:15`, `README.md:65`, 属 ISSUE-05 明示的范围外未改未擅扩; SPEC 原发现只针对 verify-change 三处且判为可读性观察, 不构成偏差.

## 6. 工单回填/勾选/EXECUTION 摘要 — 已收敛

原发现对应关系: 本项覆盖 SPEC.md 的记录类发现 F4 (ISSUE-02 未回填非作者报告), F5 (ISSUE-03 未勾选), F6 (实施前摘要缺时点记录), F7 (ISSUE-01 引用 run4 与 run5 依据不一致). 返工工单/EXECUTION 将其统称 "F2/F3/F5/F6" (编号与 SPEC 原报告不一致, 见第 8 节偏差 2), 实际内容一一对应上述四条.

逐条核对 (抽查到文件级):

- ISSUE-01 (F7): 工单交付证据补写 run4/run5 对应关系 (252 个同名日志, 181 个逐字节一致, 71 个仅差路径/时间戳/预览文件名, 结论性输出逐字节一致), 引原件 `issue-06/run1/logs/run4-run5-compare.{cmd,stdout,exit}`. 实测该 stdout 含 `shared_names=252`, `identical_shared=181`, `differing_shared=71`, 数字与工单一致. 原件在场.
- ISSUE-02 (F4): 交付证据补 check1 结论 (21 场景 43 条预期, 无已证实缺陷, 4 疑点), 指向归档树 `evidence/m07-1bc15f6.../issue-02/check1/`; 5 项验收标准全部勾选并注明引用节号. 归档实测: `CHECKS-ISSUE-02.md`, `INDEX.md`, `finished-at.txt`, `originals/`, check_skill 原件等 15 项在场. 绑定声明的 sha256 前缀 86676e53 (SKILL.md) 与 d901c5aa (REVERIFY.md) 经 `git show b260081:... | sha256sum` 独立复核逐位一致; 核对时点 04:38:52Z 早于集成提交 1bc15f6 (04:57:27Z) 与 SPEC.md 记录一致. 4 疑点逐项处理声明与回填段一致.
- ISSUE-03 (F5): 交付证据补 run1 核对回填, 5 项验收标准全部勾选并注明引用. 归档实测: `evidence/m07-1bc15f6.../issue-03/run1/{INDEX,local-check.md,candidate.patch,check_skill.log,check_skill.exit,scope.log,environment.txt}` 7 项齐备, 与引用一致. 绑定原件 `issue-06/run1/logs/issue03-run1-binding.*` 在场.
- EXECUTION 摘要 (F6): 补记行声明取得时间 2026-11-27 04:15:45 UTC, 命令, 231 文件, 且如实写明"该时点无单独时间戳文件, 以 mtime 与首条产品提交先后作旁证, 该时段未独立观察" — 与 SPEC F6 建议的两种修法之一 (如实列缺口) 一致. 实测: 仓库外 `pre-impl-snapshot/skills-manifest.sha256` 与归档副本均 231 行, 在场; 该行由 ISSUE-06 提交 676311a 加入 (EXECUTION 全差异 5 行中 1 行属 676311a, 另 4 行属集成提交 a13085a).
- 引用路径存在性: ISSUE-06 验证契约要求全部引用路径逐一核对, 其 `logs/refs-after.stdout` 抽查 (ISSUE-01 段 20+ 行 OK) 与我抽核的归档目录一致.

## 7. HEAD 复跑结果 (本审核者实跑)

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| to-spec 测试 | `uv run --with gherkin-official pytest -p no:cacheprovider -q workflow/to-spec/tests` | 40 passed, 50 subtests passed, exit 0 |
| to-spec 测试 (run2 同命令) | `uv run --with gherkin-official pytest workflow/to-spec/tests` | 40 passed, exit 0 |
| check_skill to-spec | `uv run python general/writing-for-llm/check_skill.py workflow/to-spec/SKILL.md` | OK, exit 0 |
| check_skill verify-change | 同上, verify-change/SKILL.md | OK, exit 0 |

## 8. 附加: 返工差异逐 hunk 对照工单声明范围 — 有偏差 (2 处轻微)

差异文件全表与归属: workflow/to-spec/SKILL.md + check-ac.py + tests/test_ac_draft.py (ISSUE-04 允许范围), workflow/verify-change/SKILL.md (ISSUE-05 允许范围), ISSUE-01/02/03 工单 + EXECUTION.md 1 行 + ISSUE-06 工单 (ISSUE-06 允许范围), ISSUE-04/05 工单 (各自工单文件), EXECUTION.md 4 行 (集成提交 a13085a, 集成会话自身记录职责). 无产品文件越范围改动, 无原发现之外的 workflow/ 产品条文混入. 两处轻微偏差均在 ISSUE-01 工单文档内:

1. ISSUE-06 允许范围 (a) 字面只声明 "text-mapping 引用 run4/run5 更正", 但 ISSUE-01 差异另含两处顺带更正: (i) 合成文件清单 "四个 `missing-N.md`... 七个 `typo-N.md`" 改写为 "`missing-1.md` 至 `missing-4.md`... `typo-1.md` 至 `typo-7.md`"; (ii) 技术稿核对行 `target-tech-{copy,compare,formal}` 加 `run5/logs/` 路径前缀. 两处同属"引用以实际为准"性质的记录更正, 不触碰产品, 不改变结论, 但超出工单声明字面范围, 且 ISSUE-06 执行结果节未逐条列出. 判轻微偏差, 建议知悉即可.
2. 发现编号口径不一致: 返工工单/EXECUTION 把本节四条记录类发现标为 "F2/F3/F5/F6", 而它们在 SPEC.md 原报告中的编号是 F4/F5/F6/F7; SPEC 的 F2 (AC-036 禁令承接) 与 F3 (复验会话放宽登记) 实际经 ISSUE-02 回填的疑点 Q1/Q3 处理 (Q1 登记可接受, Q3 登记为观察交父级裁决), 但 EXECUTION 的 "未处理发现与归属" 行只显式列 F1/R1/R2/R4, Q1/Q3 的裁决归属在 EXECUTION 无显式结论行 ("等用户授权范围后处理"的"等"是否覆盖 F2/F3 需读者推断). 判记录层偏差, 不阻塞; 建议后续在 EXECUTION 或裁决记录里把 Q1/Q3 结论显式落行.

未列入偏差的观察: EXECUTION 返工轮检查行写 "40 passed, exit 0" 未带 subtests 计数, 与 integration/run2/pytest.stdout 原件一致 (该命令形态不显示 subtests), 非记录失实.

## 9. 汇总

- 已收敛: H1, H2, H3, H4, R4-自动化, Q4, 工单回填/勾选/EXECUTION 摘要 (F4-F7 内容). 无未收敛项.
- 有偏差: 第 8 节 2 处轻微记录层偏差 (ISSUE-01 两处顺带更正超出工单字面范围; 发现编号 F2/F3/F5/F6 与 SPEC 原编号 F4-F7 不一致且 Q1/Q3 裁决在 EXECUTION 无显式落行), 均不影响产品行为与证据真实性.
- 本报告不构成验收, 不代替 milestone-08 独立验证与用户终点验收.
