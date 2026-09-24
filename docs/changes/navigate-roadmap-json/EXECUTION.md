# navigate roadmap JSON 化 Execution Spec

## 权威输入与决策引用
- Product Spec: `docs/changes/navigate-roadmap-json/PRODUCT.md`
- Technical Spec: `docs/changes/navigate-roadmap-json/TECHNICAL.md`
- 决策引用 (只读, 非意图来源): `docs/changes/navigate-roadmap-json/DECISIONS.md`

## 全局允许范围
- `workflow/navigate/` 内: `scripts/` (roadmap.py, web_server.py), `web/` (index.html), `tests/`, `SKILL.md`, `TEMPLATES.md`
- `pytest.ini`: 仅追加 testpath `workflow/navigate/tests`

## 全局禁止范围
- 其他 skill 目录 (`general/`, `workflow/` 下非 navigate 项), 尤其不修改 present
- NG-001 不做旧格式迁移命令; NG-002 不做认证/TLS/网段隔离; NG-005 页面只读
- 不新增第三方依赖 (BR-006): python 仅 stdlib, 前端零外部引用
- JSON 不存展示信息 (NG-004)

## 完成定义
- `uv run pytest workflow/navigate/tests/ -q` 全绿, 全仓库既有测试不回归 (`uv run pytest -q` 快层)
- ISSUE-05/06 手动验收清单逐条通过 (用户肉眼核对)
- ISSUE-07 的 grep 检查与文档走查通过

## 测试策略
- AC 与审计 BR 对应的测试类型与入口见覆盖矩阵; 接缝与适配器以 TECHNICAL.md 测试接缝映射表为唯一来源
- 守门脚本: subprocess 调 CLI + tmp_path; 展示服务: 环境变量覆盖运行时目录 + 起真实实例 + loopback 真实 HTTP; SPA: 手动验收
- 并发保护不变量 (fcntl 锁 + 原子替换, TECHNICAL.md 模块接口): 不设自动化用例 — D015 测试范围未列并发用例, 以代码审查承接, 各 issue 风险提示中已标注锁范围要求
- 每个 issue 的 TDD 切片见各 issue; ISSUE-05/06 为人工验证特例 (NG-003), 无自动化切片并已标注理由

## 任务图
- ISSUE-01: `issues/ISSUE-01-gatekeeper-read-write.md`; 覆盖: AC-001, AC-005, AC-006, AC-007, BR-007; 依赖: 无
- ISSUE-02: `issues/ISSUE-02-gatekeeper-validation.md`; 覆盖: AC-002, AC-003, AC-004; 依赖: ISSUE-01
- ISSUE-03: `issues/ISSUE-03-web-server-lifecycle.md`; 覆盖: AC-008, AC-009, AC-010; 依赖: 无
- ISSUE-04: `issues/ISSUE-04-web-server-endpoints-idle-exit.md`; 覆盖: AC-011, AC-015 (数据侧), AC-016; 依赖: ISSUE-03
- ISSUE-05: `issues/ISSUE-05-spa-cosmos-render.md`; 覆盖: AC-012, AC-013, AC-014, AC-017, AC-018; 依赖: ISSUE-04
- ISSUE-06: `issues/ISSUE-06-spa-interaction-edges.md`; 覆盖: AC-015 (展示侧), AC-019; 依赖: ISSUE-05
- ISSUE-07: `issues/ISSUE-07-skill-docs-audit.md`; 覆盖: BR-006, 文档面 G-001/G-004; 依赖: ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04, ISSUE-05, ISSUE-06

并行机会: ISSUE-01 与 ISSUE-03 互不依赖可并行; ISSUE-02 依赖到达后 ISSUE-04 可与其并行.

## 覆盖矩阵
- AC-001 -> ISSUE-01 -> TC-001 -> `uv run pytest workflow/navigate/tests/`
- AC-002 -> ISSUE-02 -> TC-002 -> 同上
- AC-003 -> ISSUE-02 -> TC-003 -> 同上
- AC-004 -> ISSUE-02 -> TC-004, TC-104 (未知顶层字段), TC-105 (整文档兜底回滚) -> 同上
- AC-005 -> ISSUE-01 -> TC-005 -> 同上
- AC-006 -> ISSUE-01 -> TC-006 -> 同上
- AC-007 -> ISSUE-01 -> TC-007 -> 同上
- AC-008 -> ISSUE-03 -> TC-008 -> 同上
- AC-009 -> ISSUE-03 -> TC-009 -> 同上
- AC-010 -> ISSUE-03 -> TC-010 -> 同上
- AC-011 -> ISSUE-04 -> TC-011 -> 同上
- AC-012 -> ISSUE-05 -> 手动验收: 恒星/飞船/驶过渲染逐条核对 (ISSUE-05 验证入口)
- AC-013 -> ISSUE-05 -> 手动验收: 双飞船各自绕转
- AC-014 -> ISSUE-05 -> 手动验收: 抵达判定两分支 (未知海域空/非空)
- AC-015 -> ISSUE-04 (TC-015 数据侧: 端点错误形态) + ISSUE-06 (手动: 友好提示页)
- AC-016 -> ISSUE-04 -> TC-016 -> `uv run pytest workflow/navigate/tests/`
- AC-017 -> ISSUE-05 -> 手动验收: 改 status 后 ≤5s 页面更新
- AC-018 -> ISSUE-05 -> 手动验收: 五种恒星外观可区分
- AC-019 -> ISSUE-06 -> 手动验收: 详情面板字段齐备
- BR-006 (审计) -> ISSUE-07 -> TC-102 (import 仅 stdlib + index.html 零外部引用静态检查)
- BR-007 (审计) -> ISSUE-01 -> TC-101 (断言只写目标 .json, 无 .md, 无临时残留)
- 非功能要求 (空闲自退) -> ISSUE-04 -> TC-011 (缩短阈值触发同一代码路径)
- 非功能要求 (页面刷新延迟) -> ISSUE-05 -> 手动验收 (NG-003)
- 模块接口错误模式 (CLI 单行 JSON + 退出码) -> ISSUE-01 TC-001 起贯穿全部守门脚本/服务 TC

## 全局风险和停止条件
- 需要改变 PRODUCT/TECHNICAL/DECISIONS 时停止
- 需要扩大允许范围 (越出 workflow/navigate/ 与 pytest.ini 追加) 或触碰禁止范围时停止
- Spec 与代码事实冲突或无法提供完成证据时停止
- ISSUE-07 的 TC-102 若发现前序 issue 违反 BR-006: 停止, 不自行改前序产物, 上报
