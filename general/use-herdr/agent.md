# 驱动已有 agent

查看, 提交, 等待或恢复交互前读取. 创建会话的选型和布局规则在 [launch.md](launch.md).

## 目标, 状态与读取

agent 命令的目标只能是唯一存活 agent 名, 或当前容纳它的窗格 ID, 不接受终端 ID 或裸 kind. 名字跟随窗格当前 occupant; agent 退出, 释放或替换后名字即清除. 用 `herdr agent list` 发现存活 agent, `agent get <名或窗格ID>` 查状态.
`idle` 和 `done` 都表示 agent 可接受输入. CLI/API 用 server 记录的 seen 标记区分二者: 显式 focus 命令把目标标为 seen, 读操作不标. 各 TUI client 另行记录自己看过的完成状态, 所以 Done 标记可能与 CLI 或其他 client 不同. `blocked` 表示 Herdr 识别到审批或提问 UI. `unknown` 表示有 agent 在场但 Herdr 无法可靠归类; 它不证明已完成.
读取输出前读 [pane.md](pane.md) 的 `读取输出`, 按其中的 source 规则使用 `agent read`. `agent_not_idle` 表示 agent 正在工作, 不是故障, 改用 `pane read` 或等待. 输出不完整也按该文件兜底, 不能把读不到当成没有产物.

## 权限与确认

以目标 agent 的实际运行环境为准, 由你检查判断, 不把调用方环境当作目标环境:
- 容器内: 我已授权你无限制启动和驱动 agent, 用它支持的最宽权限和免审批模式, 不拦截 LLM 的任何操作. 仓库/目录信任, 启动警告, 工具/命令审批直接自行确认, 包括 Codex 启动信任页, 不必再问我或等我手动操作.
- 非容器或环境未确认: 不特地放宽权限, 授权/信任确认先问我再代答.

授权确认与任务决策不同: 需要我决定的任务提问仍问我.

## 提交与等待

先处理阻塞和启动确认, 再提交任务. 向 pi 提交前必须读 [PI.md](PI.md), 其他 agent 用:

```bash
herdr agent prompt reviewer "<任务文本>" --wait --timeout 120000
```

`agent prompt` 尊重实时 bracketed-paste 模式, 把文本和编码 Enter 一次有序发出, 两者写完才报告提交成功. 审批或提问对话框中, 它在发送任何输入前返回 `agent_blocked`, 按下面的恢复规则处理.
普通工作用 `--wait`, 等第一个稳定的 `idle`/`done`/`blocked`. 不带 `--until` 的 `agent wait` 使用相同默认值; 仅在需要特定状态时用 `--until`, 如 `agent wait reviewer --until blocked --timeout 120000`.
从非 working 态发出的 prompt 带 `--wait` 时, 必须观测到 `working` 或 `blocked` 活动. Herdr 最多等 5 秒, 无关的 idle/done 或会话变化不满足这个条件; 观测不到返回 `agent_prompt_stalled`, 你的超时先到则返回 `timeout`. 超时包括提交耗时, 不设超时时, 活动之后的稳定状态等待无限期. 等待跟踪生命周期而非单个 turn; agent 已在工作时, 当前 turn 完成即可满足它.

## 交互失败恢复

`agent_not_ready`, `agent_blocked` 或状态 `blocked`: 用 `agent read` 看实际 UI, 读不到就用 `pane read`. 按 `权限与确认` 处理授权页, 用 `agent send-keys` 按实际选项确认后再读屏, 连续确认页逐一处理. 提问先取得我的决定. 启动完成才提交首条任务; 已提交的任务在确认后继续等待, 不重复提交, 不因确认页重建会话.
`agent_prompt_stalled` 或超时不证明任务未送达. 先用 `agent get` 和读屏核实:
- blocked: 先处理确认或提问, 即使任务已送达也不能只等待.
- 任务已送达或 agent 仍在工作: 继续等待, 不重建.
- agent 或窗格已消失: 才允许重建或重开.

`agent wait` 报 `agent_not_found` 时改用窗格 ID, 不重试同名. 重发前先读屏核实, 避免提交两遍.
交互按键用 `agent send-keys <目标> esc` 或 `ctrl+c` 这类逻辑键; Herdr 先校验全部按键再写入任何字节.

## 结果与收尾

结果读取按上面的输出规则执行. 你创建的会话任务完成且结果已取回或交付给我后, 必须读 [layout.md](layout.md) 的 `关闭与收尾` 判断是否应关闭; 需要保留或复用的按该节处理. 完成标准: 结果已取回或交付, 你创建的会话已关闭或已确认保留理由.
