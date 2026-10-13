# 原始终端输入输出

跑普通命令或读取终端输出前读取. 创建/拆分/关闭布局用 [layout.md](layout.md), 驱动已识别 agent 用 [agent.md](agent.md).

## 普通命令

在符合主文件空闲 shell 条件的窗格中运行:

```bash
herdr pane run <窗格ID> "just test"
herdr pane wait-output <窗格ID> --match "test result" --timeout 120000
```

`pane run` 把命令文本和 Enter 原子发出. `pane wait-output` 立即搜索所选快照, 已存在的输出也能命中. `--match` 匹配字面子串, `--regex` 用 Rust 正则, 省略超时即无限期等待.
普通命令完成且结果已取回后, 对你创建的窗格按 [layout.md](layout.md) 的 `关闭与收尾` 处理.

## 读取输出

下面的 source 规则适用于 `pane read` 和 `agent read`:
- `visible`: 当前渲染的视口.
- `recent`: 最近渲染的输出, 含软换行.
- `recent-unwrapped`: 接回软换行的最近输出, 日志和转录优先用它.
- `detection`: 供 agent 探测用的纯文本底缓冲快照.

```bash
herdr pane read <窗格ID> --source recent-unwrapped --lines 120
```

颜色和终端样式可作证据时加 `--format ansi`, 否则用纯文本.
`--lines` 向 Herdr 索要更多行, 取自窗格可用屏幕和宿主 scrollback. 调大它仍看不到某条已完成响应的更多内容, 该窗格很可能在 alternate screen 里跑 agent. 离开 alternate screen 的行不进 Herdr 的宿主 scrollback, 加大行数找不回它们. 部分受支持的 idle agent 可由 Herdr 读取应用自身历史并恢复视口, 但并非所有应用和回复都能这样取回.
读取失败后, 让该 agent 把完整响应写到临时目录中的 Markdown 文件, 只回文件路径, 再从目标环境读文件. 这仅作兜底, 首次任务仍用常规输出, 避免把每次交互都变成文件交接.
