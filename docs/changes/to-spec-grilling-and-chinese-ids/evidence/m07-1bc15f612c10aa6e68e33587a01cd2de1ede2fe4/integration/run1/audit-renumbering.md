# 编号/历史范围审计 (规则12) — milestone-07 全切片集成检查

- 任务标识: m07-int-1; 执行者: 本里程碑集成检查会话 (未参与三切片条文编写, 只读审计, 不修任何文件).
- 范围: `182ff1846d0ed310b7f4ed308366d36f6e74b412..(HEAD=milestone-07 集成提交)` 的完整旅程差异, 审查对象 `workflow/` 与 `general/` 全部现行编号规则与旧编号命中.
- 检查时刻 HEAD: 见 `head-commit.txt`; 集成合并提交 `9eedb3a`(issue/01), `f9bfe71`(issue/02), `1dfc38a`(issue/03), 记录提交 A `1bc15f6`.
- 规则来源: `PRODUCT.md` 规则12 (第40行) + `renumbering-scope.md` 折算规则/不改清单 + `REVIEW-milestone-01.md`.
- 方法: 不重做 milestone-01 汉化; 只核实现行规则未被回退, 旧编号命中逐条分类, 新增行零违规.

## 1. 结论

**无新违规. 不需要任何改造.** 旧编号命中全部落在既有例外类别内 (标签说明 / 历史引用 / ISSUE 文件名 / milestone id / 无关同形串). milestone-01 的 9 文件汉化保持有效, 本轮未回退.

## 2. 完整改动清单 (基线到 HEAD)

`audit-full-changed-files.txt`: 41 个文件. 结构:
- 本变更文档: `docs/changes/to-spec-grilling-and-chinese-ids/` 下 26 个文件.
- 产品条文/脚本/测试: `workflow/` 下 14 个 (含 milestone-01 的 9 个), 根 `README.md` 1 个.
- **其他变更的历史目录命中数: 0** (`git diff ... --name-only | grep '^docs/changes/'` 过滤本变更路径后为空), 即未改历史产物, 未重写历史引用.

`workflow/` 新增行中命中旧编号形态的只有 1 行: `workflow/to-spec/GHERKIN.md` 的 ``@AC-NNN`` 标签说明, 属标签封闭集描述, 归 "Gherkin 标签例外". 明细见 `audit-added-lines-old-ids.txt`.

## 3. 逐项分类 (全量命中 755 行)

原始命中: `audit-rg-hits.txt` (rg 模式与退出码见 `audit-rg-exit.txt`). 多类可同现, 分类按语义归主.

| 类别 | 数量(粗略) | 判定依据 | 结论 |
| --- | --- | --- | --- |
| 已汉化 (milestone-01 9 文件) | 9 文件 | 见第 4 节逐文件 | 保留, 不回退 |
| Gherkin 标签例外 | 24 行含 `@G-/@NG-/@BR-/@AC-NNN`, 134 行含无 `@` 的 `AC-###`/`BR-###`/`NG-###`; 另有 16 行 `NNN` 占位说明 | 规则12 明文 "标签仍用 @AC-001/@G-001/@BR-001 等既有拉丁三位"; 无 `@` 形态出现在脚本断言/标签值/文档标签表中, 同属标签面 | 例外, 不改 |
| ISSUE 文件名例外 | `issues/ISSUE-01..03-*.md`, `ISSUE-02` 字样 | 折算规则明文 "ISSUE-<两位> 文件名前缀不改"; `to-execution/SKILL.md:75` 用例编号规则明文 `用例2-1` 与 `ISSUE-02` 不对称且已说明 | 例外, 不改 |
| milestone 与历史引用例外 | `D0xx` 427 行, `F0xx` 16 行, `TC-` 153 行, `F-ID` 4 行 | 全部指向各自已关闭变更的账本/issue/评审 (如 `swt.py` 的 D003/D004/D005/D010/D013, `mailbox.py` 的 D003/D006/D010/D014/D022, `web_server.py` 的 D005/D007/D020, `test_roadmap_validation.py:4` 的 TC-005 说明). `REVIEW-milestone-01.md` 与 `renumbering-scope.md` 明列此类不改 | 例外, 不改 |
| 无关同形串 / 非编号体系 | 若干 (`TF-IDF`, `LR-NNNN`, `ADR-NNNN`, 三位数字阈值等) | 不在折算规则表内, 非本仓库正文编号体系 | 例外, 不改 |
| **新违规** | **0** | 见第 5 节判别方法 | **无** |

