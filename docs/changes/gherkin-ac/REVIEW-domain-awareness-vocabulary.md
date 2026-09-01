# 审核报告: domain-awareness 元词汇表落地

- 对象: workflow/domain-awareness/WORKFLOW_VOCABULARY.md (新建), workflow/domain-awareness/SKILL.md (改动)
- 依据: docs/changes/gherkin-ac/DECISIONS.md D018 (L131-137), D020 (L147-153), F007 (L202-205); UBIQUITOUS_LANGUAGE_FORMAT.md
- 日期: 审核时两文件均为未提交状态 (git status: M SKILL.md, ?? WORKFLOW_VOCABULARY.md)

## 逐项结论

### 1. 词条唯一性 — 通过
WORKFLOW_VOCABULARY.md L5-8 仅有 `权威输入` 一个词条, 无扫描阶段其他候选词夹带. 符合"用户已审定只收一词".

### 2. 词条内容 — 通过
- 优先级在场: L7 "优先级: spec 优先于决策账本", 与 D020 一致.
- 理由在场: L7 "(spec 是决策的提炼产物, 直接读账本费 token)", 与 F007 一致.
- 冲突处理在场: L8 "冲突时停止并盘问用户, 不自行改写权威方".
- _避免_ 项合理: 两条均为行为反模式 (口头指示未落盘不算权威输入; 有 spec 时绕过优先级读账本), 紧扣定义无泛化. 格式沿用 `**术语**:`/定义/`_避免_:` 模式 (L5-8), 符合 D018 与 FORMAT 范式.
- 说明: FORMAT.md 的"示例对话"节未出现, 但 D018 只约定术语/定义/_避免_ 三件套, 不算缺失.

### 3. 定位声明 (两层语义) — 通过
L3 明确: 元词汇表固定不变, 与目标仓库无关; 项目领域语言 (UBIQUITOUS_LANGUAGE.md) 由探测所得, 因仓库而异; 并点名与 UBIQUITOUS_LANGUAGE.md 的区别. 与 D018 "语义分两层"一致.

### 4. 收录标准维护规则 — 通过
L10-12: "≥2 个 workflow skill 共用, 或单 skill 使用但定义非显然; 一眼自明的词不收. 新词须经用户审定才落盘." 覆盖 D018 收录标准且补上用户审定门槛.

### 5. SKILL.md 改动 — 通过
git diff: +5/-1, 无无关重写.
- 新增 `# 恒定返回: workflow 元词汇表` 段 (L53-55): "无论目标仓库探测结果如何, 本 skill 的输出都包含指向 WORKFLOW_VOCABULARY.md 的引用", 恒定返回语义完整; 段内重述两层语义, 与词汇表定位声明一致.
- 原有探测职责 (文件结构/读取流程/行为约束) 未动.
- 完成标准 (L59) 同步追加 "以及 workflow 元词汇表引用", 与旧句以括号重组, 改动最小.

### 6. 文风 — 通过 (附建议)
`grep -P '[\x{3000}-\x{303F}\x{FF00}-\x{FFEF}…]'` 两文件均无全角/弯引号命中. 中文正文.
- 建议 (非阻断): WORKFLOW_VOCABULARY.md L3 使用 U+2014 破折号 "—", 非 ASCII 标点; 但 DECISIONS.md (L134 等) 已同款先例, 保持现状可接受.

## 总体结论

可放行. 6 项审核方向全部通过, 无严重/警告级偏差; 仅 1 条非阻断建议 (破折号非 ASCII, 有仓库先例).
