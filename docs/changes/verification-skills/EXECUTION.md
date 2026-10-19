# 验证 skills 与独立产品验收 Execution Spec

## 权威输入与决策引用

- Product Spec: `docs/changes/verification-skills/PRODUCT.md`
- Technical Spec: `docs/changes/verification-skills/TECHNICAL.md`
- 决策引用 (只读, 非意图来源): `docs/changes/verification-skills/DECISIONS.md`

## 全局允许范围

- 新建 `workflow/verify-change/`, `workflow/create-verification-skill/`, `workflow/maintain-verification-skill/`, `workflow/blast-radius/`, `workflow/benchmark-checklist/`, 每个技能含 `SKILL.md`, 必要 `reference/*.md`, 必要辅助脚本与随附许可文件.
- 修改 `workflow/tdd-as-orchestra/SKILL.md` 的执行循环.
- 修改 `README.md` 的技能索引表.
- 新增 `docs/changes/verification-skills/evidence/**` 与 `docs/changes/verification-skills/issues/**`; 任务专用演练夹具放临时项目, 必须版本化时才放 `docs/changes/verification-skills/evidence/fixtures/**`.
- 行为演练可在 `/tmp` 或仓库外临时目录创建临时 Git 项目与临时会话; 不得写入任何共享生产资源.

## 全局禁止范围

- 禁止修改 `workflow/` 下除 `tdd-as-orchestra` 之外的既有技能, 以及 `general/` 下任何技能.
- 禁止修改 `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md`, ADR 与既有 Spec/TDD/双轴评审规则.
- 禁止写入 `~/.agents/`, `~/.pi/`, `/home/bolo/.agents`, `/home/bolo/.pi` 或任何全局部署副本; 禁止运行 `sync-to-pi.py`.
- 禁止在演练目标项目中修改产品代码, 项目配置或既有测试; 夹具项目只能在临时目录创建.
- 禁止新建统一 agent 运行器, 自动行为评测平台, 固定结果 JSON 协议或公共回放框架.
- 五个通用 skill 与生成的项目级 skill 自身不得提交/推送/开 PR/合并; 本变更执行流程仍按 tdd-as-orchestra 的既有本地提交与合并职责运行.
- 不触碰 PRODUCT.md 非目标 NG-001 至 NG-007.

## 完成定义

- 每个 issue 的 TC 均有 `docs/changes/verification-skills/evidence/ISSUE-<NN>/` 下的可读取原始材料与会话记录, 并与该 issue 验收标准逐条对应.
- 五个新增 `workflow/<skill>/SKILL.md` 均通过 `uv run python general/writing-for-llm/check_skill.py workflow/<skill>/SKILL.md`, 退出码 0; `name` 与目录一致, `description` 为单行人类摘要, `disable-model-invocation: true` 明确存在.
- 全部新增与修改的中文文档通过 translate-a-skill 的全角标点扫描, 无命中; 残留英文均有保留理由.
- 每个演练记录标明待测技能源文件与提交, 宿主与 pi 版本, 实际加载方式, 临时项目路径与目标提交; 不把源码演练结论扩大为全局部署已生效.
- `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` 通过; 全量快层 `uv run --with pytest python -m pytest -m "not e2e" -q` 不得比开工时记录的既有失败集合多.
- 最终差异只落在全局允许范围; `PRODUCT.md` 与 `TECHNICAL.md` 字节不变; 未运行同步或部署.
- `README.md` 索引包含五个新技能.

## 测试策略

- 行为验证的唯一来源是真实 agent 会话加临时项目公开入口, 不使用源码关键词断言代替行为结果; 静态检查只用于 frontmatter, 许可, 标点, 差异范围等机械审计.
- 每次演练先建临时 Git 项目并提交, 把待测技能源目录复制到该项目 `.agents/skills/<name>/`, 在项目 cwd 开新的 herdr/pi 会话, 通过 `/skill:<name>` 点名加载并提交任务; 生成的项目级配方则直接写入临时项目的 `.agents/skills/` 后由新会话按名加载. 会话操作按 `~/.agents/skills/use-herdr/SKILL.md`, `launch.md`, `agent.md`, `PI.md` 执行.
- 每个 AC 的全部场景大纲例子都要跑; 一次真实执行可承接多个已满足的断言, 不为每条 AC 重建环境. 固定数值, 权限不足或能力缺口可用明确标注的受控材料检验分支, 但关键正常路径必须真实运行.
- 证据固定记录: 待测源路径与提交, 宿主/pi 版本与加载方式, 临时项目路径与起始提交, 会话名与提交渠道, 实际命令/操作, 原始输出, 结论, 清理结果. 证据只存 `docs/changes/verification-skills/evidence/`, 不随临时项目删除.
- 演练夹具与证据整理可写任务专用脚本, 但脚本只准备场景或整理记录, 不得替真实会话决定或伪造行为结果.
- 除 ISSUE-15 外的 14 个 issue 均按垂直切片交付: 每个都走源文件, 公开加载, 真实行为, 可复核证据和机械检查的完整窄路径. ISSUE-15 是最终整合审计特例, 不新增运行时行为, 不计入垂直切片.
- 本变更是新增指令型 skill 加一处流程文档修改, 没有跨代码库的机械重命名或共享符号类型改动, 宽重构的扩展-收缩例外不适用.

