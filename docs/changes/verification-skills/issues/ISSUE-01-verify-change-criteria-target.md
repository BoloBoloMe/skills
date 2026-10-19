## 父级

- `../EXECUTION.md`

## 执行

- [ ] 已实现

## 要构建什么

新增 `workflow/verify-change/SKILL.md` 的第一个端到端切片: 一个独立验收指挥会话能读入已确认 PRODUCT.md, 只把产品场景与业务规则当判据, 绑定已提交且干净的起始提交, 并把本轮输出限制在约定证据目录. 本切片只覆盖单验收者, 单轮验收; 多人分工与复验留给后续 issue. 交付后, 临时项目里的真实验收指挥会话能给出逐项产品结果和绑定提交, 缺少 PRODUCT.md 或工作区脏时明确停止.

## 覆盖依据

- Product: `../PRODUCT.md`, AC-001, AC-008
- Technical: `../TECHNICAL.md`, 模块接口 (verify-change 的必需输入, 输出目录), 测试接缝 (AC-001/AC-008 行), 安全策略 (证据目录与脱敏)

## 相关决策

- `../DECISIONS.md`: D010, D026, D031, D033, D035, D040

## 允许范围

- 新建 `workflow/verify-change/SKILL.md`; 必要时新建 `workflow/verify-change/reference/*.md`, 并在 SKILL.md 内引用.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-01/`.
- 在临时目录创建演练项目和夹具, 不写入仓库其他位置.

## 禁止范围

- 不实现非作者委派, 场景组派工, 并行执行, 复验, 写入授权, 条件方法调用; 这些归后续 issue.
- 不修改 PRODUCT.md, TECHNICAL.md, DECISIONS.md, 既有技能, 全局部署.
- 不在演练目标项目中改产品代码, 配置或测试.
- 不自动提交/推送/开 PR/合并.

## 代码定位提示

- 新建入口: `workflow/verify-change/SKILL.md`, frontmatter 按 `general/writing-for-llm/SKILL.md` 与 `general/writing-for-llm/check_skill.py` 的约束写.
- 必读: `workflow/to-spec/SKILL.md`, `workflow/to-spec/GHERKIN.md` (PRODUCT 的 AC/BR 结构), `workflow/navigate/ACCEPTANCE-GUIDE.md` (逐项证据与人工确认边界), `workflow/explain-diff/SKILL.md` (证据缺口展示), `workflow/use-sandbox-worktree/reference/task-conditions.md` (只读与授权).
- 演练: 读 `~/.agents/skills/use-herdr/SKILL.md`, `launch.md`, `agent.md`, `PI.md`; 在临时项目 cwd 开新 pi 会话, 复制 `workflow/verify-change/` 到临时项目 `.agents/skills/verify-change/`, 用 `/skill:verify-change` 点名.

## TDD 切片

- TS-001:
  接缝: verify-change -> 产品输入与判据接口 (TECHNICAL.md 测试接缝 AC-001 行); 适配器为临时项目加真实 pi 会话.
  测试用例: TC-001.
  先写的失败测试: `drill-criteria-only-product` 在技能文件尚不存在时无法加载并执行; 建好后用含 2 个场景与 1 条审计 BR 的临时 PRODUCT.md, 另放 TECHNICAL.md 与勾选完毕的 EXECUTION.md, 让会话验收; 预期失败原因是没有技能时无法产出只按 Product 的逐项报告.
  最小绿色实现范围: SKILL.md 明确必需输入, 判据来源, 缺 PRODUCT.md 停止, 技术/执行材料只作线索, 计划勾选不改判产品失败.
  不得测试: SKILL.md 里是否出现某些词; 不测私有措辞.
  覆盖: AC-001.
- TS-002:
  接缝: 同上, 目标版本与证据输出接口 (TECHNICAL.md 测试接缝 AC-008 行).
  测试用例: TC-008.
  先写的失败测试: `drill-clean-commit-evidence-dir` 在未实现目标版本检查时, 脏工作区仍被当作验收目标, 且证据目录选择没有规则; 预期失败于脏工作区未被拒绝与结论未绑定提交.
  最小绿色实现范围: 开始前核对已提交且干净, 结论绑定起始提交; 证据默认写约定目录, 目录参与构建/测试发现/运行输入时外置; 不声称收尾整体干净.
  不得测试: 内部报告格式细节; 不测未确认的目录命名.
  覆盖: AC-008.

## 验证入口

- `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` 退出 0.
- 全角标点扫描: `rg -n "[\x{ff0c}\x{ff1b}\x{ff1a}\x{ff01}\x{ff1f}\x{3001}\x{ff08}\x{ff09}]" workflow/verify-change/SKILL.md` 无命中.
- 按 TS-001/TS-002 在临时 Git 项目跑真实会话, 把会话记录, 报告, 命令输出, 起始提交, 清理结果存入 `docs/changes/verification-skills/evidence/ISSUE-01/`; 通过标准: 逐项报告只取 Product, 缺 Product 停止, 计划勾选不改判失败, 脏工作区不开始, 结论绑定提交, 证据目录规则可观察.

## 风险提示

- 临时项目的 pi 信任提示可能需要在新会话内回答; 只对该临时路径授权并记录, 不改全局配置.
- PRODUCT.md 的已确认标记要按 `to-spec` 的实际格式构造, 不能用手写假标记冒充; 夹具中标注为演练输入.
- 本切片只支持单验收者, 不要把后续 issue 的行为提前写成空泛承诺.

## 停止条件

需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 加载不到声明文件或无法核对实际来源时停止并报告.

## 适合 AFK 的原因

输入, 判据, 目标版本和证据目录规则已由 Spec 固定, 演练只使用临时项目与临时会话, 无需产品/API/架构决策.

## 验收标准

- [ ] 缺少已确认 PRODUCT.md 时验收指挥者报告输入缺口并停止.
- [ ] 技术材料与计划勾选状态不进入产品通过条件.
- [ ] 报告逐项结果绑定起始提交, 脏工作区不被验收.
- [ ] 证据目录例外规则可观察, 不声称整体工作区仍干净.

## 被阻塞于

- 无.
