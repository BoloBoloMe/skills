# 布局, ID 与 agent 生命周期

[`use-herdr`](SKILL.md) 的按需参考: 驱动 agent 时才会用到这些定义.

## 原语

按任务选原语:
- 工作空间, 标签页, 窗格的拓扑组织终端位置.
- pane 命令管原始终端: shell, 测试, 服务器, 输入输出.
- agent 命令管当前占据该窗格的, 已识别的 coding agent.

窗格有无 agent 都存在. `agent start` 要求一个已存在的可用 shell 窗格, 绝不创建, 拆分或移动布局. 普通进程用 pane 命令. 需要 Herdr 校验 agent 身份, 或解释 `idle`/`working`/`blocked`/`done`/`unknown` 生命周期状态时, 用 agent 命令.

agent 命令只接受两类目标: 唯一的存活 agent 名, 或当前容纳该 agent 的窗格 ID. 不接受终端 ID 和裸 agent 种类标签. 名字须匹配 `[a-z][a-z0-9_-]{0,31}`, 且在存活 agent 中唯一. 名字跟随窗格当前 occupant; 该 agent 退出, 释放或替换后, 名字即清除.

## 生命周期状态

`idle` 和 `done` 都表示 agent 可接受输入. CLI/API 用 server 记录的 seen 标记区分二者: 显式 focus 命令把目标标为 seen, 读操作不标. `blocked` 表示 Herdr 识别到审批或提问 UI. `unknown` 表示有 agent 在场但 Herdr 无法可靠归类; 它不证明已完成.

## ID 与调用方上下文

公开 ID 是不透明的稳定句柄:
- workspace: `w1`
- tab: `w1:t1`
- pane: `w1:p1`

已关闭的 tab/pane ID 不复用. 迁入另一工作空间的窗格会得到新的工作空间限定 ID. `pane move` 之后, 用 `.result.move_result.pane.pane_id` 或存活 agent 名继续操作. 旧值报在 `.result.move_result.previous_pane_id`, 仅在该进程继承的调用方上下文里还能解析.

Herdr 向每个受管窗格注入调用方上下文:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
```

pane 命令要打调用方所在窗格时, 优先用 `--current`. 省略目标可能落到 UI 聚焦窗格, 而它可能属于我或另一个 client.

## 发现存活状态

```bash
herdr workspace list
herdr tab list --workspace "$HERDR_WORKSPACE_ID"
herdr pane current --current
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
herdr agent list
```

创建类响应直接给出下一步要用的 ID. `workspace create` 返回 `.result.workspace`, `.result.tab`, `.result.root_pane`. `tab create` 返回 `.result.tab` 和 `.result.root_pane`. `pane split` 把新窗格返在 `.result.pane`.
