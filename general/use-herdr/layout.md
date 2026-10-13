# 终端布局与 server 会话

定位, 创建, 移动或关闭布局, 以及管理 server 会话前读取. 布局组织终端位置; pane 命令操作原始终端, agent 命令操作占据窗格的 coding agent. 窗格有无 agent 都存在.

## ID 与调用方上下文

公开 ID 是不透明的稳定句柄: workspace 如 `w1`, tab 如 `w1:t1`, pane 如 `w1:p1`. 已关闭的 tab/pane ID 不复用. 迁入另一 workspace 的窗格会得到新的 workspace 限定 ID.
`pane move` 后用 `.result.move_result.pane.pane_id` 或存活 agent 名继续操作. 旧值在 `.result.move_result.previous_pane_id`, 仅在该进程继承的调用方上下文里还能解析.
调用方上下文由 Herdr 注入; 以下示例用于本机当前会话, 远端先按 [machine.md](machine.md) 发现目标, 不沿用本机值:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
herdr workspace list
herdr tab list --workspace "$HERDR_WORKSPACE_ID"
herdr pane current --current
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
```

创建响应直接给出后续 ID: `workspace create` 返回 `.result.workspace`, `.result.tab`, `.result.root_pane`; `tab create` 返回 `.result.tab` 和 `.result.root_pane`; `pane split` 返回 `.result.pane`.
`--trust-repository` 仅授予单次请求的 Git 信任. 目标已确认是容器时可自行授权; 非容器或环境未确认时, 仅在我已验证仓库后使用, 不把它当作 worktree 失败后的常规重试手段.

## 兄弟窗格

我指定拆分方向就照做; 未指定时先看调用方布局:

```bash
herdr pane layout --pane "$HERDR_PANE_ID"
```

宽窗格向右拆, 窄或高的窗格向下拆; 避免同方向连拆造成不可用的窄列或矮行. 显式保留调用方 cwd:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

合适时把 `right` 换成 `down`, 从 `.result.pane.pane_id` 取新窗格 ID.

## 关闭与收尾

只关闭你创建的 workspace, tab, pane 或会话, 除非我明确要求关闭其他目标. `workspace close --group` 会关闭主 workspace 及其关联的 worktree workspace; 整个范围都须符合关闭授权, 不为绕过 `workspace_group_close_required` 而扩大范围.
你创建的会话在任务完成且结果已读走或交付给我后尽早关闭, 不必等我指示, 避免空闲 tab 埋掉活跃会话. 保留的情形:

- 我还要查阅: 结果我还没过目, 或我说过要看这个会话.
- 你明确知道后续要复用, 还会给同一会话追加任务.

拿不准是否保留时先问我. 其余独立 tab 用 `herdr tab close <tab ID>`, 兄弟窗格会话或跑完普通命令的窗格用 `herdr pane close <pane ID>` 尽早关闭.

## server 与隔离实验

仅在我明确要停掉 server 及其窗格进程时运行 `herdr server stop`, 不把它当活动会话内的常规恢复手段. 不 kill Herdr 主进程; 需要隔离 server 的实验使用命名测试会话.
