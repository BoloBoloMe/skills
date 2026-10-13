# 跨机操作与 machine 命令

发现远端 ID, 执行远端操作或管理 SSH machine 配置前读取.

ID 和存活 agent 名只在单个 server 内有效. 两台已存 SSH machine 可以同时各有 `w1:p1`, 或各有名叫 `reviewer` 的 agent. 在 TUI 里选中一台 machine 不会改向你窗格里的命令: 不加 `--machine` 时, 命令仍使用继承的本机 session 和 socket 上下文.

若已安装的 CLI 支持 machine API 转发, 在每条远程命令前加同一个全局选项 `--machine <配置名或ID>`, 并先在远端重新发现 ID:

```bash
herdr --machine <配置名或ID> agent list
herdr --machine <配置名或ID> pane list
```

选项值须是已启用配置的 ID 或唯一且区分大小写的名称, 不是任意 SSH 主机名. 不与 `--session` 或 `--remote` 混用; 本机 ID 和 `--current` 不能用来指向远端窗格. 使用前核对本地与远端版本都支持转发, 且远端 server 已运行并兼容. 转发不会安装, 启动或重启远端 server, 也不会失败后退回本机; 本地配置, session 管理, 安装和交互式连接不经转发. 远端 worktree 路径须为绝对路径, `~` 或 `~/` 开头; plugin link 路径须为绝对路径. 若连接失败, 先检查远端状态再重试, 因为失败不代表远端变更没有生效. CLI 不支持转发时, 按其实际能力在远端 session 中操作并重新发现 ID.

`herdr machine list` 列的是已存连接配置, 不是跨机窗格清单; 脚本里加 `--json`. 仅在我要求时才增, 删, 启用, 停用配置. 删配置会断开 client, 但不停远程会话. 添加 machine 默认接远程 default session, 除非显式给 `--remote-session`. `herdr machine status [<配置名或ID>] --json` 可诊断连接; `herdr machine reconnect` 需要我在自己的终端完成 SSH 验证, 不要代我运行. setup 停掉不兼容 server 前会询问, 且默认 No; 未经我同意, 不得批准替换. 实验性 handoff 不属于 `machine add`.
