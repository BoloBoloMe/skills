# swt-e2e-revival Execution Spec (测试基础设施修复)

本改动不是产品需求, 是测试基础设施旧账: 2026-10-13 agent 模板机制进入 birth 流程 (提交 ae37426) 后, `tests/test_swt_m12.py` 的真容器 birth 用例就一直是红的 (该文件最后一次更新是 2026-09-20 的 3f71a75), 因为之后没人真跑过真容器. 已用 0e50ddd 基线对照证实与本轮 swt-container-env-docs 改动无关 (见 `../swt-container-env-docs/UNAUTHORIZED_DECISIONS.md` 的 UD-015).

目标: 让 m12 的真容器 birth 路径能在**完全本机、不碰用户真实资源**的环境里跑通, 并顺手把测试与宿主桌面解耦.

权威输入与依据:
- 仓库自定测试原则: `workflow/use-sandbox-worktree/reference/agent-templates.md` 第 88 行原话 "测试均用临时目录/假 Key/模拟 Podman/本机模拟网关. 真实容器验收单独审批..."
- 现有实现事实: `scripts/agent_config/template.py` (`TEMPLATES` 根, `load`/`choices`), `scripts/agent_config/runtime.py` (凭据与网关校验, 缺则 TemplateError 致命), `scripts/swt.py` (agent-template 决策闸, wayland 闸), `image/Containerfile` (M03 冒烟镜像), `tests/test_swt_m12.py` 与 `tests/conftest.py`.
- 用户裁决 (2026-10-14): 走"甲"路线 —— 假模板 + 临时假 Key + 本机假网关; 桌面那条用"假装没桌面"; 代码目录口径改文档.

## 全局允许范围

- `workflow/use-sandbox-worktree/scripts/agent_config/template.py` (模板根支持测试覆盖)
- `workflow/use-sandbox-worktree/agent-templates/` (可新增测试专用模板目录)
- `workflow/use-sandbox-worktree/image/Containerfile` (M03 冒烟镜像补契约标记与契约文件)
- `tests/conftest.py`, `tests/test_swt_m12.py`, `tests/run`, `tests/README.md` (夹具与入口)
- `tests/fixtures/` (可新增假模板/假网关夹具)
- `docs/language/UBIQUITOUS_LANGUAGE.md`, `docs/changes/swt-container-env-docs/DECISIONS.md` (仅 D008 条目 2 的措辞), `docs/changes/swt-container-env-docs/issues/ISSUE-02-env-docs-generator.md` (如其中的 ENV 条目 2 措辞需同步), `workflow/use-sandbox-worktree/agent-prompts/ENV.md` (条目 2 措辞)
- `tests/test_env_docs.py`, `tests/test_swt_stage_env.py` (若断言钉死了旧措辞)

## 全局禁止范围

- 不改 `scripts/swt.py` 的任何行为语义 (只允许 `agent_config/template.py` 的支持性小改)
- 不写用户真实资源: `~/.config/cliproxyapi/keys.json` 不得创建或修改; 不起真实 8317 网关; 不改宿主 wayland socket 权限
- 不碰 `~/.pi/`, `~/.agents/`, `/home/bolo/.pi`, `/home/bolo/.agents`
- 不删既有测试用例的断言意图; 不放宽断言让红变绿
- 不推远端

## 完成定义

- m12 真容器路径验收: `uv run --no-project python -m unittest tests.test_swt_m12 -v` 在本机跑通 (允许的例外: 只有确实依赖"宿主桌面直通真实存在"的用例可标环境不适用, 且必须逐条列出)
- 快层: `uv run --with pytest python -m pytest -m "not e2e" -q` 的失败集合不得比既有 8 项既有红更多
- 机检: `check-ac.py` 与 `check-tech.py` 对上一轮 spec 仍退出码 0

## 任务图

- ISSUE-01: `issues/ISSUE-01-test-template-harness.md`; 覆盖: 模板根测试覆盖 + 假模板 + 本机假网关 + M03 镜像契约; 依赖: 无
- ISSUE-02: `issues/ISSUE-02-m12-fixture-wiring.md`; 覆盖: m12 夹具接模板决策与假依赖 + 与宿主桌面解耦; 依赖: ISSUE-01
- ISSUE-03: `issues/ISSUE-03-doc-path-wording.md`; 覆盖: 容器代码目录口径改文档; 依赖: 无

## 全局风险和停止条件

- 需要改 `swt.py` 行为语义 (例如把 wayland 闸或模板闸改成自动放行) 时停止并报告
- 需要用户真实凭据/网关/宿主权限时停止并报告
- 出现 m12 用例断言失败且根因不在测试夹具面 (例如指向 swt.py 真 bug) 时, 记录并报告, 不擅自改产品代码

## 说明

本轮不出 PRODUCT/TECHNICAL 两份 spec: 它不是产品需求, 验收口径由上文"完成定义"+ 各 ISSUE 的验证入口给定, 依据来自仓库自定测试原则与用户裁决.
