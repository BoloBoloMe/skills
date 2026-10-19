# ISSUE-22 HANDOFF

## 交付了什么

`workflow/benchmark-checklist/SKILL.md` 两处收口:

1. TS-001 例外边界: `## 粗估与选型` 的豁免清单删掉 `## 基线与脚本固定前`, 只留 `## 两侧按生产方式调优`, `## 重复与波动`, `## 收益上限与端到端`. 补三句边界: 这两项检查不由粗估豁免; 基线用于规划或脚本准备固定时仍按那一节检查; 规划前先审基线方法与适用条件, 固定成团队入口前先补齐错误数与工作量. 该节完成标准追加 "用于规划或固定脚本时, 那一节的检查已做".
2. TS-002 长句: 修前第 62, 78, 104, 108 行按动作拆句, 保持主动语态. 四段最长句从 64/50/38/69 字降到 23/20/21/22 字.

未改其他技能, 未改测量方法, 未改 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md`, 未改 `reference/PROVENANCE.md`.

## 验收标准对应证据

| 验收标准 | 证据 | 结果 |
| --- | --- | --- |
| 例外边界收口到只豁免其余五问, 有 diff 证据 | `TS-001-exemption-boundary.md`, `diff.patch`, `red.log` (修前越界), `green.log` (修后零命中) | 通过 |
| 长句已拆, 有长度检查证据 | `TS-002-sentence-length.md`, `sentence-lengths.log` (修前/修后逐句字数), `green.log` | 通过 |

## 跑过的命令与退出码

| 命令 | 结果 |
| --- | --- |
| `uv run python .../ISSUE-22/check-issue22.py --selftest` | 四类规则全覆盖, 合格样本零误报, 退出 0 |
| `uv run python .../ISSUE-22/check-issue22.py workflow/benchmark-checklist/SKILL.md` | 修前 12 处命中退出 1; 修后 `OK` 退出 0 |
| `uv run python general/writing-for-llm/check_skill.py workflow/benchmark-checklist/SKILL.md` | `OK`, 退出 0 |
| 全角标点 / U+2014 / 被 三组 rg 扫描 (SKILL.md 与本证据目录) | 无命中, 退出 1 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | `7 passed, 18 subtests passed`, 退出 0 |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed`, 退出 1; 6 条与 `evidence/BASELINE.md` 逐条相同, 未超基线 |

全部原始输出: `machine-checks.log`, `tests.log`, `red.log`, `green.log`, `sentence-lengths.log`.

## 会话与临时项目

本轮不适用: ISSUE 原文写明小范围文本修订, 不要求真会话演练. 两条断言是文本属性 (豁免清单的节名, 句子长度), 机械扫描给出可复核结论, 再开会话不会产出更硬的证据. 未开 herdr 会话, 未建临时项目, 无资源需要清理.

## 提交

- 实现提交: `ba890cccf54fa808c80c011cfe3c3b00b71a9bb9` (`feat: ISSUE-22: 收口粗估例外边界并拆分指定长句`), 分支 `issue/22`, 父提交 `711b463`.
- 本 HANDOFF 单独一个提交, 见 `git log --oneline -2`; HANDOFF 里不写自己的哈希, 避免自指.

## 缺口 / 风险 / 未验证项

- 残留风险: 按句号切分, 全文另有约 60 句超 25 字, 都是修前既有文本, 不在评审点名的四处, 本 ISSUE 未改. 若下一轮要求全文按句达标, 需要单独 ISSUE 定范围.
- 判定方式限制: 边界规则靠文本扫描 (豁免清单节名 + 规划审查句 + 固定检查句), 不模拟读者行为; 语义是否被读成"粗估仍免固定检查"只能靠人工通读, 已由 `diff.patch` 供复核.
- 未验证项: 无. 没有行为变更, 不需要新的行为演练.
