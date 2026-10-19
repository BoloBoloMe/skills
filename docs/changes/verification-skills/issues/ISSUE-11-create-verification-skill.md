## 父级

- `../EXECUTION.md`

## 执行

- [x] 已实现

## 要构建什么

新增 `workflow/create-verification-skill/SKILL.md`: 配方生成者以已确认 PRODUCT.md 和项目事实为输入, 只为当前 Product 相关入口生成项目本地验证 skill, 含共用启动/实例检查/真实入口操作/取证/清理规则和功能地图; 交付前由未参与编写的新子会话按目标运行时公开加载入口实跑本次全部新增入口, 并把未验证缺口如实留下. 生成物只写项目本地验证目录及其辅助脚本, 不改产品代码/配置/既有测试. 交付后, 临时双入口项目能生成配方并由新会话跑过, 实际加载来源可核对.

## 覆盖依据

- Product: `../PRODUCT.md`, AC-016, AC-017, AC-018
- Technical: `../TECHNICAL.md`, 模块接口 (create-verification-skill), 接缝与适配器 (跨模块接缝三), 测试接缝 (AC-016/AC-017/AC-018 行, 加载错误模式)

## 相关决策

- `../DECISIONS.md`: D005, D006, D012, D017, D020, D022, D023, D036, D037

## 允许范围

- 新建 `workflow/create-verification-skill/SKILL.md`; 必要时新建 `workflow/create-verification-skill/reference/*.md` 与辅助脚本.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-11/`.
- 在临时项目内创建最小双入口应用 (一个 CLI, 一个网页/HTTP), 生成 `.agents/skills/verify-fixture/`, 可放同名旧副本做受控错误演练.

## 禁止范围

- 不修改产品代码, 项目配置, 既有测试或全局部署副本.
- 不生成与技术文档无关的整项目功能地图; 不调用 verify-change 形成第二层产品验收.
- 不修改既有技能, 三份权威输入.
- 不自动提交/推送/开 PR/合并.

## 代码定位提示

- 入口: `workflow/create-verification-skill/SKILL.md`, frontmatter 按 `general/writing-for-llm/SKILL.md` 与 `check_skill.py`.
- 必读: `../DECISIONS.md` F010/F011 的原始契约事实; `general/writing-for-llm/SKILL.md`; `workflow/use-sandbox-worktree/reference/task-conditions.md`; `~/.agents/skills/use-herdr/*`; pi 1.3.0 的 `docs/skills.md` (本地项目技能发现与 `/skill:name`).
- 演练: 临时项目 cwd 内开新 pi 会话, 生成配方后由另一名未参与编写的新会话按 `/skill:verify-fixture` 加载.

## TDD 切片

- TS-001:
  接缝: create-verification-skill -> 产品输入到本地配方生成接口 (TECHNICAL.md 测试接缝 AC-016 行); 适配器为仅 Product 与可观察运行事实, 另加未确认 Product 的临时项目.
  测试用例: TC-016.
  先写的失败测试: `drill-generate-scoped-recipe` 在技能不存在时无法生成项目配方; 建好后用 PRODUCT 涉及两个入口且项目还有未涉及功能的临时项目, 预期失败于未覆盖两个入口或铺开无关功能.
  最小绿色实现范围: 已确认 Product 是必需输入, 缺失时停止; 只生成相关入口和共用规则; 报告写明本次范围; 技术/执行文档可选, 不因缺少而阻塞.
  不得测试: 固定功能文件模板或固定英文节名; 不测未确认的目录命名.
  覆盖: AC-016.
- TS-002:
  接缝: create-verification-skill -> 交付前非作者配方证明接口 (TECHNICAL.md 测试接缝 AC-017 行); 适配器为两功能三入口及缺前置数据的项目, 真实子会话操作/取证/清理, 项目技能按名加载.
  测试用例: TC-017, TC-104.
  先写的失败测试: `drill-non-author-recipe-run` 在技能没有交付前实跑规则时, 生成者会自己粘贴正文或只跑一个入口; 预期失败于未由新子会话跑过全部入口或未证明按名加载的是项目当前文件.
  最小绿色实现范围: 新子会话跑过全部新改入口并留操作/取证/清理记录; 缺前置的配方标未验证; 不弱化步骤; 按 `/skill:verify-fixture` 核对实际 location 与展开正文; 同名冲突/未加载/来源不符时报告缺口.
  不得测试: 手工复制正文代替加载; 不测固定会话数.
  覆盖: AC-017; 加载错误模式.
- TS-003:
  接缝: create-verification-skill -> 源修改范围与构建受阻接口 (TECHNICAL.md 测试接缝 AC-018 行); 适配器为本地配方目录/产品源码/配置/既有测试的前后对照及子会话构建失败记录.
  测试用例: TC-018.
  先写的失败测试: `drill-recipe-scope-build-failure` 在技能没有范围限制时, 生成者可能改产品代码或配置让配方跑通; 预期失败于生成物越出验证目录.
  最小绿色实现范围: 只新增/修改项目本地验证目录及自有脚本; 应用无法构建时报告并只保留未验证配方; 子会话不改产品代码/配置/测试.
  不得测试: 具体构建系统; 不测未确认的辅助脚本实现.
  覆盖: AC-018.

## 验证入口

- `uv run python general/writing-for-llm/check_skill.py workflow/create-verification-skill/SKILL.md` 退出 0; 全角标点扫描无命中.
- 按 TS-001/TS-002/TS-003 在临时项目跑真实会话, 保存生成差异, 三入口运行记录, 加载 location, 同名冲突/缺口记录, 构建失败记录与清理结果到 `docs/changes/verification-skills/evidence/ISSUE-11/`; 通过标准: 范围只含相关入口, 三入口由新会话跑过, 加载来源是项目当前文件, 生成物不越界.

## 风险提示

- 项目本地加载受 pi 信任/过滤/同名冲突影响; 必须记录实际渠道与 location, 不能凭 `/skill:` 成功就认定用了新文件.
- 网页入口用临时本地端口, 不访问共享服务.
- 生成器可以把调查委派, 但最终实跑必须由未参与编写的新会话完成.

## 停止条件

需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 无法取得已确认 Product 或目标运行时加载条件不满足时, 记录缺口并停止.

## 适合 AFK 的原因

输入, 范围, 实跑角色和加载入口已由 Spec 固定; 演练只用临时项目与临时端口.

## 验收标准

- [ ] 只凭已确认 Product 和项目事实生成相关范围配方; 缺 Product 时停止.
- [ ] 新子会话跑过全部新改入口, 未实跑项如实保留.
- [ ] 项目技能按真实加载入口使用当前文件, 来源可核对; 加载缺口不掩盖.
- [ ] 生成物只落在项目本地验证目录, 构建失败不修产品.

## 被阻塞于

- 无.
