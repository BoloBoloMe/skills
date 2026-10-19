# ISSUE-22 证据索引

对象: `workflow/benchmark-checklist/SKILL.md` 的粗估例外边界与四段长句. 修前为提交 `711b463` (工作树起点), 修后见分支 `issue/22` 的 ISSUE-22 提交.

权威依据:
- `../../evidence/code-review/SPEC-2.md` N1 (粗估例外越界豁免规划/固定脚本检查).
- `../../evidence/code-review/STANDARDS-2.md` H1 未闭合部分 (行 62, 78, 104, 108 超长句).
- `../../TECHNICAL.md:54-55` (只免其余五问; 基线与脚本固定前检查独立强制).
- `../../PRODUCT.md:744-755` (AC-031-1/2/3 基线规划审查与脚本固定).

文件:
- `check-issue22.py`: 机械扫描工具. 四类规则: 豁免清单越界, 边界未挂回 (规划审查/固定检查句缺失), 锚点段逐句超 25 字, 全文逐子句超 25 字. 自带 `--selftest` (合格样本零误报, 违规样本四类规则全覆盖, 否则退出 2).
- `red.log`: 修前扫描 (退出 1, 12 处命中) 与工具自检 (退出 0).
- `green.log`: 修后扫描 (退出 0) 与工具自检 (退出 0).
- `sentence-lengths.log`: 四段锚点逐句汉字数, 修前/修后对照表.
- `diff.patch`: `workflow/benchmark-checklist/SKILL.md` 的完整改动.
- `machine-checks.log`: `check_skill.py` 退出 0; 全角标点, U+2014, 被 三组扫描无命中.
- `tests.log`: `general/writing-for-llm/tests` 与全量快层 `-m "not e2e"` 结果.
- `TS-001-exemption-boundary.md`, `TS-002-sentence-length.md`: 两个 TDD 切片的红/绿说明.
- `HANDOFF.md`: 交付报告.

复现:

```bash
uv run python docs/changes/verification-skills/evidence/ISSUE-22/check-issue22.py --selftest
uv run python docs/changes/verification-skills/evidence/ISSUE-22/check-issue22.py workflow/benchmark-checklist/SKILL.md
uv run python general/writing-for-llm/check_skill.py workflow/benchmark-checklist/SKILL.md
```

## 未做与边界

- 本 ISSUE 是小范围文本修订, 按 ISSUE 原文不要求真实 pi 会话演练: 两条断言都是文本属性, 扫描能给出可复核结论, 会话不会给出比扫描更硬的证据.
- 未改 `reference/PROVENANCE.md`, 未改测量方法与其他技能, 未动 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md`.
- 残留风险: 全文还有一批修前就存在的超 25 字句 (按句号切分), 不在本 ISSUE 点名的四处内, 本轮未改.
