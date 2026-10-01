# /list-sandbox 沙盒容器清单与访问入口 Execution Spec

## 权威输入与决策引用

- Product Spec: `docs/changes/swt-list-sandbox/PRODUCT.md`
- Technical Spec: `docs/changes/swt-list-sandbox/TECHNICAL.md`
- 决策引用 (只读, 非意图来源): `docs/changes/swt-list-sandbox/DECISIONS.md`

## 全局允许范围

- `workflow/use-sandbox-worktree/scripts/swt.py`: 新增 `list` 只读子命令 (parse_args 注册 + 子命令实现), 不动其余子命令行为.
- `workflow/use-sandbox-worktree/pi-extension/`: 新增目录与 `index.ts`.
- `sync-to-pi.py`: 改造 `_merge_extensions` 为登记对账并新增 sidecar 维护.
- 测试: 新增 `tests/test_swt_list.py`, `tests/pi/list-sandbox.test.mjs`; 扩展 `tests/test_sync_to_pi.py`.
- 依据 TECHNICAL.md 模块划分末尾的模块/目录边界.

## 全局禁止范围

- 不可修改 birth/resume/status/terminate/display-check/enroll-device-key 的行为与输出契约 (NG-003).
- 不可实现跨设备聚合 (NG-001), 不可扩展 terminate 受理无记录容器 (NG-002), 不可清理 host 侧 worktree (NG-004), 访问入口不含风险声明与容器内路径契约 (NG-005).
- 不可在 pi 扩展内实现 podman/runtime 业务 (BR-010).
- 不改 LIST schema 已定字段的语义 (只加不改).
- 不修改 `pi/` 目录下其他扩展与 `docs/` 下 spec/账本 (账本只读引用).

## 完成定义

- `uv run --with pytest pytest -m "not e2e" -q tests/test_swt_list.py tests/test_sync_to_pi.py` 通过.
- `node tests/pi/list-sandbox.test.mjs` 通过.
- `tests/run --fast` 全仓快层通过 (收口回归).
- ISSUE-06 人工清单逐项勾选 (TUI 渲染 / 无 podman 环境 / BR-007 会话无注入).

## 测试策略

- AC 与 (审计) BR 对应类型与入口以 TECHNICAL.md 测试接缝映射表为唯一来源: 接缝 B (podman fake-run) -> `tests/test_swt_list.py`; 接缝 A (LIST 行字符串) -> `tests/pi/list-sandbox.test.mjs`; 接缝 D (tmp 目录 fixtures) -> `tests/test_sync_to_pi.py`; 接缝 C (pi 宿主) 无自动化替身, 归 ISSUE-06 人工.
- 每个 issue 至少一个可执行 TDD 切片; ISSUE-06 为人工验证特例 (非代码).

## 任务图

- ISSUE-01: `issues/ISSUE-01-list-skeleton.md`; 覆盖: AC-001 (数据面), AC-007, 非功能要求; 依赖: 无.
- ISSUE-02: `issues/ISSUE-02-running-entries.md`; 覆盖: AC-002 (组装面), AC-003, 安全策略 (LIST 无秘密值); 依赖: ISSUE-01.
- ISSUE-03: `issues/ISSUE-03-stopped-unmatched.md`; 覆盖: AC-004, AC-005; 依赖: ISSUE-01.
- ISSUE-04: `issues/ISSUE-04-pi-extension.md`; 覆盖: AC-001 (交互面), AC-002 (展示面), AC-006 (分路文案), BR-010, 安全策略 (print/json 走 stderr); 依赖: ISSUE-01.
- ISSUE-05: `issues/ISSUE-05-sync-reconcile.md`; 覆盖: AC-008, BR-008; 依赖: 无.
- ISSUE-06: `issues/ISSUE-06-integration-manual.md`; 覆盖: AC-006 (渲染面), BR-007, M2 超时降级; 依赖: ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04, ISSUE-05.

## 覆盖矩阵

- AC-001 -> ISSUE-01 (数据) + ISSUE-04 (交互) -> TC-001/TC-011 -> `uv run --with pytest pytest -q tests/test_swt_list.py` / `node tests/pi/list-sandbox.test.mjs`.
- AC-002 -> ISSUE-02 (组装) + ISSUE-04 (展示) -> TC-021/TC-012 -> 同上.
- AC-003 -> ISSUE-02 -> TC-022 -> `tests/test_swt_list.py`.
- AC-004 -> ISSUE-03 -> TC-031 -> `tests/test_swt_list.py`.
- AC-005 -> ISSUE-03 -> TC-032 -> `tests/test_swt_list.py`.
- AC-006 -> ISSUE-04 (分路) + ISSUE-06 (渲染) -> TC-041/TC-042 + 人工清单 -> `tests/pi/list-sandbox.test.mjs` / ISSUE-06 清单.
- AC-007 -> ISSUE-01 -> TC-001..TC-005 -> `tests/test_swt_list.py`.
- AC-008 -> ISSUE-05 -> TC-051 -> `tests/test_sync_to_pi.py`.
- BR-007 (审计) -> 人工验证: ISSUE-06 清单 — 代码审查扩展不调用 sendUserMessage/sendMessage, 真机执行 /list-sandbox 后会话文件无新增模型可见条目.
- BR-010 (审计) -> ISSUE-04 -> TC-043 (静态断言) -> `node tests/pi/list-sandbox.test.mjs`.
- 非功能要求 (TECHNICAL.md 非功能要求节: 子进程 ≤ 2+N) -> ISSUE-01 -> TC-004 -> `tests/test_swt_list.py` (fake-run 计数).
- 安全策略 (TECHNICAL.md 安全策略节) -> ISSUE-02 (LIST 无秘密值, TC-023) + ISSUE-04 (print/json 不写 stdout, TC-042) + 同级暴露陈述 (无需验证).

## 全局风险和停止条件

- 需要改变 PRODUCT/TECHNICAL/DECISIONS 时停止.
- 需要扩大允许范围 (如修改 SKILL.md/其他子命令/pi 目录) 或触碰禁止范围时停止.
- Spec 与代码事实冲突 (如 podman 输出形状与 fake 假设不符) 或无法提供完成证据时停止.
- swt.py 现有公共函数与 list 需求不匹配时, 优先复用; 确需改动共享函数签名时停止并上报.