## 任务图

- ISSUE-01: `issues/ISSUE-01-verify-change-criteria-target.md`; 覆盖: AC-001, AC-008; 依赖: 无.
- ISSUE-02: `issues/ISSUE-02-verify-change-coverage-evidence.md`; 覆盖: AC-002, AC-003; 依赖: ISSUE-01.
- ISSUE-03: `issues/ISSUE-03-verify-change-non-author-dispatch.md`; 覆盖: AC-004, AC-005; 依赖: ISSUE-02.
- ISSUE-04: `issues/ISSUE-04-verify-change-parallel-reverify.md`; 覆盖: AC-006, AC-007; 依赖: ISSUE-03.
- ISSUE-05: `issues/ISSUE-05-verify-change-applicability-recipes.md`; 覆盖: AC-009, AC-010; 依赖: ISSUE-04.
- ISSUE-06: `issues/ISSUE-06-benchmark-measurement.md`; 覆盖: AC-025, AC-026, AC-027; 依赖: 无.
- ISSUE-07: `issues/ISSUE-07-blast-radius.md`; 覆盖: AC-021, AC-022, AC-023, 自足历史与中文交接 (TC-107); 依赖: 无.
- ISSUE-08: `issues/ISSUE-08-benchmark-bounds-baseline.md`; 覆盖: AC-024, AC-030, AC-031; 依赖: ISSUE-07, ISSUE-06.
- ISSUE-09: `issues/ISSUE-09-benchmark-conclusions.md`; 覆盖: AC-028, AC-029; 依赖: ISSUE-08.
- ISSUE-10: `issues/ISSUE-10-verify-change-boundaries-methods.md`; 覆盖: AC-011, AC-012, AC-013; 依赖: ISSUE-05, ISSUE-07, ISSUE-06.
- ISSUE-11: `issues/ISSUE-11-create-verification-skill.md`; 覆盖: AC-016, AC-017, AC-018, 加载错误模式 (TC-104); 依赖: 无.
- ISSUE-12: `issues/ISSUE-12-maintain-verification-skill.md`; 覆盖: AC-019, AC-020; 依赖: 无.
- ISSUE-13: `issues/ISSUE-13-replica-provenance-license.md`; 覆盖: BR-010, 翻译行为保真 (TC-102, TC-108); 依赖: ISSUE-07, ISSUE-09.
- ISSUE-14: `issues/ISSUE-14-tdd-orchestra-acceptance-node.md`; 覆盖: AC-014, AC-015; 依赖: ISSUE-10.
- ISSUE-15: `issues/ISSUE-15-final-scope-audit.md`; 覆盖: AC-032, BR-009, BR-011, 安全策略 (TC-105), 演练记录边界 (TC-106); 依赖: ISSUE-11, ISSUE-12, ISSUE-13, ISSUE-14.

## 覆盖矩阵

