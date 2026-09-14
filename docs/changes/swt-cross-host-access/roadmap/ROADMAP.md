# swt-cross-host-access Roadmap

## 目的地

use-sandbox-worktree 的容器 GUI/内容无感访问能力完整固化进 skill 并真机验证通过 — 三类场景 (容器内 headed 浏览器过登录墙 / present 展示 HTML / 容器内 web 服务) × 两个访问位置 (宿主本机 Linux Wayland 桌面会话 / 局域网内其他 Linux Wayland 设备) 各有明确无感路径: 该弹窗弹窗, 该点 URL 点 URL, 零手工命令. 宿主无桌面会话 → 只走远程路径; 远程设备为 mac/Windows → noVNC 兜底 (现状不动).

完成判据: 三类场景 × 两个位置各真机跑通一次, SKILL.md 记录实证现实. 范围含方案定稿 → 实施 (base/display 镜像 + swt.py + SKILL.md + 交付包, 含 D017 级联重建) → 真机验证.

## 笔记

- 前序调研 (事实底座): [跨机GUI无感访问可行性调研报告](../use-sandbox-worktree/跨机GUI无感访问可行性调研报告.md) (waypipe 实测通过, 8 坑), [容器GUI无感访问技术报告](../use-sandbox-worktree/容器GUI无感访问技术报告.md) (同机直通原理), 交接 [2026-09-13-跨机gui调研](../handoff/2026-09-13-跨机gui调研.md)
- 方向侦查 (2026-09-13, 三子代理并行): [01 信箱通道](../recon/01-llm-channel.md) / [02 网页与网站](../recon/02-present-web.md) / [03 waypipe 固化](../recon/03-waypipe.md)
- 术语对齐: 本 Roadmap 用 **设备侧** (人面前的机器) / **容器侧**, 不用 A/B (调研报告与用户口头用法相反)
- 关键不对称: 设备侧→容器侧通信现成 (ssh 入口 + herdr 委派配方); 容器侧→设备侧缺失 (白名单挡出向/无凭证/设备无常驻接收端)
- 固定偏好: 容器之外用户说了算; 零手工命令 — 手工命令只作底层零件, 由设备侧常驻 AI 或自动化代执行
- 领域文档: docs/language/UBIQUITOUS_LANGUAGE.md (sandbox-worktree/母体/常驻展示服务); 相关 ADR 0005 (远程展示网段可读取舍) / 0006 (扁平并集); 决策账本 D040 (6080 回环发布) / D051 (双模显示栈) / D017 (镜像级联重建) / F019 (wayland 禁中继)
- 与旧图 (use-sandbox-worktree/roadmap) 的边界: M13 (本机直通 D051) 互补不重叠 (其范围外即本图范围内); M14 第 2 项 (D053 展示端口预留) 已移交本图 M04/M05 (0.0.0.0 直达超集取代回环, D053 标替代), M14 第 3 项 (LAN IP 选取) 是 M05 软依赖

**路线侦查结论**:

- **信箱通道 — 采纳用户主候选 (a)**: 队列放容器内 + 设备侧常驻 pi 会话 (挂 herdr) 由 pi 扩展驱动 pop→处理→pop 循环, 经既有 ssh 入口拉取. 依据: pi 扩展能力面全过 (`sendMessage(triggerTurn)` 无输入自触发, 官方 file-trigger.ts 为现成骨架; 轮询放 Node 层零 token; `pi.exec` 跑 ssh). 淘汰: (b) 容器直驱设备 herdr (容器持设备凭证 + 白名单放行, 双违背安全立场, IP 漂移); (c) ssh -R 反带接收端降级为实时性升级项 (进迷雾)
- **网页与网站 — 采纳 O1+O9+O5 共形**: birth 补 `-p 8800` (0.0.0.0 动态宿主端口, 修硬缺口 — 镜像 EXPOSE 8800 从未被 swt 发布) + 8800 钉死为容器对外 web 端口 (present/dev server 共用一个端口) + STATE 登记 + 交付包双 URL + 本机 xdg-open. 用户已拍 web 服务直达局域网 (要发给同事看, 取舍明示接受). 淘汰: O4 pasta 自动转发 (暴露面隐性扩大, 违 D040), O8 固定宿主端口 (多容器必撞), O3 纯手工隧道 (违零手工). 传话通道是加速器不是底座 (不解决网络可达性)
- **窗口直飞 — 采纳 waypipe 固化**, 触发链路以 (b) 经信箱通知设备侧拉起为主, (a) 手工命令降级为底层零件; (c3) 设备侧常驻隧道 + 容器内按需起 server 列为盘问点. 淘汰: (c1) waypipe 原生反向 (不存在, server 恒为拨出方), (c2) 容器拨出常驻隧道 (白名单冲突). 其他事实: 脚本模板归 birth 母本制 (chromium 路径漂移 + 调参不触发级联); 三态判定靠文件/socket 事实不靠 env; 音频 ssh -R 文献可行待实测 (StreamLocalBindUnlink 缺省 no); Debian 12 waypipe 0.8.2 默认压缩 none, Rust 版删了重连

