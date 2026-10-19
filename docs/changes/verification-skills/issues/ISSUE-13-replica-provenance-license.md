## 父级

- `../EXECUTION.md`

## 执行

- [ ] 已实现

## 要构建什么

为 `workflow/blast-radius/` 与 `workflow/benchmark-checklist/` 补齐共同交付要求: 每个复刻包随附完整 MIT 版权/许可/免责文本, 记录固定来源 SHA `4382e687a50b8d2c5ce4d141d001186589cff8d5`, 并用可复核文件记录源版位置/目标版位置/影响/处理决定的逐项行为差异; 用 translate-a-skill 的既有命令与语义规则核对中文正文, 不把 `check_skill.py` 当标点或翻译忠实性校验器; 最后在临时项目分别加载两个复刻, 各跑一个代表场景, 对照差异记录确认汉化后的实际行为未偏离. 交付后, 读者能从两个技能包内直接读到许可, 来源和差异记录, 并看到实际执行的校验命令, 会话记录与行为对照结果.

## 覆盖依据

- Product: `../PRODUCT.md`, BR-010
- Technical: `../TECHNICAL.md`, 两项复刻的共同交付要求, 测试接缝 (BR-010 行)

## 相关决策

- `../DECISIONS.md`: D021, D024, D037

## 允许范围

- 在 `workflow/blast-radius/` 与 `workflow/benchmark-checklist/` 内新增 `LICENSE` 与 `reference/PROVENANCE.md` (或同义必要说明文件).
- 必要时修正两个复刻的中文正文以通过 translate-a-skill 的语义与标点核对, 但不得改变已确认行为.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-13/`.
- 在临时项目复制两个复刻到 `.agents/skills/`, 用 `/skill:blast-radius` 与 `/skill:benchmark-checklist` 各跑一个代表场景并保存记录.

## 禁止范围

- 不改 PRODUCT.md, TECHNICAL.md, DECISIONS.md 或已确认行为.
- 不把许可只放外部临时材料或只写作者名/链接.
- 不新建统一审计平台或强制所有技能共用的文件协议.
- 不自动提交/推送/开 PR/合并.

## 代码定位提示

- 目标包: `workflow/blast-radius/`, `workflow/benchmark-checklist/`.
- 必读: `../DECISIONS.md` F008 (固定 SHA 与许可原文), F012/F013/F014 (借用范围), 账本末尾的 MIT 原文; `general/translate-a-skill/SKILL.md` 第 7 节校验命令; `general/writing-for-llm/check_skill.py` 只用于 frontmatter, 不用于翻译忠实性.
- 源文: 从固定 SHA 的 `pstack/skills/blast-radius/SKILL.md`, `pstack/skills/benchmark-checklist/SKILL.md`, `pstack/LICENSE` 只读获取.

## TDD 切片

- TS-001:
  接缝: blast-radius / benchmark-checklist -> 固定上游到汉化源文件的对照接口 (TECHNICAL.md 测试接缝 BR-010 行); 适配器为各复刻包随附的完整 MIT 文本, 交付报告引用的固定 SHA 来源与逐项差异记录/校验材料.
  测试用例: TC-102.
  先写的失败测试: `check-provenance-artifacts` 在 `LICENSE` 与 `reference/PROVENANCE.md` 尚不存在时失败; 命令检查两个包内没有完整 Copyright/许可/免责段, 也没有固定 SHA 或差异表.
  最小绿色实现范围: 两个包各含完整 MIT 正文; 差异记录含源版位置/目标版位置/影响/处理决定; 写明固定 SHA 与未追 main; 记录 translate-a-skill 的标点/残留英文/标题结构命令及结果; 保留核心步骤/强度/数量/例外/完成条件.
  不得测试: 用 `check_skill.py` 代替翻译忠实性检查; 不测未确认的统一审计格式.
  覆盖: BR-010 (静态交付).
- TS-002:
  接缝: blast-radius / benchmark-checklist -> 关键安全事实调查与实证接口, 占测量前主张与工具检查接口 (TECHNICAL.md 测试接缝 AC-021/AC-025 行); 适配器为临时项目真实会话.
  测试用例: TC-108.
  先写的失败测试: `drill-replica-translation-fidelity` 在差异记录或实际运行记录缺失时无法对照; 预期失败于没有可对照的差异记录, 或汉化后的代表场景行为与原版记录不一致.
  最小绿色实现范围: 在临时项目分别加载两个复刻, blast-radius 跑一次关键事实真实代码证明, benchmark-checklist 跑一次至少 5 次交替的前后对比; 保存会话记录, 命令输出与差异记录对照结论.
  不得测试: 不重复两个复刻的全量行为验收 (归 ISSUE-06/07/08/09); 不测未确认的模型或固定统计阈值.
  覆盖: BR-010 (行为保真).

## 验证入口

- `test -f workflow/blast-radius/LICENSE && test -f workflow/benchmark-checklist/LICENSE` 且两份均含完整 MIT 版权/许可/免责段.
- `rg -n "4382e687a50b8d2c5ce4d141d001186589cff8d5" workflow/blast-radius workflow/benchmark-checklist` 有命中; `rg -n "Copyright \(c\) 2026 Lauren Tan" workflow/blast-radius workflow/benchmark-checklist` 有命中.
- 按 translate-a-skill 第 7 节运行全角标点扫描与残留英文/标题结构检查, 结果存入 `docs/changes/verification-skills/evidence/ISSUE-13/`.
- 在临时项目按 `/skill:blast-radius` 与 `/skill:benchmark-checklist` 各跑一个代表场景, 保存会话记录, 命令输出与差异记录对照到 `docs/changes/verification-skills/evidence/ISSUE-13/`; 通过标准: 许可随包, 固定 SHA 与差异表可复核, 标点无命中, 残留英文均有理由, 两个代表场景的实际行为与差异记录一致.

## 风险提示

- 上游源文必须按固定 SHA 读取, 不用浮动 main; 网络不可用时记录来源限制, 不编造差异.
- 中文翻译校正不得削弱 must/never/only/at most 的强度或删掉例外条件.
- 许可文本必须随技能包复制, 不能只存本变更目录.

## 停止条件

需要改变任一 Spec, 决策, 行为语义或扩大范围时停止; 无法取得固定来源或许可原文时停止并报告.

## 适合 AFK 的原因

固定来源, 许可要求, 差异记录字段, 校验命令和两个代表场景已由 Spec 与 translate-a-skill 固定; 只需文档核对, 机械检查和临时项目实跑, 无需产品/架构决策.

## 验收标准

- [ ] 两个复刻包内均有完整 MIT 版权/许可/免责文本.
- [ ] 差异记录含固定 SHA, 源/目标位置, 影响和处理决定.
- [ ] 中文正文通过 translate-a-skill 的标点与语义检查, 强度与例外未削弱.
- [ ] 两个复刻各跑一个代表场景, 实际行为与差异记录一致.
- [ ] 校验命令与结果可复核, 不以 `check_skill.py` 冒充翻译校验.

## 被阻塞于

- ISSUE-07, ISSUE-09.
