herdr 和 pi 组合使用的注意事项如下.

- 本机 pi 的提交键是 `alt+\`, 不是 `enter`; `agent prompt` 默认发的 enter 只把文本留在输入框. 提交改两步:
    1. `herdr pane send-text <pane-id> '<任务文本>' && herdr agent send-keys <短名> "alt+\\"`
    2. 行尾双反斜杠经 shell 转义, Herdr 收到的键名是 `alt+\`.
- `--wait` / `wait` 会误报 `agent_prompt_stalled` (pi 干完很快回 idle, 或快照滞后), 不等于文本没送达; 重发前先
  `agent read` 看屏幕, 免得任务提交两遍. 真实进度以最新 read 和仓库文件变化为准, 不以状态字段为准.
