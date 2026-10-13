# 创建 agent 会话

创建前读取. 与已有 agent 交互不需要重新选型或创建布局, 用 [agent.md](agent.md).

1. **选型**: 每次开新会话, 在创建 tab 和启动 agent 前完成选型, 因为它决定成本与任务质量.
   - 我未同时指定 model 与 thinking 时, 调用 `llm-select` skill, 保留我已指定的值并补齐缺项. 指定 pi/codex/kimi 只固定 kind, 不等于指定模型与思考深度.
   - kind 用我指定的; 未指定时按模型匹配: OpenAI -> codex, Kimi -> kimi, 其他/无匹配 -> pi.
   - 把 model/thinking 落实为目标 agent 支持的原生参数, 以它的 `--help` 为准. skill 或评分数据不可用时先报告并问我如何继续.
   完成标准: 说明选定的 model/thinking/kind, 所依据的任务画像列或我已完整指定, 并确定选型对应的原生参数.
2. **准备目标**: 创建/选择窗格前读 [layout.md](layout.md) 和 [agent.md](agent.md) 的 `权限与确认`, 以目标实际运行环境决定启动权限及对应参数.
   默认在调用方 workspace 的新 tab 中启动, tab 名为 `S-<子代理名>-<序号>`, 沿用当前 cwd, 直接使用 `tab create` 返回的 root pane. 兄弟窗格, 新 workspace, worktree 或更换 cwd 仅在我明确要求时使用.
   完成标准: 已取得目标窗格 ID, 目标符合主文件的空闲 shell 条件, 且启动权限符合目标环境的授权规则.
3. **启动**: 起一个表意且唯一的名字, 匹配 `[a-z][a-z0-9_-]{0,31}`. `agent start` 只在已有窗格启动 agent, 不创建, 拆分或移动布局. 原生 agent 参数只放在 `--` 之后, 首条任务另行提交, 避免把任务误当启动参数.
   `herdr agent` 可查看已装 kind 与选项. 启动成功表示 Herdr 在同一窗格探测到预期 agent 并认为它能接受输入, 默认超时 30 秒. 启动遇到 blocked 会立即返回 `agent_not_ready`, 名字仍可用于读屏和发送按键, 按 [agent.md](agent.md) 的 `交互失败恢复` 处理.
   完成标准: 所有启动确认已处理, `herdr agent get <名>` 报 `idle`.

`agent start` 的命令形态, kind 与参数须替换成选型结果:

```bash
herdr agent start reviewer --kind codex --pane <窗格ID> [-- <agent参数...>]
```

启动完成后, 首条任务和后续交互按 [agent.md](agent.md) 的提交与等待规则执行.
