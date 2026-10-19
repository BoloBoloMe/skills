# Standards review

## 规范来源与范围

已逐项读取:
- `AGENTS.md`, `README.md`.
- `general/writing-for-llm/` 下 `SKILL.md`, `SKILL-MECHANICS.md`, `GLOSSARY.md`, `check_skill.py`.
- `general/translate-a-skill/SKILL.md`.
- `docs/language/UBIQUITOUS_LANGUAGE.md`, `workflow/domain-awareness/WORKFLOW_VOCABULARY.md`.
- `docs/adr/0020-independent-product-acceptance.md`, `docs/adr/0021-project-verification-recipes-not-acceptance-authority.md`; 其关联 `docs/changes/verification-skills/DECISIONS.md` 的写作约定与适配例外.
- `workflow/code-review/SKILL.md`, `workflow/code-review/references/fowler-baseline.md` 全文.
- `workflow/blast-radius/reference/` 下 `PROVENANCE.md`, `multimodel.md`, `report-style-zh.md`; `workflow/benchmark-checklist/reference/PROVENANCE.md`; `workflow/maintain-verification-skill/reference/drift-classification.md`.

分支 `v2`, 基准 `ec9d55f`, 顶端 `53e75b4`. 基准有效, diff 非空.

```bash
git diff ec9d55f...HEAD -- . ':(exclude)docs/changes/verification-skills/evidence'
git log ec9d55f..HEAD --oneline
```

只审规范, 不审 spec 符合性. 所有发现均已读取完整文件. 仓库规则覆盖 Fowler 基线; 跳过工具已覆盖的名称/frontmatter/许可等机械检查. evidence 仅少量抽查, 未全量读取. 同因跨文件位置合并计数.

## 硬性违规 (6 项)

### workflow/benchmark-checklist/SKILL.md

- H1, `:38,60,70`: 使用非 ASCII 破折号 U+2014, 非警告正文使用"被", 并有超过 25 字的中文句子. 依据 `general/translate-a-skill/SKILL.md:79-80` 的短句/主动句硬规则及第 7 节 ASCII 标点要求. 应拆句并改主动表达.
- H2, `:102,108,116`: 引用"第 4/7 问", 但本文已删除问题编号. `reference/PROVENANCE.md:41` 声称改为节名加原编号, 实际没有落实. 依据 translate-a-skill 第 4 节"无需对照英文"的完成标准. 应引用现有节名或恢复编号.

### workflow/blast-radius/SKILL.md

- H3, `:15,31,33,51`: 非警告叙述出现"被写成这样", 多处中文句子超过 25 字. 同样违反 translate-a-skill 第 4 节语法切割规则, 应拆成独立动作句.
- H4, `:9,41`: "我的角色"和"我说是这样"把执行 agent 写成"我". 同因位置: `workflow/verify-change/SKILL.md:12,17,35,40,47,68,94` 与 `workflow/benchmark-checklist/SKILL.md:100,106` 把指挥者写成第三人称"用户". 依据 `general/writing-for-llm/SKILL.md:80`: 人是"我", agent 是"你". 应统一视角, 避免混淆执行与批准角色.

### 两份 reference/PROVENANCE.md

- H5, `workflow/blast-radius/reference/PROVENANCE.md:37` 与 `workflow/benchmark-checklist/reference/PROVENANCE.md:37`: 都称从模型调用改为用户调用, 但仓库内 `docs/changes/verification-skills/evidence/ISSUE-13/upstream/` 的两份 `*-SKILL.md:4` 原本已有 `disable-model-invocation: true`. 未记录运行时语义差异依据, 不能把措辞汉化算作模式改变. 依据 translate-a-skill 第 2 节"本地化措辞差异没有被误判为行为差异". 应更正差异表或补实证依据.
- H6, `workflow/blast-radius/reference/PROVENANCE.md:38`: 声称 H2 结构由 `check_skill.py` 校验通过, 但该脚本不检查标题. 依据 `general/writing-for-llm/SKILL-MECHANICS.md:34` 明定的检查范围及 `check_skill.py` 的实现. 应区分人工结构检查与脚本结果, 不扩大机检保证.

## 判断性发现 (1 项)

### workflow/maintain-verification-skill/

- J1, 可能是 Duplicated Code (同一指令重复): `SKILL.md:31-35` 与 `reference/drift-classification.md:8-13` 重复三类判据及判断顺序. 对应新增 hunk `+1,62` / `+1,26`. 依据 Fowler 同名坏味道与 writing-for-llm 第 108 行的单一真相源原则. 建议保留一份判据, 参考文件专放混淆例子, 避免以后两处维护不一致.

合计: 硬性违规 6 项, 判断性发现 1 项. 最严重为 H4 的执行者/批准者视角混淆; 本报告不据此推断已发生错误操作.
