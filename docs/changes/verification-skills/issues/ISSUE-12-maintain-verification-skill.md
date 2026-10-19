## 父级

- `../EXECUTION.md`

## 执行

- [x] 已实现

## 要构建什么

新增 `workflow/maintain-verification-skill/SKILL.md`: 配方维护者以当前已确认 PRODUCT.md 和目标项目为输入, 只核对当前 Product 相关功能, 区分文档漂移/驱动缺口/产品缺陷; 只修项目本地配方目录及自有脚本, 产品缺陷单独报告; 修改后由未参与编写的新子会话按项目真实加载入口复跑全部新改内容, 失败迭代的残留也清理并保留证据. 交付后, 临时项目中能看到范围内修正, 新会话复跑, 产品缺陷单列和局部结论边界.

## 覆盖依据

- Product: `../PRODUCT.md`, AC-019, AC-020
- Technical: `../TECHNICAL.md`, 模块接口 (maintain-verification-skill), 接缝与适配器 (跨模块接缝三), 测试接缝 (AC-019/AC-020 行)

## 相关决策

- `../DECISIONS.md`: D005, D006, D012, D017, D020, D022, D023, D036

## 允许范围

- 新建 `workflow/maintain-verification-skill/SKILL.md`; 必要时新建 `workflow/maintain-verification-skill/reference/*.md` 与辅助脚本.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-12/`.
- 临时项目内手工准备一份覆盖多历史功能的配方与一个真实产品缺陷.

## 禁止范围

- 不修改产品代码, 项目配置, 既有测试或全局部署副本.
- 不把局部维护说成整张历史地图或全项目已验证.
- 不调用 verify-change 增加产品验收层.
- 不修改既有技能, 三份权威输入.
- 不自动提交/推送/开 PR/合并.

## 代码定位提示

- 入口: `workflow/maintain-verification-skill/SKILL.md`, frontmatter 按 `writing-for-llm` 与 `check_skill.py`.
- 必读: `../DECISIONS.md` F011 的原始契约事实; `workflow/use-sandbox-worktree/reference/task-conditions.md`; `~/.agents/skills/use-herdr/*`; pi 1.3.0 `docs/skills.md`.
- 演练: 临时项目已有 `.agents/skills/verify-fixture/`; 配方含三条功能, 当前 Product 只涉及两条; 一条产品行为故意与 Product 不符.

## TDD 切片

- TS-001:
  接缝: maintain-verification-skill -> 范围识别与漂移分类接口 (TECHNICAL.md 测试接缝 AC-019 行); 适配器为当前 Product/历史地图/正确配方下的真实产品失败.
  测试用例: TC-019.
  先写的失败测试: `drill-maintain-scope-drift` 在技能不存在时无法修订; 建好后用只涉及两条功能的当前 Product, 预期失败于修改无关历史功能或把产品缺陷写成配方问题.
  最小绿色实现范围: 已确认 Product 是必需输入, 缺失时停止; 只改相关功能及共用规则; 区分文档漂移/驱动缺口/产品缺陷; 产品缺陷单列; 报告本次范围, 不扩大到整张地图.
  不得测试: 固定历史地图规模; 不测未确认的漂移分类算法.
  覆盖: AC-019.
- TS-002:
  接缝: maintain-verification-skill -> 配方修正后子会话证明接口 (TECHNICAL.md 测试接缝 AC-020 行); 适配器为新改配方/失败迭代/健康检查漂移, 实际子会话复跑及清理记录.
  测试用例: TC-020.
  先写的失败测试: `drill-maintain-non-author-rerun` 在技能没有交付前复跑规则时, 维护者会自己跑或只跑改动的方便入口; 预期失败于未由新子会话复跑全部新改内容或失败迭代残留未清.
  最小绿色实现范围: 新子会话按项目真实入口复跑全部新改配方及入口; 失败迭代残留清理; 健康检查漂移在配方范围内修正后重跑; 产品代码不改; 不再开 verify-change 层.
  不得测试: 固定会话数或固定重试次数; 不测未确认的清理工具.
  覆盖: AC-020.

## 验证入口

- `uv run python general/writing-for-llm/check_skill.py workflow/maintain-verification-skill/SKILL.md` 退出 0; 全角标点扫描无命中.
- 按 TS-001/TS-002 在临时项目跑真实会话, 保存修改前后差异, 范围说明, 产品缺陷报告, 新会话复跑记录, 失败迭代残留清理与证据到 `docs/changes/verification-skills/evidence/ISSUE-12/`; 通过标准: 只改相关配方, 产品缺陷单列, 新会话跑过全部新改内容, 残留清理且证据仍在, 结论不扩大到全项目.

## 风险提示

- 维护范围由当前 Product 决定, 不因配方文件里有更多功能就顺手修.
- 健康检查自身漂移与产品回归要分清; 前者修配方, 后者单独报告.

## 停止条件

需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 无已确认 Product 或缺权限/目标时记录缺口并停止.

## 适合 AFK 的原因

输入, 范围, 漂移分类和复跑角色已由 Spec 固定; 演练只用临时项目与临时会话.

## 验收标准

- [ ] 维护只覆盖当前 Product 相关功能及必要共用规则.
- [ ] 文档漂移, 驱动缺口与产品缺陷分开, 产品缺陷单独报告.
- [ ] 新子会话复跑全部新改配方及入口, 失败迭代残留清理.
- [ ] 报告明确本次范围, 不声称整张历史地图或全项目已验证.

## 被阻塞于

- 无.
