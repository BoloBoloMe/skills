---
name: herdr
description: "操作 Herdr (agent 终端工作区). 仅当我明确提到 Herdr, 或要求用 Herdr 查看/控制 工作空间/workspace, 标签页/tab, 窗格/pane, 命令或另一个 agent 时才用; 任务只是能受益于后台终端, 委派或并行时不用. 需 HERDR_ENV=1. 帮我学习/安装/排查 Herdr 时改用 https://herdr.dev/agent-guide.md (它教人, 本 skill 管操作)."
---

# herdr

Herdr 把终端组织成 工作空间/workspace, 标签页/tab, 窗格/pane, 能识别窗格内运行的 coding agent, 并通过 `herdr` CLI 暴露当前会话.

先分派任务:
- 你亲自操作 Herdr → 用本 skill, 从下面的环境检查开始.
- 帮我学习, 安装或排查 Herdr → 读 https://herdr.dev/agent-guide.md 并按它回答. 它面向教人, 本 skill 的操作规则不适用.

## 环境检查

发任何控制命令前, 先验证你运行在 Herdr 管理的窗格内:

```bash
test "${HERDR_ENV:-}" = 1
```

检查失败: 声明你不在 Herdr 内运行, 然后停止. 切勿在 Herdr 之外查看或控制聚焦中的 Herdr 会话.

检查通过后, PATH 里的 `herdr` 二进制即连接当前会话. 用它查看邻近工作, 建终端布局, 启动 agent 和命令, 读输出, 等待状态变化.

## 学习当前 CLI

已装二进制是命令语法的权威. 先跑:

```bash
herdr --help
```

再打印相关命令组 (不带子命令运行该组):

```bash
herdr agent
herdr pane
herdr workspace
herdr tab
herdr worktree
herdr terminal
herdr notification
herdr integration
herdr session
herdr machine
```

切勿跑裸 `herdr` 做探索: 它会启动或附着 TUI. 切勿用省略参数的方式探测会改状态的嵌套命令: `herdr workspace create` 这类命令带默认值即成立, 会直接执行.

多数控制命令返回 JSON. 从响应里读标识符和状态, 不靠预测.

## 理解布局, 窗格与 agent

按任务选原语:
- 工作空间, 标签页, 窗格的拓扑组织终端位置.
- pane 命令管原始终端: shell, 测试, 服务器, 输入输出.
- agent 命令管当前占据该窗格的, 已识别的 coding agent.

窗格有无 agent 都存在. `agent start` 要求一个已存在的可用 shell 窗格, 绝不创建, 拆分或移动布局. 普通进程用 pane 命令. 需要 Herdr 校验 agent 身份, 或解释 `idle`/`working`/`blocked`/`done`/`unknown` 生命周期状态时, 用 agent 命令.

agent 命令只接受两类目标: 唯一的存活 agent 名, 或当前容纳该 agent 的窗格 ID. 不接受终端 ID 和裸 agent 种类标签. 名字须匹配 `[a-z][a-z0-9_-]{0,31}`, 且在存活 agent 中唯一. 名字跟随窗格当前 occupant; 该 agent 退出, 释放或替换后, 名字即清除.

`idle` 和 `done` 都表示 agent 可接受输入. CLI/API 用 server 记录的 seen 标记区分二者: 显式 focus 命令把目标标为 seen, 读操作不标. 每个 TUI client 各自记录已看过的完成, 所以它的 Done 徽章可与 CLI 或另一 client 不一致. `blocked` 表示 Herdr 识别到审批或提问 UI. `unknown` 表示有 agent 在场但 Herdr 无法可靠归类; 它不证明已完成.

## 用 ID 和调用方上下文

公开 ID 是不透明的稳定句柄:
- workspace: `w1`
- tab: `w1:t1`
- pane: `w1:p1`

已关闭的 tab/pane ID 不复用. 迁入另一工作空间的窗格会得到新的工作空间限定 ID. `pane move` 之后, 用 `.result.move_result.pane.pane_id` 或存活 agent 名继续操作. 旧值报在 `.result.move_result.previous_pane_id`; 旧 ID 仅在该进程继承的调用方上下文里还能解析, 切勿拿它当通用 agent 目标.

