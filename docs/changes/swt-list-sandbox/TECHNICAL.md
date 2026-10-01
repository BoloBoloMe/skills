# /list-sandbox 沙盒容器清单与访问入口 Technical Spec

## 模块划分

- **M1 `list` 子命令** (新增, `workflow/use-sandbox-worktree/scripts/swt.py` 内): 责任 = 本 host 跨仓枚举带 label 容器, 判定双轴状态与 record-state, 现查端口, 枚举网卡并区分已确认/候选, 组装访问入口行 (含 reason 纪律), 输出 LIST 协议. 藏: podman 调用形状与 label 匹配, runtime 记录匹配/损坏区分, TUNNEL_INTERFACE_PREFIXES 过滤, 单容器采集失败的容错. 删除测试: 删掉它, 上述复杂度散回 pi 扩展的 TS 重实现与裸终端用户的手敲 podman — 复杂度不消失, 模块成立.
- **M2 `/list-sandbox` pi 扩展** (新增, `workflow/use-sandbox-worktree/pi-extension/index.ts`): 责任 = 子进程调用 M1, 解析 LIST 末行, 选择与展示交互, 四模式分路降级. 藏: pi ExtensionAPI 用法, 模式探测, LIST 解析容错. 刻意浅 (纯连接器, BR-010): 业务零实现; 删除它只损失 pi 内交互入口, 复杂度不散 — 它是 UI 适配器, 不是业务模块.
- **M3 扩展登记对账** (改造, `sync-to-pi.py`): 责任 = 扫描部署树的 `*/pi-extension` 目录, 对 settings.json extensions 数组做集合对账, 维护管理标记. 藏: 手工项与管理项的区分 (sidecar), 备份与原子写. 沿用现状的其余部分不重述.

模块/目录边界: `workflow/use-sandbox-worktree/scripts/swt.py` (list 子命令), `workflow/use-sandbox-worktree/pi-extension/index.ts` (新), `sync-to-pi.py`, 测试落 `tests/test_swt_list.py` 与 `tests/pi/list-sandbox.test.mjs` 与 `tests/test_sync_to_pi.py` (扩展).

## 模块接口

### M1 `list` 子命令

- 调用: `uv run python scripts/swt.py list [--records-root <PATH>]`. 无 `--repo` (跨仓枚举), `--records-root` 缺省 `~/.agents/sandbox-worktree/` (与生命周期子命令对齐).
- 输出: stdout 人话进度行, 末行 `LIST {...}` 单行 json; stderr 仅在 podman 整体不可用时首行 `ENV <人话>`, 原生报错透传.
- 退出码: 0 (含空清单, 含单容器采集失败) / 4 (podman 缺失或整体不可用). 不出现 1/2/3.
- LIST schema v1 (只加字段不改名):
  - 顶层: `schema` (int, 恒 1), `scope` `{records-root, completeness}`, `completeness` 恒 `"podman-all,records-root-one"`, `containers[]`, `warnings[]`.
  - 条目: `name`, `repo` (label 值), `branch`, `podman-state` (podman 状态字符串原样透传, 非闭集), `lifecycle` (active|retired|unknown), `record-state` (matched|missing|corrupt), `ports` `{ssh, vnc, web}` (int 或 null), `host-display` (ok|degraded|absent 或 null), `lans[]` `{addr, iface, kind}` (kind = confirmed|candidate, confirmed 排最前), `access-entries[]` (string, 组装好的展示行, 含 已确认/候选 标注与 reason 行), `collection-errors[]` (string).
- 不变量: 只读 — 不改 runtime 记录, 不动 nftables, 不持生命周期锁, 重复执行结果幂等; 非 running 容器的 `access-entries` 不含可达入口 (只含状态行与 resume 提示行); record-state 为 missing/corrupt 的条目含 `podman rm <名>` 指引行且不含 terminate 指引; 网卡枚举排除 TUNNEL_INTERFACE_PREFIXES 全集接口.
- 顺序约束: 无 (独立调用, 无前置).
- 错误模式: 单容器 inspect/port 失败或枚举期间消失 -> 该条目 `collection-errors` 记录, 整体仍 exit 0.
- 性能特征: N 容器 ≈ 2+N 次 podman 子进程 (1 次 ps 聚合 + 逐容器 inspect/port), 典型秒级, 无缓存.
- 必需配置: 无新增 (沿用 records-root 布局).

### M2 `/list-sandbox` pi 扩展

- 注册: `pi.registerCommand("list-sandbox", {description, handler})`; 无参数, 无补全.
- 行为按 `ctx.mode`/`ctx.hasUI` 分路: tui -> `ctx.ui.select` (选项 = 容器名 + podman-state + 分支摘要) -> 选中后 `ctx.ui.custom()` 滚动文本展示 `access-entries`; rpc -> `ctx.ui.notify` 摘要 (容器数 + 裸命令提示); print/json -> stderr 一行 "交互展示需 TUI/RPC 模式; 裸数据: uv run python <skill>/scripts/swt.py list" (不写 stdout, 不污染输出流).
- 子进程: `uv run python <skillDir>/scripts/swt.py list`, skillDir 由 `__dirname` 相对推导 (仿 mailbox 先例); 超时 120s.
- 错误模式: 子进程超时 / exit 4 / stdout 末行无 `LIST ` 前缀或 json 解析失败 -> 按所在模式降级为同一句提示 (tui/rpc 用 notify, print/json 用 stderr); exit 4 的 ENV 行识别为 "本环境无 podman, 仅 host pi 可用".
- 展示内容不调用 sendUserMessage/sendMessage (不进 LLM 上下文).
- 纯函数出口 (供测试, 模块级导出): `parseListLine(stdout)` (取末行解析, 失败返回 null), `buildSelectItems(listJson)`, `modeRoutePlan(mode)` (返回该模式应走的通知通道与文案键).
- 必需配置: 无 (部署路径即配置).

