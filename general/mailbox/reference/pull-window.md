# 拉窗 (swt.pull-window) 收信侧配方

收到 `swt.pull-window` 拉窗信时读本文件. 本配方针对 Linux Wayland 桌面与 waypipe; 容器侧选路和 noVNC 退路由 `use-sandbox-worktree` skill 的 `reference/pull-window.md` 维护. 投信与授权规则沿用 [SKILL.md](../SKILL.md).

## 指令范围

`exec` 正文为 JSON 对象, 必含 `tool`/`container`, 只允许额外的 `url` 键:

| 字段 | 含义 |
| --- | --- |
| `tool` | 固定为 `swt.pull-window` |
| `container` | 投信方自己的 pi session id, 或服务登记归属的本容器名 |
| `url` | 可选, 已核实的容器内页面 URL |

服务端校验形状与投信方绑定; pi 信箱的容器归属从注册记录取得, 再剥接线 session 的随机后缀, 不相信正文自报归属; 不符合规则就标记降级, 收信侧按 `request` 核实. 取信脚本负责 waypipe 在场与同容器 300s 限频, 两种容器标识归一后共用限频, 缺席/重复直接回执 skipped. 这些机械判定不再由 LLM 重算.

## 设备侧操作

1. **确认连接与页面**: 核对本次容器的实际 SSH 入口, 免密访问能力, 容器内 headed 启动脚本及 URL. 用信中已确认的 `url` 或前置编排给出的容器内地址, 缺值则请求补充. 该页面在容器浏览器内打开, 所以用容器内可达地址, 不拿设备访问用的局域网映射 URL 替代. 完成标准: 连接目标和页面均有实际来源, 设备具备 Wayland/waypipe 条件.
2. **复用或拉起**: 先经同一 SSH 入口检查目标容器是否已有活跃 waypipe 进程; 活跃则复用并回报. 仅有 socket 文件不证明存活. 需要新开时使用下面模板, 保持后台会话存续. 完成标准: 已确认复用的活跃会话, 或新会话启动结果; 失败则交给容器侧退路.
3. **回报实际结果**: 按主文件的投信流程回告原会话, 区分连接建立, 页面拉起与我能看到窗口. 完成标准: 已回报可确认的结果或失败原因, 不以 ack 或后台命令退出码代替窗口结果.

命令里的占位值来自本次连接资料, 不绑定固定用户/home. 已有授权的容器启动脚本负责设置其环境; 命令行不加环境赋值前缀, 曾因此被 waypipe 当成程序名而启动失败. 模板采用 POSIX shell:

```bash
nohup waypipe ssh -p <容器映射SSH端口> <SSH用户>@<已确认宿主地址> <容器内headed脚本> --user-data-dir=/tmp/pullwin-<标记> --disable-gpu --disable-gpu-compositing --no-first-run --no-default-browser-check --start-maximized <容器内URL> >/dev/null 2>&1 &
```

- **独立浏览器目录**: `<标记>` 用容器名或来信 id. 曾因默认 Chromium profile 被占用, 新调用被单例转发后秒退, 因此保留独立 `--user-data-dir`.
- **软件渲染**: 保留 `--disable-gpu --disable-gpu-compositing`, 曾在部分 waypipe 版本出现任务栏有图标却无可见画面.
- **可选音频**: 需要且两端条件具备时, 在 SSH 参数加入 `-R /tmp/swt/pulse-b.sock:<设备音频socket绝对路径>`. 容器音频 socket 条件缺失时省去该段, 仅无声音, 不阻断拉窗.

历史已验证容器 waypipe 0.8.4 / 宿主 minimal 构建 / 设备 0.11.0 可混用, 无需仅因版本不同拒绝尝试; 当前兼容性仍以实际拉窗结果为准.
