## 父级

- `../EXECUTION.md`

## 执行

- [x] 已实现

## 要构建什么

更正两份 `reference/PROVENANCE.md` 的差异表: 上游两份 SKILL.md 第 4 行原本已有 `disable-model-invocation: true`, 不得把措辞汉化记成调用模式改变, 差异记录要按实际对比结论改写并注明依据; 不得声称 `check_skill.py` 校验标题结构, 标题结构检查要标为人工检查.

## 覆盖依据

- 评审发现 (权威): `../evidence/code-review/STANDARDS.md` H5 与 H6.
- 决策: `../DECISIONS.md` D021, D024, D037; 固定来源 SHA `4382e687a50b8d2c5ce4d141d001186589cff8d5`.
- 上游材料: `../evidence/ISSUE-13/upstream/` 下的两份源文件.

## 允许范围

- 修改 `workflow/blast-radius/reference/PROVENANCE.md` 与 `workflow/benchmark-checklist/reference/PROVENANCE.md`.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-20/`.

## 禁止范围

- 不改技能正文、许可文本、固定 SHA 与借用范围; 不改权威输入; 不自动提交/推送/合并.

## TDD 切片

- TS-001 接缝: 差异记录 -> 上游原文对照. 红: 差异表把未变化的 frontmatter 记为模式改变, 并夸大机检范围; 绿: 每条差异都能指到上游原文行与本地行, 机检与人工检查分列. 覆盖 H5/H6.

## 验证入口

- `check_skill.py` 两份技能仍退出 0; 全角标点扫描新增文字无命中.
- 差异表逐条对照 `evidence/ISSUE-13/upstream/` 原文, 对照记录存 `evidence/ISSUE-20/`.
- 全量快层不超基线 6 条.

## 停止条件

无法取得上游原文或需要改行为语义时停止报告.

## 验收标准

- [ ] 两份差异表不再把未变的 frontmatter 记为模式改变, 有原文对照证据.
- [ ] 机检与人工检查分开表述, 有证据.
