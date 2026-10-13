---
name: use-herdr
description: 查看/控制 Herdr 布局或 agent 会话, 委派子代理, 或学习/安装 Herdr 时使用.
---

# Herdr

操作当前会话及处理交互失败走下面的入口. 我只要讲解或安装指导时, 读 https://herdr.dev/agent-guide.md; 这不授权你执行会话控制.

## 公共约束

查看或控制会话前确认 `HERDR_ENV=1`; 不满足就报告你不在 Herdr 管理的窗格内并停止, 避免打到别的 client 的聚焦会话. 检查通过后, PATH 中的 `herdr` 连接当前会话.
已装 CLI 是语法的权威: 先读 `herdr --help`, 再查任务相关命令组的帮助. 裸 `herdr` 会启动或附着 TUI; 带默认值的变更命令即使缺参数也可能执行, 探索只用帮助或已确认只展示帮助的组命令.

- 目标用 `--current`, 显式 ID 或唯一存活 agent 名, 不依赖 UI 焦点; ID 和状态从 JSON 响应取, 不从示例或侧栏顺序推导.
- 后台操作用 `--no-focus`, 除非我要求切换上下文, 让我的焦点保持不变.
- 用 `agent start` 或 `pane run` 前, 目标必须是 shell 自身在前台且停在交互提示符的空闲窗格.
- 依赖新 server 特性前查 `herdr status`; client/server 可能版本不同, 方法缺失时用已有方法.

server 错误在 stderr 上返回 JSON, 退出码 1; CLI 语法错误退出码 2.

## 操作入口

执行下列操作前先读对应材料; 同一任务涉及多类操作时分别读取, 执行中出现新条件也要补读.

| 触发条件 | 先读 |
| --- | --- |
| 定位/调整终端布局或解释布局 ID, 管理 server 会话 | [layout.md](layout.md) |
| 创建 agent 会话 | [launch.md](launch.md) |
| 查看/驱动已有 agent, 或处理其交互失败 | [agent.md](agent.md) |
| 操作原始终端进程或输入输出 | [pane.md](pane.md) |
| 向 pi 提交任务 | [PI.md](PI.md) |
| 发现/操作远端目标或管理 SSH machine 配置 | [machine.md](machine.md) |
| Herdr 窗格内 Chromium 启动失败 | [browser.md](browser.md) |
