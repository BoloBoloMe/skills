# REVIEW-milestone-01: commit f20a58e 编号汉化独立评审

- 评审者: 独立会话 (未参与实现), 任务标识 review-m01-0323.
- 对象: f20a58e (父提交 182ff18), 全量 diff 已通读.
- 要求来源: ROADMAP.json milestones.milestone-01 (python json 读取核对), renumbering-scope.md.

## 总评: 通过 (2 项轻微发现, 均不阻塞 milestone-04)

## 必跑命令实测输出

```
uv run --with gherkin-official pytest workflow/to-spec/tests -q
  -> 42 passed, 37 subtests passed in 2.96s
uv run pytest --noconftest tests/test_skills_codex_metadata.py -q
  -> 1 passed
uv run python general/writing-for-llm/check_skill.py workflow/decision-ledger/SKILL.md
  -> workflow/decision-ledger/SKILL.md: OK
uv run python general/writing-for-llm/check_skill.py workflow/to-execution/SKILL.md
  -> workflow/to-execution/SKILL.md: OK
```

## 方向 1: 漏改/多改 — 结论: 通过

全量搜旧编号 (`D0NN`/`F0NN`/`(G|NG|BR|AC)-NNN`/`TC-NNN`/`TC-<issue>-<seq>`/`NNN`/`F-ID`), workflow/ 与 general/ 逐个判定:

- 改动清单内 7 个文件 (decision-ledger/SKILL.md, to-spec 的 TEMPLATES/GHERKIN/check-ac/ac-draft/两测试, to-execution 两个文件) 全部落改, 与 renumbering-scope.md 逐位置清单一致, 无漏项. to-spec/SKILL.md 本就无编号规则, 不需改 (grep 零命中).
- 残留的拉丁编号逐类核实均为三类合法形态:
  - 标签写法说明: GHERKIN.md:53/61/62/65/115, TEMPLATES.md:30, check-ac.py:14-17/205/304/314 的 `@AC-NNN`/`@G-NNN`/`@BR-NNN` 全是对标签封闭集/对账规则的描述, 标签按裁决保留拉丁.
  - 历史引用: check-ac.py docstring 的 D003/D005/D007/D008/D011/D012, navigate/codebase-map/use-sandbox-worktree/mailbox/present/access-web 各脚本与测试注释里的 D0xx/F0xx/TC-xxxx/AC-xxx (全部指向各自已关闭变更的账本/issue), 均按不改名单保留.
  - 无关同形串: general/teach/LEARNING-RECORD-FORMAT.md 的 `LR-NNNN`, ADR-FORMAT.md 的 `ADR-NNNN` 不在折算规则表内, 属范围外编号体系, 不是漏改.
- 未发现任何残留的规则性文字在指示未来写 D001/TC-001 等旧编号.

依据: `rg -n -e '\bD0[0-9]{2}\b' -e '\bF0[0-9]{2}\b' -e '\b(G|NG|BR|AC)-[0-9]{3}\b' -e 'TC-[0-9]' -e 'NNN|F-ID' workflow/ general/` 全量输出逐条过目.
影响: 对 milestone-04 无影响.

## 方向 2: 脚本对账逻辑 — 结论: 通过 (1 项轻微发现)

check-ac.py:

- `ENTRY_RE = ^\s*[-*]\s*(目标|规则)(\d+)\s*[:：]` (check-ac.py:60) 正确认新写法; 旧写法 `- G-001:` 不再被识别, 引用时报 "在 `## 目标` 节不存在", 实测 exit=1, 无旧写法兼容 (符合破坏性变更裁决).
- `tag_entry_key` (check-ac.py:104) 归一化正确: `@G-001`/`@BR-012` -> `目标1`/`规则12` (int 吞前导零), 与正文键 `f"{类别}{int(数字)}"` (extract_entry_texts) 完全同构.
- 重复编号: 正文 `- 目标1:` 与 `- 目标01:` 同节 -> 归一化后同键, 实测报 ``[输入] `目标` 节的 目标1 重复`` exit=2. 跨节错配: `- 规则1:` 误写进 `## 目标` 节不会被判 "放错节", 但 @BR 引用照常失败 (实测 exit=1); 此行为与改前 (旧 `G|BR` 两类通吃) 一致, 非本轮回归.
- 报错文案指向新写法: "对账来源: 该节的 `- 目标N:` 列表项" / "`- 规则N:` 列表项" (check-ac.py:371/381).
- 标签位数由 `COVER_TAG_RE \d{3}` 封死, `@G-0001` 走非法标签拒绝, tag_entry_key 不会收到越界输入.

ac-draft.py: entries 键改 `目标`/`规则`, 引用取用 `entries[kind][checker.tag_entry_key(tag)]` (ac-draft.py:167-169), 与 check-ac 同一函数, 路径一致. 实测: `ac-draft.py preview <最小样例> <草稿>` 生成 HTML 中 `reference-text` 输出 `- 目标1: 读者能看到已确认的内容.` 与 `- 规则1: 内容以当前版本为准.`, 标签到正文条目映射正确.

