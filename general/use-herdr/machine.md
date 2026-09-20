# 跨机操作与 machine 命令

ID 和存活 agent 名只在单个 server 内有效. 两台已存 SSH machine 可以同时各有 `w1:p1`, 或各有名叫 `reviewer` 的 agent. 在 TUI 里选中一台 machine 不会改向你窗格里的命令: 它们仍用继承的 session 和 socket 上下文. 远程控制命令要在目标主机上以其显式 session 运行, 并在那里重新发现 ID.

`herdr machine list` 列的是已存连接配置, 不是跨机窗格清单; 脚本里加 `--json`. 仅在我要求时才增, 删, 启用, 停用配置. 删配置会断开 client, 但不停远程会话. 添加 machine 默认接远程 default session, 除非显式给 `--remote-session`. setup 停掉不兼容 server 前会询问, 且默认 No; 未经我同意, 不得批准替换. 实验性 handoff 不属于 `machine add`.