## 已关闭决策

<!-- 每个已关闭 Milestone 一行: 链接 + 一句话摘要 -->
- [MILESTONE-01](MILESTONE-01.md) — 信箱通道设计定稿 ([账本](../milestone-01/DECISIONS.md), ADR [0010](../../../adr/0010-mailbox-centralized-web-monolith.md)/[0011](../../../adr/0011-mailbox-exec-instruction-allowlist.md)): 信箱与 llm-proxy 合并为 host 常驻 web 单体 swt-base-server (端口区间+身份探测); 队列纯单向容器投/设备长轮询取, 回信走既有 ssh; 纯文本 4 类型, exec 限服务端指令白名单, 之外降级 request; 设备 HMAC 签名+容器 key 作用域+双向签名防重放; 跨机 ssh -L; 取信会话 host 上 pane/远程固定 tab 手动首启. 反方攻击推翻 exec 任意直批并修复响应未签名漏洞; "信箱实时性"迷雾随之关闭 (长轮询秒级)
- [MILESTONE-02](MILESTONE-02.md) — 信箱原型真跑通过: "来信→唤醒→处理"状态模型成立, 本机唤醒 2ms/空转零 token/缺省路由可用, 白名单直批/降级问人/越权 403/防重放全符合设计; 移交 M03: 投信错误响应也要签名, 扩展忽略非 message 触发事件, 端口区间首空闲 38417; 原型 `prototypes/mailbox-loop/` 保留作参考答案

## 前沿

<!-- 开放 + 已解除阻塞 + 未被认领的 Milestone -->
- [MILESTONE-04](MILESTONE-04.md) — `deliberate` — 网页/网站无感盘问: 8800 钉死 / STATE 登记 / 交付包双 URL / 本机自动打开 / dev server 约定 / 分享形态
- [MILESTONE-06](MILESTONE-06.md) — `deliberate` — 窗口直飞盘问: 触发链路 / 三态选路 / 音频形态 / 脚本母本制 / base 层改动与级联成本 / B 端前提
- [MILESTONE-03](MILESTONE-03.md) — 信箱实施 (M02 已关闭, 阻塞解除)

## 未决迷雾

<!-- 范围内但尚无法精确表述为 Milestone 的模糊视图; 随前沿推进而转化 -->
- ~~信箱实时性~~ — 已关闭 (M01 D008: 长轮询秒级, 无需 inotifywait/ssh -R 升级)
- Rust 版 waypipe (0.10+) 删除了断线重连 (recon/--control): base 层未来换发行版时回访重连策略
- mac/windows 的 noVNC 隧道仍手工: 目的地已排除, 但信箱落地后可顺带自动化 — 用户改主意时回访
- 分享给同事的 URL 稳定性: 动态宿主端口每次重建会变, 链接失效 — 先由 MILESTONE-04 盘问消化, 消化不掉再立 Milestone

## 范围外

<!-- 目的地之外, 有意识排除的工作; 标注排除原因 -->
- mac/windows 无感化 — 目的地明确排除, noVNC 兜底
- 跨互联网访问 — 只覆盖局域网
- web 服务认证/TLS — 与用户已拍的 "直达开放" 相反
- present 常驻展示服务自身改造 (present-web-server 会话跟踪中) — 本路线只消费其结果
- 旧 Roadmap (use-sandbox-worktree/roadmap) 的 M10/M13 验收 — 另一会话推进

## 阻塞关系

```
M01(信箱盘问)✅ ──→ M02(信箱原型)✅ ──→ M03(信箱实施) ──────────────┐
                                                                ├─→ M08(直飞实施) ──┐
M06(直飞盘问) ──→ M07(双机实测) ────────────────────────────────┘                  │
                                                                                   ├─→ M09(真机验收) ──→ 目的地
M04(网页盘问) ──→ M05(网页实施) ──────────────────────────────────────────────────┘
```

- 前沿: M03/M04/M06 互不阻塞
- M08 依赖 M03: 窗口直飞的 "经信箱通知设备侧拉起" 集成需要信箱就位
