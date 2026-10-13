# pi 任务提交

提交前先读 [agent.md](agent.md) 的 `提交与等待`, 核对目标是否能接收任务; 本文件只补充 pi 差异.

本 skill 配套 pi 配置用 `alt+\` 提交, Enter 换行; 目标配置不同时用它实际生效的提交键. 实测 `agent prompt` 默认发的 Enter 只把任务留在输入框, 因此文本与提交键分两步发送:

```bash
herdr pane send-text <pane-id> '<任务文本>' && herdr agent send-keys <短名> "alt+\\"
```

行尾双反斜杠经 shell 转义, Herdr 收到的键名是 `alt+\`.

pi 完成很快, 状态快照也可能滞后; 判断实际进度时结合最新 `agent read` 和仓库文件变化, 不只看状态字段.
