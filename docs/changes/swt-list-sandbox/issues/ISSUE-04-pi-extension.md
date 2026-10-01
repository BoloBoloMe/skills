## 父级

- `../EXECUTION.md`

## 执行

- [ ] 已实现

## 要构建什么

pi 扩展 `workflow/use-sandbox-worktree/pi-extension/index.ts` 全量: 注册 `/list-sandbox` 命令, 子进程 `uv run python <skillDir>/scripts/swt.py list` (skillDir 相对 `__dirname` 推导, 超时 120s), 解析 stdout 末行 `LIST ` 前缀 json; TUI 模式 `ctx.ui.select` (选项 = 容器名+podman-state+分支摘要) → 选中后 `ctx.ui.custom()` 滚动文本展示 `access-entries` (不进 LLM 上下文); rpc 模式 notify 摘要; print/json 模式 stderr 一行提示 (不写 stdout); 子进程超时/exit 4/stdout 无 LIST 行或解析失败按所在模式同路降级, exit 4 识别为无 podman 提示. 纯函数模块级导出: `parseListLine`/`buildSelectItems`/`modeRoutePlan`. 适合 AFK: 交互逻辑由纯函数与静态断言钉住, 宿主渲染归 ISSUE-06 人工.

## 覆盖依据

- Product: `docs/changes/swt-list-sandbox/PRODUCT.md`, AC-001 (交互面), AC-002 (展示面), AC-006 (分路文案)
- Technical: `docs/changes/swt-list-sandbox/TECHNICAL.md`, 模块接口 (M2), 测试接缝 (接缝 A/C), 安全策略 (print/json 走 stderr)

## 相关决策

- `docs/changes/swt-list-sandbox/DECISIONS.md`: D001, D004, D009, D010, D013

## 允许范围

- 新增 `workflow/use-sandbox-worktree/pi-extension/index.ts` (可附 `package.json` 若加载需要).
- 新增 `tests/pi/list-sandbox.test.mjs`.

## 禁止范围

- 扩展内实现任何 podman/runtime/入口组装业务 (BR-010: 唯一子进程是 swt.py list).
- 调用 sendUserMessage/sendMessage 注入会话.
- 修改 swt.py / sync-to-pi.py / 其他扩展 / `pi/` 目录.
- 改动 LIST schema.

## 代码定位提示

- 结构母本: `workflow/mailbox/pi-extension/index.ts` — `__dirname` 相对推导 skill 路径, spawn 形状, ExtensionAPI 类型导入 (`@earendil-works/pi-coding-agent`).
- pi 扩展 API 参考: `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/extensions.md` (registerCommand / ctx.ui.select / ctx.ui.custom / ctx.mode / ctx.hasUI).
- 测试形状母本: `tests/pi/repetition-guard.test.mjs` (node:test 直 import 扩展源文件测导出函数).

## TDD 切片

- TS-041:
  接缝: 接缝 A (LIST 行字符串), `tests/pi/list-sandbox.test.mjs`.
  测试用例: TC-041.
  先写的失败测试: `parseListLine 末行解析与容错` — 合法 stdout (人话行+末行 LIST json) 解析出对象; 末行非 LIST 前缀/非法 json 返回 null; `buildSelectItems` 对三容器 fixture 产出含名字/状态/分支摘要的选项.
  最小绿色实现范围: 三个纯函数.
  不得测试: TUI 渲染.
  覆盖: AC-001 (交互面数据), AC-002 (展示面数据).
- TS-042:
  接缝: 接缝 A, 同文件.
  测试用例: TC-042.
  先写的失败测试: `modeRoutePlan 四模式分路` — tui 计划含 select+custom 通道; rpc 计划含 notify 通道与摘要文案键; print/json 计划仅 stderr 通道且文案含裸数据命令 `uv run python <skill>/scripts/swt.py list`; 降级文案 (exit 4 / 解析失败 / 超时) 复用所在模式通道.
  最小绿色实现范围: 模式路由纯函数.
  不得测试: pi 宿主实际行为.
  覆盖: AC-006 (分路文案), 安全策略 (print/json 不写 stdout).
- TS-043:
  接缝: 接缝 A (静态断言), 同文件.
  测试用例: TC-043.
  先写的失败测试: `扩展源码静态断言` — 读 index.ts 源文本: 不含 podman 直调 (spawn 参数仅 swt.py list), 不含 sendUserMessage/sendMessage 调用; 实现前文件不存在, 失败.
  最小绿色实现范围: 源码符合纯连接器与无注入约束.
  不得测试: 超时真实行为 (归 ISSUE-06 人工).
  覆盖: BR-010, BR-007 (静态部分; 运行态部分归 ISSUE-06).

## 验证入口

- `node tests/pi/list-sandbox.test.mjs` 全绿.
- 可选真机冒烟: host pi 装载扩展后执行 `/list-sandbox` (依赖 ISSUE-05 登记或手工登记, 归 ISSUE-06 正式验证).

## 风险提示

- pi 装载 skill 目录内扩展的路径登记由 ISSUE-05 承接, 本切片不碰 settings.json.
- `ctx.ui.custom` 的组件 API 细节以 pi 当前版本文档为准, 纯函数先行可把宿主耦合压到最小.

## 停止条件

- 需要改变任一 Spec/决策/issue 边界, 或 pi API 与文档事实不符时停止.

## 适合 AFK 的原因

除宿主渲染外的全部逻辑有纯函数测试; 渲染风险显式移交 ISSUE-06 人工.

## 验收标准

- [ ] 纯函数三件套 + 容错 (TC-041).
- [ ] 四模式分路与降级文案 (TC-042).
- [ ] 静态断言: 无 podman 直调, 无会话注入 (TC-043).

## 被阻塞于

- ISSUE-01 (`issues/ISSUE-01-list-skeleton.md`)