- AC-001 -> ISSUE-01 -> TC-001 -> `evidence/ISSUE-01/` 判据与输入演练.
- AC-002 -> ISSUE-02 -> TC-002 -> `evidence/ISSUE-02/` 全量覆盖与审计规则演练.
- AC-003 -> ISSUE-02 -> TC-003 -> `evidence/ISSUE-02/` 证据标注与原始材料演练.
- AC-004 -> ISSUE-03 -> TC-004 -> `evidence/ISSUE-03/` 非作者委派演练.
- AC-005 -> ISSUE-03 -> TC-005 -> `evidence/ISSUE-03/` 场景组派工演练.
- AC-006 -> ISSUE-04 -> TC-006 -> `evidence/ISSUE-04/` 并行与证据共享演练.
- AC-007 -> ISSUE-04 -> TC-007 -> `evidence/ISSUE-04/` 修复后复验演练.
- AC-008 -> ISSUE-01 -> TC-008 -> `evidence/ISSUE-01/` 目标提交与证据目录演练.
- AC-009 -> ISSUE-05 -> TC-009 -> `evidence/ISSUE-05/` 旧证据适用性演练.
- AC-010 -> ISSUE-05 -> TC-010 -> `evidence/ISSUE-05/` 配方选择与过时配方演练.
- AC-011 -> ISSUE-10 -> TC-011 -> `evidence/ISSUE-10/` 写入授权与清理演练.
- AC-012 -> ISSUE-10 -> TC-012 -> `evidence/ISSUE-10/` 实现问题与缺口分类演练.
- AC-013 -> ISSUE-10 -> TC-013 -> `evidence/ISSUE-10/` 条件调用两项方法演练.
- AC-014 -> ISSUE-14 -> TC-014 -> `evidence/ISSUE-14/` 收尾前独立验收节点演练.
- AC-015 -> ISSUE-14 -> TC-015 -> `evidence/ISSUE-14/` 验收发现项回重构演练.
- AC-016 -> ISSUE-11 -> TC-016 -> `evidence/ISSUE-11/` 配方生成范围演练.
- AC-017 -> ISSUE-11 -> TC-017 -> `evidence/ISSUE-11/` 新会话实跑与按名加载演练.
- AC-018 -> ISSUE-11 -> TC-018 -> `evidence/ISSUE-11/` 生成物范围与构建受阻演练.
- AC-019 -> ISSUE-12 -> TC-019 -> `evidence/ISSUE-12/` 维护范围与漂移分类演练.
- AC-020 -> ISSUE-12 -> TC-020 -> `evidence/ISSUE-12/` 修订后新会话复跑演练.
- AC-021 -> ISSUE-07 -> TC-021 -> `evidence/ISSUE-07/` 关键安全事实证明演练.
- AC-022 -> ISSUE-07 -> TC-022 -> `evidence/ISSUE-07/` 风险与已排除项交接演练.
- AC-023 -> ISSUE-07 -> TC-023 -> `evidence/ISSUE-07/` 多模型同题调查演练.
- AC-024 -> ISSUE-08 -> TC-024 -> `evidence/ISSUE-08/` 一次性实验边界演练.
- AC-025 -> ISSUE-06 -> TC-025 -> `evidence/ISSUE-06/` 测量前主张与脚本检查演练.
- AC-026 -> ISSUE-06 -> TC-026 -> `evidence/ISSUE-06/` 公平配置与重复测量演练.
- AC-027 -> ISSUE-06 -> TC-027 -> `evidence/ISSUE-06/` 错误计数与真实工作演练.
- AC-028 -> ISSUE-09 -> TC-028 -> `evidence/ISSUE-09/` 粗估与异常处理演练.
- AC-029 -> ISSUE-09 -> TC-029 -> `evidence/ISSUE-09/` 结论与 PR 主数字演练.
- AC-030 -> ISSUE-08 -> TC-030 -> `evidence/ISSUE-08/` 收益上限与端到端演练.
- AC-031 -> ISSUE-08 -> TC-031 -> `evidence/ISSUE-08/` 基线与脚本固定前检查演练.
- AC-032 -> ISSUE-15 -> TC-032 -> `evidence/ISSUE-15/` 交付无 Git 动作审计.
- BR-009 (审计) -> ISSUE-15 -> TC-101 -> `check_skill.py` 全量结果与生成配方 frontmatter 证据.
- BR-010 (审计) -> ISSUE-13 -> TC-102 -> 两个复刻包的完整 MIT 文本, 固定 SHA 来源与逐项差异记录.
- BR-010 (审计) 翻译行为保真用例 -> ISSUE-13 -> TC-108 -> 两个复刻在临时项目的代表场景记录与差异记录对照.
- BR-011 (审计) -> ISSUE-15 -> TC-103 -> 最终差异范围与调用关系审计.
- 加载来源/同名冲突/未加载错误模式 (AC-017 额外用例, TECHNICAL 测试接缝) -> ISSUE-11 -> TC-104 -> `evidence/ISSUE-11/` 实际加载来源核对记录.
- 安全策略 (AC-011/AC-024 额外用例, TECHNICAL 安全策略) -> ISSUE-15 -> TC-105 -> 复核 ISSUE-10 与 ISSUE-08 的授权, 清理, 脱敏与冻结目标记录.
- 演练记录边界 (AC-003/AC-017 额外用例, TECHNICAL 测试接缝末段) -> ISSUE-15 -> TC-106 -> 核对每个演练记录区分源文件/宿主/临时项目, 未宣称全局部署生效.
- 自足历史定位与中文报告整理 (AC-021/AC-022 额外用例, TECHNICAL 模块接口 blast-radius) -> ISSUE-07 -> TC-107 -> `evidence/ISSUE-07/` 实际 Git 历史定位命令与交接报告.

## 全局风险和停止条件

- 需要改变 PRODUCT.md, TECHNICAL.md 或 DECISIONS.md 时停止.
- 需要扩大允许范围, 触碰禁止范围, 修改全局部署或运行同步时停止.
- 真实会话无法按目标运行时公开入口加载待测技能, 或实际来源无法核对时, 记录缺口并停止该条演练, 不改项目配置或全局部署绕过.
- 演练需要写入共享资源或取得新权限时停止并报告; 只允许临时项目与 `/tmp` 范围内的写入.
- 多模型能力不可用时按 AC-023-4 如实记录缺口, 不伪造多路调查.
- 证据无法支撑结论或清理残留未处理时停止并报告, 不把未验证项写成通过.
