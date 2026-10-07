---
name: use-herdr
description: Herdr (agent 终端工作区) 操作指南. 当被要求 查看/控制 `工作空间/workspace`, `标签页/tab`, `窗格/pane`, `另一个 agent`, 或 `开新会话` 时使用.
---

# herdr

Herdr 把终端组织成 工作空间/workspace, 标签页/tab, 窗格/pane, 能识别窗格内运行的 coding agent, 并通过 `herdr` CLI 暴露当前会话.

先分派任务:
- 你亲自操作 Herdr → 用本 skill, 从下面的环境检查开始.
- 帮我学习, 安装或排查 Herdr → 读 https://herdr.dev/agent-guide.md 并按它回答. 它面向教人, 本 skill 的操作规则不适用.
- 官网 → https://herdr.dev/zh-cn/docs/agent-skill/

## 环境检查

发任何控制命令前, 先验证你运行在 Herdr 管理的窗格内; 失败就声明你不在 Herdr 内运行, 然后停止. 切勿在 Herdr 之外查看或控制聚焦中的 Herdr 会话.

```bash
test "${HERDR_ENV:-}" = 1
```

检查通过后, PATH 里的 `herdr` 二进制即连接当前会话.

## 学习当前 CLI

已装二进制是命令语法的权威. 先跑 `herdr --help`, 再对任务相关的命令组跑裸组命令 (如 `herdr agent`) 看子命令与选项; 组名以 `--help` 输出为准.
切勿跑裸 `herdr` 做探索 (它会启动或附着 TUI), 也切勿用省略参数的方式探测会改状态的嵌套命令 (`herdr workspace create` 这类带默认值即成立). 多数控制命令返回 JSON.

## 驱动 agent

### 默认策略

开新会话的默认: 开在调用方所在 workspace 的新 tab, tab 名称按格式 `S-<子代理名>-<序号>` 生成; llm/思考深度除非我指定, 否则用 `llm-select` skill 选定; 与 llm 匹配的 coding agent 按 OpenAI → codex, Kimi → kimi, 其他/无匹配 → pi; 容器环境一律以最宽权限启动, 不拦截 llm 的任何操作, 非容器环境则不特地指定权限宽松度.

`tab create` 返回的 root pane 直接用作 `agent start` 的目标窗格, 沿用当前工作目录. 兄弟窗格, 新工作空间, worktree 或更换 cwd 仅在我明确要求时用; 兄弟窗格的几何与焦点规则见 [`pane.md`](pane.md).

### 启动

目标窗格须停在交互提示符上: shell 自身在前台, 没有前台命令, 编辑器或 agent 在跑. 起一个表意且唯一的名字, 原生 agent 参数只放在 `--` 之后 (`--` 是 agent 自身参数, 不是任务通道):

```bash
herdr agent start reviewer --kind codex --pane <窗格ID> [-- <agent参数...>]
```

kind 用我指定的; `herdr agent` 查看已装 kind 列表和选项. `agent start` 成功的返回条件: Herdr 在同一窗格探测到预期 agent, 且认为它可接受交互输入. 启动期间 agent 若进入 blocked, 命令立即返回 `agent_not_ready`, 但该名字仍可用于 `agent read` 和 `agent send-keys`. 启动默认 30 秒超时.
完成标准: `herdr agent get <名>` 报 idle.

### 提交任务

先 `agent start`, 再用提交方式单独送任务; 首条任务不放 `start` 的 `--` 之后. 提交方式按 agent 分流:
- pi: 提交键是 `alt+\`, 用 [`PI.md`](PI.md) 的两步法 (`pane send-text` + `send-keys "alt+\\"`).
- 其他 agent: `herdr agent prompt reviewer "<任务文本>" --wait --timeout 120000`.

`agent prompt` 尊重窗格实时的 bracketed-paste 模式, 把文本和随后的编码 Enter 作为一次有序提交发出, 两者都写完才报告提交成功. 目标 agent 正停在审批或提问对话框时, 它在发出任何输入前就以 `agent_blocked` 拒绝 — 此时先查看 blocked UI, 问过我之后再代答. 普通 agent 工作用 `--wait` 即可 (等第一个 settled 的 `idle`/`done`/`blocked`); 仅在需要特定状态的流程里用 `--until`, 例如等一个运行中的 agent 来要输入.

### 等待与 stalled 处理

带 `--wait` 时, 从非 working 态发出的 prompt 必须产生可观测的 `working` 或 `blocked` 活动, Herdr 最多等 5 秒; 观测不到返回 `agent_prompt_stalled`, 你的超时先到则返回 `timeout`. 这些信号只说明没观测到活动, 不证明任务没送达.

任何 `agent_prompt_stalled` 或超时之后, 第一步是 `herdr agent get <名>` + `herdr agent read <名>`, 按观测结果分状态收尾:
- 任务已送达, 或 agent 仍在跑 → 继续等待, 不重建.
- agent 或窗格已消失 → 才允许重建或重开.
- `blocked` → 先看 UI 并问我.

`agent wait` 报 `agent_not_found` 时改用窗格 ID, 不重试同名. `agent read` 报 `agent_not_idle` 表示 agent 正在干活, 不是错误 — 改用 `pane read` 或等待. 重发前先 `agent read` 看屏幕, 免得任务提交两遍.

### 读取结果

日志与转录优先用 `herdr agent read reviewer --source recent-unwrapped --lines 120`; 各 source 语义与 alternate screen 兜底见 [`pane.md`](pane.md).

## 参考材料

| 主题 | 文件 |
| --- | --- |
| 布局, 原语, ID 语义, 调用方上下文, 发现命令, agent 生命周期状态 | [`layout.md`](layout.md) |
| 兄弟窗格几何与焦点, pane 命令 source 语义, alternate screen 兜底, 清理已完成会话 | [`pane.md`](pane.md) |
| 安全与协调规则 | [`rules.md`](rules.md) |
| 驱动 pi agent 的提交键与显示环境注意点 | [`PI.md`](PI.md) |
| 跨机, 远程 server 或 SSH machine 任务 | [`machine.md`](machine.md) |
