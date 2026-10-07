# 安全与协调规则

[`use-herdr`](SKILL.md) 的按需参考: 每条控制命令都要遵守.

- 后台工作用 `--no-focus`, 除非我要求切换上下文.
- 用 `--current`, 显式窗格 ID 或唯一 agent 名. 不依赖别的 client 的聚焦窗格.
- 从 JSON 响应解析 ID 和状态. 不从侧栏顺序或示例推导.
- 不关闭不是你创建的工作空间, 标签页, 窗格或会话, 除非我明确要求. 你创建且已完成的会话按 `pane.md` 的 `清理已完成的会话` 尽早关闭. `workspace close --group` 会关掉主工作空间及其关联的 worktree 工作空间; 切勿只为绕过 `workspace_group_close_required` 而加它.
- `--trust-repository` 仅在我已验证仓库之后用. 它授予单次请求的 Git 信任, 不是 worktree 命令失败后的常规重试手段.
- 更新后 client 与 server 版本可能不一致. 依赖新 server 特性前先查 `herdr status`; 方法缺失时继续用已有方法完成任务.
- 切勿在活动会话内跑 `herdr server stop`, 除非我明确意图停掉 server 及其窗格进程.
- 切勿 kill Herdr 主进程. 需要隔离 server 的实验用命名测试会话.
- CLI 的 server 错误是 stderr 上的 JSON, 退出码 1; CLI 语法错误退出码 2.
