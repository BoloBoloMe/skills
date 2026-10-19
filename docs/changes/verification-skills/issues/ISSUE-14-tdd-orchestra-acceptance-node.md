## 父级

- `../EXECUTION.md`

## 执行

- [x] 已实现

## 要构建什么

在 `workflow/tdd-as-orchestra/SKILL.md` 的执行循环中接入独立产品验收节点: 最后一轮评审没有新须重构发现项后, 停止并汇报前另开独立会话使用 verify-change; 实现指挥者不亲自使用; 验收发现明确实现问题则拆新 ISSUES 回重构/实现/合并/评审, 评审收敛后再次验收; 环境/权限/标准/证据缺口按原停止条件处理, 不塞进重构; 收尾把验收报告路径, 覆盖提交和逐项结果交给 explain-diff 执行者, 讲解页引用该报告并显示未验证范围, 无报告或必验项证据未齐不得正常收尾. 交付后, 临时最小任务中的派发顺序, 失败回路和收尾交接都可核对.

## 覆盖依据

- Product: `../PRODUCT.md`, AC-014, AC-015
- 交付 Git 事实: 本 issue 只记录 AC-032-3 的前置事实, 主验归 ISSUE-15 的 TC-032
- Technical: `../TECHNICAL.md`, 模块接口 (tdd-as-orchestra 的改动接口), 测试接缝 (AC-014/AC-015 行), 关键流程 1

## 相关决策

- `../DECISIONS.md`: D007, D018, D030, D031, D035, D040

## 允许范围

- 修改 `workflow/tdd-as-orchestra/SKILL.md` 的执行循环与收尾节点.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-14/`.
- 临时 Git 仓库内准备最小任务, 完成态 ISSUES, 评审结论, 验收报告和 worktree 现场.

## 禁止范围

- 不修改 verify-change 的验收判据; 不把验收细节内联回实现指挥者.
- 不修改 code-review, explain-diff, tdd, navigate 等既有技能.
- 不自动提交/推送/开 PR/合并 (既有 tdd-as-orchestra 本地提交与合并职责保持不变).
- 不修改既有三份权威输入与全局部署.

## 代码定位提示

- 入口: `workflow/tdd-as-orchestra/SKILL.md` 的 `# 执行循环`.
- 必读: `workflow/verify-change/SKILL.md`, `workflow/code-review/SKILL.md`, `workflow/explain-diff/SKILL.md`, `workflow/navigate/ACCEPTANCE-GUIDE.md`.
- 演练: 临时 repo 预置"全部 ISSUE 完成, 合并完成, 最后一轮评审无发现"的现场; 另预置一份含一个实现问题和一个环境缺口的验收报告.

## TDD 切片

- TS-001:
  接缝: tdd-as-orchestra -> 评审收敛后的独立验收节点 (TECHNICAL.md 测试接缝 AC-014 行); 适配器为具有既有执行输入的最小临时任务, 实际派发/收尾顺序及讲解产物.
  测试用例: TC-014.
  先写的失败测试: `drill-acceptance-before-stop` 在当前流程没有验收节点时, 评审收敛后直接进入 explain-diff/停止汇报; 预期失败于没有独立 verify-change 会话或实现指挥者亲自验收.
  最小绿色实现范围: 最后一轮评审无新须重构项才进入; 另开独立验收指挥会话, 实现指挥者不亲自使用 verify-change; 产品检查通过才正常停止并生成讲解页; 未通过用户确认仍待人工验收.
  不得测试: 固定会话数或固定模型; 不测 code-review 双轴内部措辞.
  覆盖: AC-014.
- TS-002:
  接缝: tdd-as-orchestra -> 验收发现项回重构与阻塞出口 (TECHNICAL.md 测试接缝 AC-015 行); 适配器为实现缺陷和环境缺口两类验收回传, 实际 Issue/循环/评审/复验记录.
  测试用例: TC-015.
  先写的失败测试: `drill-acceptance-failure-loop` 在当前流程没有失败回路时, 验收报告的实现问题会被直接汇报或自行修复; 预期失败于未拆新 ISSUES 回重构或把环境缺口塞进重构.
  最小绿色实现范围: 明确实现问题拆新 ISSUES 回重构/实现/合并/评审, 评审收敛后再验收; 环境/权限/标准/证据缺口按原停止条件报告, 不进重构; 不直接跳到汇报.
  不得测试: 固定 Issue 数量或修复方式; 不测未确认的缺陷根因.
  覆盖: AC-015.
## 验证入口

- `uv run python general/writing-for-llm/check_skill.py workflow/tdd-as-orchestra/SKILL.md` 退出 0; 全角标点扫描无命中.
- 按 TS-001/TS-002 在临时 repo 跑真实会话, 保存评审结论, 验收会话记录, 失败回路 Issue 与评审/复验记录, 收尾讲解页引用与 Git 时间线到 `docs/changes/verification-skills/evidence/ISSUE-14/`; 通过标准: 验收在停止前发生且由独立会话执行, 实现问题回路完整, 环境缺口不进重构, 收尾引用报告与提交. 演练记录同时保留本地提交/合并在验收前完成的 Git 时间线, 供 ISSUE-15 的 TC-032 审计 AC-032-3.

## 风险提示

- 这是流程文本改动, 演练要观察真实会话与文件, 不只读 SKILL.md.
- 临时 repo 的预置现场必须明确标注, 不能把预置状态说成完整跑完了上游所有节点.
- 收尾门不能由实现指挥者用摘要自我放行; 必须核对报告逐项结果与未验证范围.

## 停止条件

需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 验收节点无法真实派发或报告缺证据时按停止条件报告.

## 适合 AFK 的原因

节点位置, 失败回路和收尾交接已由 Spec 固定; 演练只在临时 repo 与临时会话内进行.

## 验收标准

- [ ] 最后一轮评审无新须重构项后, 停止前另开独立 verify-change 会话.
- [ ] 实现指挥者不亲自使用 verify-change, 验收不塞进 code-review/explain-diff.
- [ ] 验收实现问题拆新 ISSUES 回重构并重新评审/验收; 环境缺口不进重构.
- [ ] 收尾引用验收报告路径, 覆盖提交和逐项结果, 无报告或证据未齐不正常收尾.

## 被阻塞于

- ISSUE-10.