自造样例实测矩阵 (均为临时文件实跑 check-ac.py):

| 样例 | 结果 |
| --- | --- |
| `- 目标1:` + `@G-001` + `@BR-001` | 通过, exit=0 |
| `- 目标1:` + `@G-002` | `[编号对账] @G-002 在 ## 目标 节不存在 (对账来源: - 目标N:)`, exit=1 |
| 正文旧写法 `- G-001:` + `@G-001` | 编号对账失败, exit=1 (无兼容) |
| `@BR-002` 指向 (审计) 条目 | `[编号对账] 指向 (审计) 条目...`, exit=1 |
| 正文 `- 目标01:` + `@G-001` | 通过, exit=0 (见发现 F1) |
| 正文 `- 目标1:` + `- 目标01:` | 归一化后判重复, exit=2 |

影响: 对 milestone-04 无阻塞; F1 若要在机检层强制, 属 milestone-04 规格可顺手覆盖的增量.

## 方向 3: 文档与脚本一致性 — 结论: 通过

- TEMPLATES.md 的 PRODUCT 模板条目写法 (`- 目标1:`/`- 非目标1:`/`- 规则1..3`) 与 ENTRY_RE 逐字匹配; 我按模板样式造的最小样例机检通过, 即模板写法能过机检. GHERKIN.md 的 gherkin 示例块经测试 test_documented_example_is_valid_and_expands_to_three_cards 实测有效 (3 卡), 该测试在本次 42 passed 内.
- GHERKIN.md:67 新增映射说明写全了三要素: 正文写法 (汉字+无前导零), 与标签只差前导零 (`@G-001` 对 `目标1`, `@BR-002` 对 `规则2`), 机检去前导零按数字对账, 且明确标签保持拉丁三位. 下游照此足以落笔并被机检接受.
- to-execution 用例编号自洽: SKILL.md:75 主用例与验收同号 (`验收5 -> 用例5`), 额外用例 `用例<issue 编号>-<序号>` 且明确 "issue 编号与序号都不带前导零, 如 ISSUE-02 的第一条额外用例为 用例2-1"; TEMPLATES.md 覆盖矩阵 `验收1 -> ISSUE-01 -> 验证入口 (采用测试时加 用例1)` 与之一致. ISSUE-01 文件名两位前缀与用例无前导零的不对称是裁决明文 (ISSUE-01 保留, 用例2-1), 有说明, 不算矛盾.
- 报错文案/文档/模板三处对账来源写法一致 (都是 `- 目标N:`/`- 规则N:`).

影响: 无.

## 方向 4: 测试忠实性 — 结论: 通过

- 两个测试文件改后样例正文全部是新写法 (目标1/非目标1/规则1/规则2/决策1), 断言原文串也改成 `- 目标1:`/`- 规则1:` (test_ac_reading.py:113-114/212), 即测试断言的是新写法产出, 不是旧写法.
- 不存在 "脚本同时接受旧写法导致假通过" 的路径: 实测旧正文写法被机检拒绝 (方向 2 矩阵), 测试样例若残留旧写法会直接红. grep 确认 tests 内 `G-001`/`BR-001`/`AC-001` 仅以标签形态 (`@G-001` 等) 出现, 全部按裁决保留.
- 测试与文档样例一致: test_ac_reading.py:301-308 直接读 GHERKIN.md 的 gherkin 块并以 BASE (新写法) 校验展开, 文档示例与测试样例走同一机检路径; 若 GHERKIN.md 示例与 ENTRY_RE 不符, 该测试会失败.
- 负路径保留: @G-999/@BR-999 (不存在), @BR-002 (审计), 多 AC, 无覆盖, 重复规则编号等用例均仍在新写法下成立.

影响: 无. milestone-07 实施新流程时可在现测试基线上扩展, 不需要重写.

## 发现清单

- F1 (轻微, 不阻塞): 机检不拒绝正文条目带前导零. ENTRY_RE 数字组是 `\d+`, 归一化把 `- 目标01:` 当 `目标1` 放行 (实测通过). 折算规则明文 "正文不带前导零", 但该约束只有文档约束没有机检约束. 影响: milestone-04/07 的产物若手滑写 `- 目标01:` 不会被机检拦. 建议: 可在 milestone-04 规格 "机检改动边界" 里补一句 (正文数字组限 `[^0]\d*`), 或接受文档约束即可.
- F2 (记录, 非缺陷): 正文条目写错节 (如 `- 规则1:` 写进 `## 目标` 节) 不被单独点名, 只在引用对账时间接失败; 与改前行为一致, 属既有语义, 不要求本轮修.

除上述外无问题清单; 无漏改, 无多改, 无旧写法兼容残留.
