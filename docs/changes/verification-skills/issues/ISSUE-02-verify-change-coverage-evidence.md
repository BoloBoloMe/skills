## 父级

- `../EXECUTION.md`

## 执行

- [x] 已实现

## 要构建什么

在 `workflow/verify-change/SKILL.md` 增加全量覆盖与证据标注切片: 验收报告逐项列出 PRODUCT.md 的全部验收场景和标为审计的业务规则, 并区分当前观察, 引用的旧观察, 仅推断, 未运行; 只有摘要而无原始材料时要求补证, 原始记录与摘要冲突时拒绝通过并报告差异. 交付后, 含 12 个场景, 3 条审计 BR 和一个不可运行项的临时项目能得到完整逐项结果, 整体不虚报全部通过.

## 覆盖依据

- Product: `../PRODUCT.md`, AC-002, AC-003
- Technical: `../TECHNICAL.md`, 模块接口 (verify-change 的证据和结果, 可读取原始材料位置), 测试接缝 (AC-002/AC-003 行)

## 相关决策

- `../DECISIONS.md`: D009, D015, D031, D033, D035, D040

## 允许范围

- 修改 `workflow/verify-change/SKILL.md`; 必要时新增或修改 `workflow/verify-change/reference/*.md`.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-02/`.
- 临时项目内构造 PRODUCT.md, 审计规则材料, 旧证据与冲突记录.

## 禁止范围

- 不改 ISSUE-01 已定的判据来源, 目标版本和证据目录规则.
- 不实现非作者委派, 场景组, 复验, 写入授权和条件方法调用.
- 不修改既有技能, 全局部署, PRODUCT.md, TECHNICAL.md, DECISIONS.md.
- 不自动提交/推送/开 PR/合并.

## 代码定位提示

- 入口: `workflow/verify-change/SKILL.md` 的输入核对与结果输出节.
- 必读: `workflow/navigate/ACCEPTANCE-GUIDE.md` 的逐项报告规则, `workflow/explain-diff/SKILL.md` 的证据缺口规则, `workflow/to-spec/GHERKIN.md` 的审计 BR 定义.
- 演练: 沿用 ISSUE-01 的临时项目与 `/skill:verify-change` 加载方式; 另建一个只给摘要的会话和一个摘要与原生记录冲突的会话.

## TDD 切片

- TS-001:
  接缝: verify-change -> 逐项覆盖与结果接口 (TECHNICAL.md 测试接缝 AC-002 行); 适配器为含场景与不同审计材料的临时 Product.
  测试用例: TC-002.
  先写的失败测试: `drill-full-coverage-audit` 在当前技能只有基础输入规则时, 报告只覆盖与 diff 相关的场景, 且静态审计与运行审计混为一谈; 预期失败于漏列未受影响场景或把运行审计用静态材料顶替.
  最小绿色实现范围: 报告覆盖全部场景与审计 BR; 静态材料核对与运行记录分开; 不可执行项保持未验证并说明缺口; 不用总标签隐藏失败与未验证.
  不得测试: 内部报告模板措辞; 不测未确认的审计分类算法.
  覆盖: AC-002.
- TS-002:
  接缝: verify-change -> 报告与证据引用接口 (TECHNICAL.md 测试接缝 AC-003 行); 适配器为当前真实输出, 有效旧输出, 仅推断与不可运行的独立材料集.
  测试用例: TC-003.
  先写的失败测试: `drill-evidence-types-and-conflict` 在当前技能没有证据分级规则时, 会话会把摘要当运行记录, 或只核对材料路径存在; 预期失败于未区分观察/旧观察/推断/未运行或未发现原生记录与摘要冲突.
  最小绿色实现范围: 标注材料类型与引用信息; 摘要无原件不算充分; 冲突时拒绝通过并要求实际验收者核实; 指挥者不补跑成品; 报告仍需用户逐项确认.
  不得测试: 原始材料的固定存储格式; 不测未确认的脱敏字段.
  覆盖: AC-003.

## 验证入口

- `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` 退出 0; 全角标点扫描无命中.
- 按 TS-001/TS-002 跑真实会话, 保存会话记录, 逐项报告, 原始材料与冲突记录到 `docs/changes/verification-skills/evidence/ISSUE-02/`; 通过标准: 12 个场景与 3 条审计 BR 全部有结果, 静态与运行审计可区分, 不可运行项未验证, 摘要缺原件被要求补证, 冲突被拒绝并报告差异.

## 风险提示

- "原始材料" 可能出现多种形态: 会话记录, 命令输出, 截图, 文件状态; 不要强行统一成一种格式, 也不要用明文密钥.
- 冲突演练要保留同一目标版本与同一请求的两份材料, 否则无法证明冲突.

## 停止条件

需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 无法取得可读取原始材料时停止并报告缺口.

## 适合 AFK 的原因

覆盖范围, 审计材料类型和证据纪律已由 Spec 固定; 演练只用临时项目, 无需产品决策.

## 验收标准

- [ ] 报告逐项覆盖全部场景与审计 BR, 不只列 diff 相关项.
- [ ] 静态核对与运行结果分开标注.
- [ ] 当前观察, 旧观察, 推断, 未运行可区分.
- [ ] 仅有摘要不算充分证据; 摘要与原生记录冲突时拒绝通过并报告.

## 被阻塞于

- ISSUE-01.
