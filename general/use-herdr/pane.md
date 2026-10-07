# 窗格操作

[`use-herdr`](SKILL.md) 的按需参考: 开兄弟窗格, 跑普通命令, 读输出, 收尾会话时才需要.

## 兄弟窗格几何与焦点

我指定了拆分方向就照做. 没指定就先看调用方窗格:

```bash
herdr pane layout --pane "$HERDR_PANE_ID"
```

宽窗格向右拆, 窄或高的窗格向下拆. 避免同方向连拆: 会造出不可用的窄列或矮行. 让我的焦点留在调用方窗格, 并显式保留调用方工作目录:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

合适时把 `right` 换成 `down`. 从 `.result.pane.pane_id` 读新窗格 ID.

可用 shell 窗格的标准: 停在交互提示符上, shell 自身在前台, 没有前台命令, 编辑器或 agent 在跑.

## 在另一窗格跑普通命令

```bash
herdr pane run <返回的窗格ID> "just test"
herdr pane wait-output <返回的窗格ID> --match "test result" --timeout 120000
herdr pane read <返回的窗格ID> --source recent-unwrapped --lines 120
```

`pane run` 把命令文本和 Enter 原子发出. `pane wait-output` 立即搜索所选快照, 已存在的输出也能命中. `--match <文本>` 匹配字面子串, `--regex <模式>` 用 Rust 正则. 省略 `--timeout` 即无限期等待.

按任务选 read source:
- `visible`: 当前渲染的视口.
- `recent`: 最近渲染的输出, 含软换行.
- `recent-unwrapped`: 接回软换行的最近输出; 日志和转录优先用它.
- `detection`: 供 agent 探测用的纯文本底缓冲快照.

颜色和终端样式可作证据时加 `--format ansi`, 否则用纯文本.

`--lines` 向 Herdr 索要更多行, 取自窗格可用屏幕和宿主 scrollback. 调大它仍看不到某条已完成响应的更多内容, 该窗格很可能在 alternate screen 里跑 agent. 离开 alternate screen 的行不进 Herdr 的宿主 scrollback, 加大行数找不回它们.

读取失败后, 让该 agent 把完整响应写成临时目录里的 Markdown 文件, 只回文件路径, 你再直接读文件. 此法仅作兜底; 首次 prompt 不要就要求文件输出.

## 清理已完成的会话

你创建的会话, 任务完成且结果已读走或已交付给我后, 尽早关闭, 不必等我指示: 空闲 tab 攒起来会埋掉还活着的会话.

保留的两种情形:
- 我还要查阅: 结果我还没过目, 或我说过要看这个会话.
- 你明确知道后续要复用: 还会给同一会话追加任务.

拿不准是否保留时先问我. 其余尽早关:
- 独立 tab 里的会话: `herdr tab close <tab ID>`.
- 兄弟窗格里的会话或跑完命令的窗格: `herdr pane close <pane ID>`.
