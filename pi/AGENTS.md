回复和文档用中文, 非译项除外.
信道按字符计费, 成本高昂. 回复电报文: 只输出有效载荷. 遇多步推理/风险分析, 可放宽压缩, 保留完整推理链. **只压缩回复, 不省略思考**.
用我能直接看懂的大白话写; 省字符靠删句子, 不靠生僻术语/缩写/代号; 非译项, 命令, 标识符除外, 非用不可的术语当场一句白话解释.
标点一律半角 ASCII, 禁用全角 (尤其 U+3001). 普通并列用 `,`, 短选项或紧密组合用 `/`, 长并列分行.
运行 Python 脚本/模块用 `uv run python`, 添加依赖用 `uv add`, 禁止直接使用 `python`/`pip`.
需要了解当前环境时, 读 `~/AGENTS.md`; 不存在就跳过.
当被要求调用某个不在列表中的 skill 时, 读 `~/.agents/skills/<skill-name>/SKILL.md`; 文件不存在就报告未找到, 不要搜索其他位置.
当被要求使用子代理/subagent 时, 用 herdr 开新会话 (用法读 `herdr --skill` 输出); 新会话放新标签页, 标签名 `S::<子代理名>::<序号>`.
注意事项:
- pi 的 tui.input.submit 不是 `enter` 是 `alt+\`
- 如果子代理会话使用 pi 作为 agent, 那么这个 pi 会话也要指定名称, 和标签名相同.

## Herdr/pi 协作踩坑

- 控制 Herdr 前先确认 `test "${HERDR_ENV:-}" = 1`. 不在 Herdr 管理的 pane 中时不要调用控制命令.
- 子代理要放进新标签页时, 用 `herdr tab create --label 'S::<子代理名>::<序号>' --no-focus`, 读取返回的 `root_pane.pane_id`; 不要按标签编号猜 pane ID.
- Herdr 的 agent 名有字符限制, 不能直接使用带 `:` 的标签名. 用短的唯一名作 Herdr target, 同时把完整标签名传给 pi 的原生参数, 例如:
  `herdr agent start milestone-04-1 --kind pi --pane <pane-id> -- --name 'S::MILESTONE-04::1'`
  `--` 后不要再写一个 `pi`, 因为 Herdr 已经会启动 pi; 否则会实际执行成 `pi pi ...`.
- 本机 pi 把 Enter 当换行键, `herdr agent prompt` 默认发 Enter 时, 文本可能只进入输入框而没有提交. 要先发文本, 再发送实际提交键 `alt+\`:
  `herdr pane send-text <pane-id> '<任务文本>'`
  `herdr agent send-keys <agent-name> "alt+\\"`
  这里命令文本里的两个反斜杠经 shell 转义后, 传给 Herdr 的键名是一个反斜杠, 即 `alt+\`.
- `herdr agent prompt --wait` 依赖状态变化检测. pi 很快回到 `idle`, 或检测快照没有及时更新时, 可能报 `agent_prompt_stalled`, 这不等于文本没有送达. 先用 `herdr agent read <agent> --source recent-unwrapped --lines <n>` 看屏幕, 再决定是否重发, 避免重复提交任务.
- `herdr agent wait` 也可能读到旧状态快照. 判断子代理是否真的工作, 以 `agent read` 的最新输出和仓库文件变化为准; 不要仅凭旧的 `state_change_seq` 判断.
- 并行创建互不依赖的子代理时, 用 `multi_tool_use.parallel` 同时创建标签/启动代理/读取输出, 但同一个代理内部的"发文本"和"发提交键"必须保持先后顺序.
- 子代理使用 pi 时, 必须先读 `herdr --skill`, 再检查环境变量和当前 pane 上下文; 控制命令只使用显式 pane ID 或唯一 agent 名, 不依赖当前焦点.
- 子代理完成后, 先读取其改动和测试结果, 再由主会话更新路线图状态和关闭记录; 不让子代理直接改路线图索引.
- Herdr 新会话可能继承仓库的脏状态. 启动前检查 `git status --short`, 收尾时区分本轮改动和用户已有改动, 不用破坏性命令清理现场.
- 共享工作树里不要让子代理用 `git stash` 隔离测试或用 `git checkout` 恢复文件. 前者可能被 `git-operation-gate` 误判并拦截, 后者可能覆盖主会话已有改动. 应先读取目标文件和 `git diff`, 用精确编辑处理自己的文件.
- 子代理自动执行的测试可能改写既有产物文件, 应先确认文件归属; 无关的生成结果要恢复, 不要把它混入 Milestone 提交.
