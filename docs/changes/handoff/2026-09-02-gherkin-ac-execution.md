# 交接: Gherkin AC 形式化与 workflow 元词汇表 — 待执行

> 改名注解 (2026-09-02): 文中 `to-product-spec` 与 `to-technical-spec` 即现行 `to-spec` (`workflow/to-spec/`), `to-execution-spec` 即现行 `to-execution` (`workflow/to-execution/`); 决策见 `docs/changes/spec-skills-merge/DECISIONS.md`.

交接目的: 后续会话负责**执行落地**. 全部设计决策已关闭并固化于决策账本, 本文只补账本没有的信息.

## 执行上下文

- 权威依据是决策账本 (见必读推荐 1), 共 D001-D022 + F001-F010; 本文不重复其内容.
- 用户已授权: 执行可用子代理并行代工, 不急于单会话完成.
- 改动范围只涉及 markdown skill 文件与一个新 Python 脚本, 无代码库风险; 收尾必须 `uv run python sync-to-pi.py` 同步到真实 agent 目录 (仓库纪律见 AGENTS.md, 禁止直接改 ~/.agents).

## 账本未载的执行细节

1. **dogfood 写什**么 (D017 只说"试金石"): `docs/changes/gherkin-ac/PRODUCT.md` 的内容对象是**本变更自身** — 用新格式给"AC Gherkin 化 + 机检脚本"写产品 spec, 其 AC 围绕 check 脚本的可观察行为 (合法产物通过/非法产物报错) 与模板产物形态. 写完必须用 check-ac.py 自检通过.
2. **check-ac.py 实现要点**: 输入为 PRODUCT.md 路径; 从 `验收标准` 节提取唯一 ```gherkin fenced 块; 块首行已是 `# language: zh-CN` (D002), 可直接喂 parser; `gherkin-official` 的 Python API 精确用法未验证 (F003 仅证实 zh-CN 解析能力), 以包文档为准; 标签/覆盖/关键字白名单规则为自研逻辑, 规则源 = D003/D007/D008/D010.
3. **验证入口**: `uv run workflow/to-product-spec/check-ac.py docs/changes/gherkin-ac/PRODUCT.md` 退出码 0; 再跑 sync.
4. **词汇表盘点工作流** (D018): `workflow/` 下 19 个 skill 目录; 子代理分批扫描提候选词 → 汇总去重按收录标准过滤 → **定义须用户审过才落盘** WORKFLOW_VOCABULARY.md 与各 skill 接线 — 用户审是硬关卡, 禁止跳过.
5. **反方攻击报告无独立落盘**: 其结论已折入账本 (D001 排除项, D003/D010 的修正史), 无需寻找.
6. NB 承接行插入点: to-execution-spec/SKILL.md 的"起草完成标准"节 (现文为"每个 AC/TG/NFR 被至少一个拟议 issue 覆盖或明确说明无需执行任务"), 加 NB 维度.

## 路线图

1. **起点**: 用户接触到 Gherkin-style Acceptance Testing, 提出融入 workflow 的模糊意向.
2. **概念对齐**: 确认现有 PRODUCT/TECHNICAL 模板的 AC/TC 已是 GWT 散文句式, 形式化是顺水推舟; 划定边界 — 技术层 ROI 不成立, 范围锁定 PRODUCT 层, 产物保持 markdown.
3. **盘问对齐 (grilling, 2 轮 18 问)**: 用户中途注入四条元原则 (账本/spec 定位, 机械校验必须真脚本, 权威输入 spec 优先, 元词汇表需求) 与一条 skill 边界裁定 (deliberate 零改动), 全部收口.
4. **反方攻击 (opposing-viewpoint, glm-5.3 子代理)**: 三条反驳, 两条成立并转化为修正 (AC 基数 1:1→1..N; NB 审计断言补承接硬约束), 一条 (自研 lint 替代 Gherkin) 经评估驳回.
5. **决策固化**: `docs/changes/gherkin-ac/DECISIONS.md` 落盘 (本交接同时).
6. **当前位置**: 设计全关闭, 剩纯执行.

**剩余评估**: D022 清单 9 项. 单项最大的是词汇表全量盘点 (扫描+定义+用户审+19 skill 接线); 其余为小而确定的文件编辑. 预估执行无设计返工风险 — 所有"为什么"均可在账本回溯.

## 必读推荐

1. `docs/changes/gherkin-ac/DECISIONS.md` — 唯一权威依据; D022 是执行清单, 各决策 `预计影响` 节给出目标文件, `依赖事实` 给出理由源头. 执行前通读.
2. `workflow/to-product-spec/SKILL.md` — 被改对象现状 (模板/完成标准原文), 改动幅度最大.
3. `docs/changes/present-web-server/PRODUCT.md` — 旧格式唯一现存实例 (F004 证据现场), 改写模板与写 dogfood 时对照.
4. `workflow/domain-awareness/SKILL.md` 与 `workflow/domain-awareness/UBIQUITOUS_LANGUAGE_FORMAT.md` — 词汇表挂载点与格式范式 (D018).
5. `workflow/to-execution-spec/SKILL.md` — 仅"起草完成标准"节加 NB 一行 (D010), 其余不动.
