# HANDOFF: ISSUE-20 两份 reference/PROVENANCE.md 差异表更正

## 交付了什么

只动两份来源差异记录, 不碰技能正文, 许可文本, 固定 SHA 与借用范围:

1. `workflow/blast-radius/reference/PROVENANCE.md`
   - 差异表第 1 行: 删掉 "调用方式从模型自动触发改为用户点名"; 改为 "只改描述措辞; 调用方式没有改变", 并写明 `disable-model-invocation: true` 上游第 4 行与本地第 4 行逐字相同, 依据是上游原文第 4 行.
   - 差异表第 2 行: 删掉 "frontmatter 与 H2 结构由 `check_skill.py` 校验通过"; 改为人工检查结论, 并写明 `check_skill.py` 不检查标题.
   - "命令 3" 小节改名 "人工标题结构检查 (只列标题, 判定靠人读)", 正文拆成机检 / 人工两段.
2. `workflow/benchmark-checklist/reference/PROVENANCE.md`
   - 差异表第 1 行: 同上, 不再记为调用模式改变.
   - 差异表第 2 行: 标题层级结论补标为人工核对, 不借用机检结果.
   - "命令 3" 小节同样改名并拆分机检 / 人工.

新增证据: `docs/changes/verification-skills/evidence/ISSUE-20/` 下 6 个文件 (对照脚本, 逐行对照表, 切片记录, 红轮日志, 绿轮日志, 机械检查日志).

## 每个验收标准对应的证据

| 验收标准 | 证据文件 | 要点 |
| --- | --- | --- |
| 两份差异表不再把未变的 frontmatter 记为模式改变, 有原文对照证据 | `TS-001.md` (红轮 / 绿轮节), `red-ts001.log`, `green-ts001.log`, `DIFF-ANCHORS.md` 第 1 行 | 上游两份 `*-SKILL.md` 第 4 行都是 `disable-model-invocation: true`, 本地两份 `SKILL.md` 第 4 行逐字相同; 红轮 2 条失败, 绿轮 0 失败 |
| 机检与人工检查分开表述, 有证据 | `TS-001.md` (H6 依据节), `DIFF-ANCHORS.md` 第 2 行, `machine-checks.log` | 依据 `general/writing-for-llm/SKILL-MECHANICS.md:34` 与 `check_skill.py` 实现 (全文无标题判断); 两份差异表第 2 行标为人工结论 |
| 差异表逐条对照上游原文行号 | `DIFF-ANCHORS.md` (32 行) | 由 `check-diff-anchors.py --markdown` 生成, 引文按行号实际取出并断言命中, 不是手抄 |

## 跑过的命令与退出码

| 命令 | 结果 |
| --- | --- |
| `uv run python docs/changes/verification-skills/evidence/ISSUE-20/check-diff-anchors.py` (更正前) | `checks=116 failures=15`, 退出码 1 |
| `uv run python docs/changes/verification-skills/evidence/ISSUE-20/check-diff-anchors.py` (更正后) | `checks=116 failures=0`, 退出码 0 |
| `uv run python general/writing-for-llm/check_skill.py workflow/blast-radius/SKILL.md` | `OK`, 退出码 0 |
| `uv run python general/writing-for-llm/check_skill.py workflow/benchmark-checklist/SKILL.md` | `OK`, 退出码 0 |
| 全角标点扫描 (两份 `PROVENANCE.md` + 本证据目录, 含 U+2014) | 无命中, rg 退出码 1 |
| `uv run python docs/changes/verification-skills/evidence/ISSUE-13/check-provenance-artifacts.py` | `checks=50 failures=0`, 退出码 0 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | `7 passed, 18 subtests passed` |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed`; 失败集合与 `evidence/BASELINE.md` 的 6 条逐条相同 |

## 会话与临时项目

本轮不适用: ISSUE-20 是纯文档更正, 不新增或改变技能行为, 不要求真实会话演练. 未开 herdr 会话, 未建临时项目, 无需要清理的资源. 行为保真演练仍在 `../ISSUE-13/TS-002-drill.md`, 本轮未改技能正文, 该结论继续有效.

## 提交

- 实现提交: `ac067a3e49d9f5156a835631093410d360fcc145` (`feat: ISSUE-20: 更正两份 PROVENANCE 差异表的调用方式与标题结构说法`), 分支 `issue/20`, 父提交 `5c21b0b`.
- 本 HANDOFF 单独一个提交, 见 `git log --oneline -2`; HANDOFF 里不写自己的哈希, 避免自指.

## 缺口 / 风险 / 未验证项

- 差异表的行位置不是稳定锚点: 以后增删行会让 `check-diff-anchors.py` 的行号断言失效. 这是刻意的, 失效时应当重新对照上游原文, 而不是放松断言.
- 对照脚本只验证位置与两处说法, 不判断中文译文是否忠实. 忠实性仍由人工通读与 ISSUE-13 的三条 translate-a-skill 校验承担.
- 未验证项: 无. 本轮没有行为变更, 不需要新的行为演练.
- 风险: `benchmark-checklist` 差异表第 6 行仍记录 "工具名未逐项列" 属既有记录, 不在本 ISSUE 范围 (属 H2 类的引用编号问题), 本轮未改.