旧正文条目形态专项 (`audit-old-entry-forms.txt`, 模式: 列表项/标题/表格首列 `G|NG|BR|D|F` + 数字): 35 行, **全部是源码注释中的历史引用** (例: `image-prep.py:303 # F012: ...`, `swt.py:77 # D005: ...`), 无一条是把旧编号写成正文条目或指示未来使用旧编号.

规则性指示专项 (`audit-rule-like-lines.txt`, "编号/命名/ID" 与拉丁编号同现): 18 行, 逐条看完, 全是标签对账规则说明 (`GHERKIN.md:65/115`, `check-ac.py:25`) 或历史引用, 无 "从 D001 起编号" 一类旧规则文字.

## 4. 对照 milestone-01 的 9 文件清单

`REVIEW-milestone-01.md` 认定的 9 文件与本轮状态 (`audit-m01-nine-files.txt`: 中文编号行数 / 旧 `D0xx|F0xx` 行数):

| 文件 | 中文编号行 | 旧 D/F 行 | 判定 |
| --- | --- | --- | --- |
| workflow/decision-ledger/SKILL.md | 3 | 0 | 汉化保留 (`决策1`/`事实1` 起), 无旧写法 |
| workflow/to-execution/SKILL.md | 1 | 0 | 汉化保留 (`验收5 -> 用例5`, `用例2-1`), 无旧 `TC-` 规则文字 |
| workflow/to-execution/TEMPLATES.md | 7 | 0 | 汉化保留 |
| workflow/to-spec/TEMPLATES.md | 10 | 0 | 汉化保留 (`- 目标1:`/`- 规则1:`), 唯一 `@BR-NNN` 命中为标签说明 |
| workflow/to-spec/GHERKIN.md | 1 | 0 | 汉化保留 (第67行补的标签↔正文对账说明仍在), 标签表不动 |
| workflow/to-spec/check-ac.py | 3 | 7 | 汉化保留 (`ENTRY_RE` 认 `- 目标N:`/`- 规则N:`, `tag_entry_key` 归一化); 7 行 D0xx 为 docstring 历史引用, REVIEW-milestone-01 明列不改 |
| workflow/to-spec/ac-draft.py | 0 | 0 | 汉化保留 (键为 `目标`/`规则`, 无编号字面, 与 REVIEW 描述一致) |
| workflow/to-spec/tests/test_ac_draft.py | 5 | 0 | 汉化保留 (样例正文新写法, 断言 `- 目标1:`) |
| workflow/to-spec/tests/test_ac_reading.py | 12 | 0 | 汉化保留 (同上) |

本轮三切片对这些文件的改动 (issue/01 触及 to-spec 5 个文件, issue/02 触及 verify-change 2 个, issue/03 触及 navigate 2 个 + README): 未引入旧正文编号, 未移除中文编号规则. 佐证: 第 5 节 grep 全空 + 本轮 `pytest workflow/to-spec/tests` 39 passed (编号对账用例含在内).

## 5. 无新违规的判别方法 (可复现)

1. 全量搜旧编号: `rg -n -e '\bD0[0-9]{2}\b' -e '\bF0[0-9]{2}\b' -e '\b(G|NG|BR|AC)-[0-9]{3}\b' -e 'TC-[0-9]' -e '\bNNN\b' -e 'F-ID' workflow/ general/` -> 755 行, 全表落盘 (`audit-rg-hits.txt`), 逐类归入第 3 节类别.
2. 只差集看新增行: `git diff <基线>..HEAD --unified=0 -- workflow/ general/` -> 798 行补丁 (`audit-diff-workflow-general.patch`), 新增行命中旧编号 1 处, 为 `@AC-NNN` 标签说明.
3. 只看 "旧编号被当正文条目用" 的可能: 第 3 节末两个专项 grep 均为历史引用或标签说明.
4. 只看 "规则文字被改写回旧写法": 规则性指示专项 18 行逐条过目, 无旧规则文字.

## 6. 局限与未覆盖

- 判定 "历史引用 vs 新违规" 采用语义抽查 (全部旧正文条目形态 35 行 + 规则性指示 18 行逐条过目; 其余 700 余行为标签/占位/无关同形, 按模式归类). 未逐行读完 755 行每一处上下文.
- 本审计只覆盖 `workflow/` 与 `general/`; `docs/` 下历史引用的完整性属 milestone-13 更新差异时的范围.
- 本审计不评价条文语义正确性 (那属评审与 milestone-08 独立验证), 只作编号与历史范围核对.