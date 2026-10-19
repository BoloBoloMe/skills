# Standards 第二轮复核

来源:
- `AGENTS.md`, `README.md`.
- `general/writing-for-llm/SKILL.md`, `SKILL-MECHANICS.md`, `GLOSSARY.md`; `general/translate-a-skill/SKILL.md`.
- `docs/adr/0020-independent-product-acceptance.md`, `0021-project-verification-recipes-not-acceptance-authority.md`; 关联 `docs/changes/verification-skills/DECISIONS.md` 的 D021/F018 写作与适配约定.
- `workflow/code-review/SKILL.md`, `workflow/code-review/references/fowler-baseline.md` 全文. 仓库规范优先, Fowler 只作判断依据.

```bash
git rev-parse --verify '5c21b0b^{commit}'
git diff 5c21b0b...HEAD -- . ':(exclude)docs/changes/verification-skills/evidence'
git log 5c21b0b..HEAD --oneline
```

对象: `v2`, `5c21b0b...f6cde39`. 基准有效, diff 非空. 只审规范, 不判 spec 符合性. 每条发现均已通读对应文件; evidence 仅读首轮两报告与两份固定上游副本. 辅核 `check_skill.py` 实现, 不重复评判工具已覆盖的字段约束. 下列技能路径相对 `workflow/`.

## 首轮 H1-H6/J1

- **H1 部分修复.** `benchmark-checklist/SKILL.md` 已清除非 ASCII 破折号和非警告的 "被". 但 `:62` 的列举句仍有 64 个汉字, `:78,104,108` 也超长. 仍违反 translate-a-skill `:79` 的单句不超 25 字规则; 换同义词不等于拆句.
- **H2 已修.** `benchmark-checklist/SKILL.md:11` 给出编号与节名对照, `:104,118` 的第 4/7 问现在能独立定位.
- **H3 部分修复.** `blast-radius/SKILL.md:15-17,33-35,53` 已拆句并改主动. 但 `:24` 原有中文命令注释仍写 "符号被增删", 不属警告, 未满足 translate-a-skill `:80` 的全文禁字要求. 这是旧残留, 不是新增违规.
- **H4 原列位置已修.** `blast-radius/SKILL.md:9,43` 已用 "你"; `verify-change/SKILL.md:12,17,35,41,68,95` 和 `benchmark-checklist/SKILL.md:102,108` 已改 "我". 本轮另有同因新增问题, 见 N1.
- **H5 已修.** 两份 `blast-radius/reference/PROVENANCE.md:37` 与 `benchmark-checklist/reference/PROVENANCE.md:37` 均改为仅描述措辞变化. 抽查上游与本地第 4 行, 都是 `disable-model-invocation: true`.
- **H6 已修.** `blast-radius/reference/PROVENANCE.md:38,94-95` 已明确标题靠人工核对, 不再扩大机检保证; 与 SKILL-MECHANICS `:34` 及脚本实现一致. 人工结果另有 N2.
- **J1 已修.** `maintain-verification-skill/SKILL.md:31-35` 保留判据; `reference/drift-classification.md:3,7-11` 改为回指与具体样例, 原重复分类表和顺序规则已删除.

## 新发现

### 硬性违规

- **N1, 叙述视角倒退.** `create-verification-skill/SKILL.md:27,38` 与 `maintain-verification-skill/SKILL.md:40,51` 新增 "交用户批准"/"转给用户决定". 这里指发令与批准的人, 不是固定术语 "用户调用". 违反 writing-for-llm `:80`, 应统一成 "我".
- **N2, 来源记录错位.** `blast-radius/reference/PROVENANCE.md:95` 新写的人工结论仍称七个 H2, 实际 `SKILL.md:13-98` 有八个. 新增第 5 节后, 差异表 `:44-52` 的第 5/6/7 节引用也未随之更新. 不满足 translate-a-skill `:50,141` 的准确差异位置与标题核对要求. 应按现有节名重核, 而非保留旧计数.

### 判断性发现

- **N3, 可能是 Duplicated Code (重复指令).** `create-verification-skill/SKILL.md:33-40` 与 `maintain-verification-skill/SKILL.md:46-53` 重复批准绑定, 换范围再批准与授权下传规则, 其中两段逐字相同. 对应新增 hunk `@@ -22,6 +22,23 @@` / `@@ -28,13 +28,30 @@`. 依据 Fowler 同名条目及 writing-for-llm `:108` 的单一真相源原则. 可保留各自资源清单, 把共用规则放一处, 用写入前必读指针承接, 避免两处修订不同步.

汇总: 首轮 5 项关闭, H1/H3 部分修复; 新增硬性违规 2 项, 判断性发现 1 项. 仅新增本报告, 未改实现, 未启动 agent 会话.