Herdr 向每个受管窗格注入调用方上下文:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
```

pane 命令要打调用方所在窗格时, 优先用 `--current`. 省略目标可能落到 UI 聚焦窗格, 而它可能属于我或另一个 client.

发现存活状态:

```bash
herdr workspace list
herdr tab list --workspace "$HERDR_WORKSPACE_ID"
herdr pane current --current
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
herdr agent list
```

创建类响应直接给出下一步要用的 ID. `workspace create` 返回 `.result.workspace`, `.result.tab`, `.result.root_pane`. `tab create` 返回 `.result.tab` 和 `.result.root_pane`. `pane split` 把新窗格返在 `.result.pane`.

ID 和存活 agent 名只在单个 server 内有效. 两台已存 SSH machine 可以同时各有 `w1:p1`, 或各有名叫 `reviewer` 的 agent. 在 TUI 里选中一台 machine 不会改向你窗格里的命令: 它们仍用继承的 session 和 socket 上下文. 远程控制命令要在目标主机上以其显式 session 运行, 并在那里重新发现 ID.

`herdr machine list` 列的是已存连接配置, 不是跨机窗格清单; 脚本里加 `--json`. 仅在我要求时才增, 删, 启用, 停用配置. 删配置会断开 client, 但不停远程会话. 添加 machine 默认接远程 default session, 除非显式给 `--remote-session`. setup 停掉不兼容 server 前会询问, 且默认 No; 未经我同意, 不得批准替换. 实验性 handoff 不属于 `machine add`.

## 启动并协调 agent

默认在当前标签页开兄弟窗格, 沿用当前工作目录. 只有我明确要求相应拓扑或位置时, 才新建工作空间, 标签页, worktree 或更换 cwd.

我指定了拆分方向就照做. 没指定就先看调用方窗格:

```bash
herdr pane layout --pane "$HERDR_PANE_ID"
```

宽窗格向右拆, 窄或高的窗格向下拆. 避免同方向连拆: 会造出不可用的窄列或矮行. 让我的焦点留在调用方窗格, 并显式保留调用方工作目录:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

合适时把 `right` 换成 `down`. 从 `.result.pane.pane_id` 读新窗格 ID.

可用 shell 窗格的标准: 停在交互提示符上, shell 自身在前台, 没有前台命令, 编辑器或 agent 在跑. 在该窗格启动受支持的 agent, 起一个表意且唯一的名字:

```bash
herdr agent start reviewer --kind codex --pane <返回的窗格ID>
```

kind 用我指定的. 跑 `herdr agent` 查看已装 kind 列表和选项. 原生 agent 参数只放在 `--` 之后:

```bash
herdr agent start reviewer --kind codex --pane <返回的窗格ID> -- <agent参数...>
```

`agent start` 成功的返回条件: Herdr 在同一窗格探测到预期 agent, 且认为它可接受交互输入. 启动期间 agent 若进入 blocked, 命令立即返回 `agent_not_ready`, 但该名字仍可用于 `agent read` 和 `agent send-keys`. 等 agent 变 idle 再发任务. 启动默认 30 秒超时.

通过 agent 界面提交工作:

```bash
herdr agent prompt reviewer "review 当前 diff, 只报告需要动手的发现" --wait --timeout 120000
```

`agent prompt` 尊重窗格实时的 bracketed-paste 模式, 把文本和随后的编码 Enter 作为一次有序提交发出. 两者都写完才报告提交成功; 仅此不证明 agent 已开始一轮. Windows 上 Codex 的提交延迟随 prompt 体积增长. 目标 agent 正停在审批或提问对话框时, 它在发出任何输入前就以 `agent_blocked` 拒绝. 此时先查看 blocked UI, 问过我之后再代答. 普通 agent 工作用 `--wait` 即可: 它等第一个 settled 的 `idle`/`done`/`blocked`. 别用 `--until` 重复这些默认值.

带 `--wait` 时, 从非 working 态发出的 prompt 必须产生可观测的 `working` 或 `blocked` 活动. 提交后 Herdr 最多等 5 秒等这个活动; 无关的 `idle`/`done` 或会话变化不满足这个闸门. 观测不到活动返回 `agent_prompt_stalled`; 你的超时先到则返回 `timeout`. 该超时含提交耗时. 不给超时时, 观测到活动后的 settled 等待无限期. 这个等待跟踪生命周期状态, 不是单个 turn; agent 本就在工作时, 当前 turn 的完成即可满足它.

仅在需要特定状态的流程里用 `--until`, 例如等一个运行中的 agent 来要输入:

```bash
herdr agent wait reviewer --until blocked --timeout 120000
```

不带 `--until` 时, 单独的 `agent wait` 与 `agent prompt --wait` 用同一套 settled 默认值.

交互式 agent UI 控制用逻辑键:

```bash
herdr agent send-keys reviewer esc
herdr agent send-keys reviewer ctrl+c
```

Herdr 先校验全部按键, 再写入任何字节. 通过解析后的 agent 读结果:

```bash
herdr agent get reviewer
herdr agent read reviewer --source recent-unwrapped --lines 120
```

等待失败或返回 `blocked` 时, 先看 `agent get` 和 `agent read`, 再决定发什么输入. 超时或 stalled 不证明 prompt 没送达; 切勿盲目重发. 仅在确需原始终端控制时才用 pane 界面.

## 在另一窗格跑普通命令

按同一几何规则开兄弟窗格, 保留调用方工作目录, 不动我的焦点:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

从 `.result.pane.pane_id` 读新窗格 ID, 然后运行并查看:

```bash
herdr pane run <返回的窗格ID> "just test"
herdr pane wait-output <返回的窗格ID> --match "test result" --timeout 120000
herdr pane read <返回的窗格ID> --source recent-unwrapped --lines 120
```

`pane run` 把命令文本和 Enter 原子发出. `pane wait-output` 立即搜索所选快照, 已存在的输出也能命中. `--match <文本>` 匹配字面子串, `--regex <模式>` 用 Rust 正则. 省略 `--timeout` 即无限期等待.

按任务选 read source:
- `visible`: 当前渲染的视口.
- `recent`: 最近渲染的输出, 含软换行.
- `recent-unwrapped`: 接回软换行的最近输出; 日志和转录优先用它.
- `detection`: 供 agent 探测用的纯文本底缓冲快照.

颜色和终端样式可作证据时加 `--format ansi`, 否则用纯文本.

`--lines` 向 Herdr 索要更多行, 取自窗格可用屏幕和宿主 scrollback. 调大它仍看不到某条已完成响应的更多内容, 该窗格很可能在 alternate screen 里跑 agent. 离开 alternate screen 的行不进 Herdr 的宿主 scrollback, 加大行数找不回它们.

读取失败后, 让该 agent 把完整响应写成临时目录里的 Markdown 文件, 只回文件路径, 你再直接读文件. 此法仅作兜底; 首次 prompt 不要就要求文件输出.

## 安全与协调规则

- 后台工作用 `--no-focus`, 除非我要求切换上下文.
- 用 `--current`, 显式窗格 ID 或唯一 agent 名. 不依赖别的 client 的聚焦窗格.
- 从 JSON 响应解析 ID. 不从侧栏顺序或示例推导.
- 不关闭不是你创建的工作空间, 标签页, 窗格或会话, 除非我明确要求. `workspace close --group` 会关掉主工作空间及其关联的 worktree 工作空间; 切勿只为绕过 `workspace_group_close_required` 而加它.
- `--trust-repository` 仅在我已验证仓库之后用. 它授予单次请求的 Git 信任, 不是 worktree 命令失败后的常规重试手段.
- 更新后 client 与 server 版本可能不一致. 依赖新 server 特性前先查 `herdr status`. 缺少某个方法不构成停止或升级 server 的许可.
- 切勿在活动会话内跑 `herdr server stop`, 除非我明确意图停掉 server 及其窗格进程.
- 切勿 kill Herdr 主进程. 需要隔离 server 的实验用命名测试会话.
- CLI 的 server 错误是 stderr 上的 JSON, 退出码 1; CLI 语法错误退出码 2.