### M3 扩展登记对账 (sync-to-pi.py)

- 入口: 同步执行末尾调用, 扫描 `<skills_dir>/*/pi-extension` (目录存在即候选), 语义 = 集合对账.
- 管理标记: sidecar `<pi_dir>/extensions.synced.json` 记录 sync 管理过的路径集合.
- 不变量: 幂等; 当前扫描集新增登记; sidecar 中有而扫描集与 settings 均已消失的路径移除登记并移出 sidecar; 既不在 sidecar 又不在扫描集的 settings 项 (用户手工项) 永不增删; 写 settings.json 与 sidecar 前备份/原子写.
- 错误模式: settings.json 或 sidecar 不可解析 -> 打印告警跳过本步, 不中断其余同步计划.
- 必需配置: 沿用现有 pi 目录探测.

## 接缝与适配器

- 接缝 A (跨模块, M1↔M2): LIST 协议行 (stdout 末行). 生产侧适配器: swt.py list 的输出. 测试侧适配器: 固定 LIST 行字符串直接喂 `parseListLine` (`tests/pi/list-sandbox.test.mjs`). 依赖类别: 本地可替换 (子进程管道在测试中以字符串替换).
- 接缝 B (模块内部, M1 内部): podman 命令执行器. 生产侧适配器: 现有 `run()`/`podman_json()`. 测试侧适配器: fake-run 注入伪造 ps/inspect/port/ip 输出 (`tests/test_swt_list.py`, 仿 m08 fake 形状断言). 依赖类别: podman 本体为真正外部 (快层全 fake, 真跑归 e2e 层).
- 接缝 C (跨模块, M2↔pi 宿主): ExtensionAPI. 生产侧适配器: pi 进程装载 index.ts. 测试侧适配器: 无 — 宿主交互不做自动化替身, 仅测导出纯函数; 交互本体归手动验证. 依赖类别: 真正外部.
- 接缝 D (跨模块, M3↔文件系统): settings.json + extensions.synced.json. 生产侧适配器: 真实文件. 测试侧适配器: tmp 目录 fixtures (`tests/test_sync_to_pi.py` 既有模式). 依赖类别: 本地可替换.

## 测试接缝

- AC-001 -> M1 (枚举与条目构造) -> 接缝 B -> `tests/test_swt_list.py` (fake ps: 三容器双仓/空清单/目标已删); 选项构造 -> 接缝 A -> `tests/pi/list-sandbox.test.mjs` (`buildSelectItems`).
- AC-002 -> M1 (access-entries 组装与 reason 行) -> 接缝 B -> `tests/test_swt_list.py` (fake runtime 记录 + 端口, 断言行集).
- AC-003 -> M1 (lans 枚举/排序/排除) -> 接缝 B -> `tests/test_swt_list.py` (fake `ip addr` 含 wlan0/eth0/tailscale0, lan-address 文件在场/缺席).
- AC-004 -> M1 (非 running 分支) -> 接缝 B -> `tests/test_swt_list.py` (fake exited 容器, 断言无可达入口行与 resume 提示行).
- AC-005 -> M1 (record-state 分支) -> 接缝 B -> `tests/test_swt_list.py` (记录缺失/损坏 fixtures).
- AC-006 -> M2 (模式分路与文案) -> 接缝 A -> `tests/pi/list-sandbox.test.mjs` (`modeRoutePlan`/`parseListLine` 对 print/json/rpc 的计划断言); 交互渲染本体 -> 接缝 C -> 手动验证.
- AC-007 -> M1 (CLI 端到端形状与只读性) -> 接缝 B -> `tests/test_swt_list.py` (输出末行形状; fake runtime/nft 状态执行前后一致; 单容器采集失败 exit 0; podman 缺失 exit 4 + ENV 行).
- AC-008 -> M3 -> 接缝 D -> `tests/test_sync_to_pi.py` (登记新增/登记回收/手工项保留).
- BR-007 (审计) -> M2 -> 接缝 C -> 无自动化; 实现约束为不调用 sendUserMessage/sendMessage, 代码审查承接.
- BR-010 (审计) -> M2 -> 接缝 A -> `tests/pi/list-sandbox.test.mjs` 静态断言扩展源码不含 podman 子进程直调.

## 安全策略

- 访问入口含 ssh 密码 (既有公开约定, 固定 sandbox) 与私钥路径: 展示面为本机 pi 会话, 与 birth 交付同级暴露, 不新增泄露面; 私钥本体不读不出, 只展示路径.
- LIST json 不含秘密值: 凭证 env/密钥内容不进输出.
- print/json 模式不把入口行写 stdout (避免进管道与日志), 提示走 stderr.
- 无新认证/授权面; list 全程只读.

## 非功能要求

- M1 子进程调用次数上限: N 容器时 podman 子进程 ≤ 2+N (验证口径: 快层 fake-run 计数断言).

## 决策引用

- docs/changes/swt-list-sandbox/DECISIONS.md: D001, D002, D003, D004, D005, D006, D007, D008, D009, D010, D011, D012, D013
