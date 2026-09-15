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
- **网页与网站 - 采纳 O1+O9+O5, 细节以 M04 结论为准**: 新容器 birth 补 `-p 8800` (0.0.0.0 动态宿主端口), 容器对外 web 监听 `0.0.0.0:8800`, present 多页复用单实例; STATE 登记 + 当前母体对应容器的双 URL. 用户接受 web 服务直达局域网及重建后重新分享 URL. 页面就绪后在本次工作已确定的设备上自动打开, 不把宿主桌面或最近轮询设备当成用户位置. 容器经信箱询问设备 agent 查网址/回话/代开; 无信箱仍可点交付包链接. 现有容器不处理, 不因假想 Vite/Next.js 服务增加端口竞争方案. 淘汰项不变: O4 pasta 自动转发/O8 固定宿主端口/O3 纯手工隧道. 详见 [M04 账本](../milestone-04/DECISIONS.md).
- **窗口直飞 - 采纳 waypipe 固化, 细节以 M06 结论为准**: 触发 = 信箱 exec 零参数指令 (幂等+限频) 通知设备侧拉起, 手工命令为底层零件, (c3) 常驻隧道仅文档备选; 音频同条 ssh -R unix 为主/独立 -R 为备/TCP 救场; 脚本模板归 birth 母本制只读挂载; 三态判定 = 脚本 preflight (env+socket 可连) + SKILL.md 编排 + 投信后轮询会话 socket 文件事实判活; base 层 SetEnv 合并单行+目录保障+StreamLocalBindUnlink yes; STATE 不动. 淘汰: (c1) waypipe 原生反向 (不存在), (c2) 容器拨出常驻隧道 (白名单冲突). 详见 [M06 账本](../milestone-06/DECISIONS.md). 遗留事实: Debian 12 waypipe 0.8.2 默认压缩 none, Rust 版删了重连

## 已关闭决策

<!-- 每个已关闭 Milestone 一行: 链接 + 一句话摘要 -->
- [MILESTONE-01](MILESTONE-01.md) — 信箱通道设计定稿 ([账本](../milestone-01/DECISIONS.md), ADR [0010](../../../adr/0010-mailbox-centralized-web-monolith.md)/[0011](../../../adr/0011-mailbox-exec-instruction-allowlist.md)): 信箱与 llm-proxy 合并为 host 常驻 web 单体 swt-base-server (端口区间+身份探测); 队列纯单向容器投/设备长轮询取, 回信走既有 ssh; 纯文本 4 类型, exec 限服务端指令白名单, 之外降级 request; 设备 HMAC 签名+容器 key 作用域+双向签名防重放; 跨机 ssh -L; 取信会话 host 上 pane/远程固定 tab 手动首启. 反方攻击推翻 exec 任意直批并修复响应未签名漏洞; "信箱实时性"迷雾随之关闭 (长轮询秒级)
- [MILESTONE-02](MILESTONE-02.md) — 信箱原型真跑通过: "来信→唤醒→处理"状态模型成立, 本机唤醒 2ms/空转零 token/缺省路由可用, 白名单直批/降级问人/越权 403/防重放全符合设计; 移交 M03: 投信错误响应也要签名, 扩展忽略非 message 触发事件, 端口区间首空闲 38417; 原型 `prototypes/mailbox-loop/` 保留作参考答案
- [MILESTONE-03](MILESTONE-03.md) — 信箱实施收口 (8 ISSUE, 213 测试全绿): swt-base-server.py 单体 (信箱+llm 中转, stdlib 零依赖) + 设备侧 pi 扩展/取信脚本 + birth 自动接线 + e2e 门禁 (D010 全覆盖) + SKILL.md 章节 + 驻留件; 评审驱动演进 14 条 UD ([账本](../milestone-03/UNAUTHORIZED_DECISIONS.md)), 含 post 响应用容器 key 签名/响应密钥每设备一份/ack 闭环/缺省路由过作用域; 指令集空集待 M08 填

- [MILESTONE-04](MILESTONE-04.md) - 网页访问设计关闭 ([账本](../milestone-04/DECISIONS.md), ADR [0012](../../../adr/0012-container-web-direct-access.md)): 新容器 8800 直达 + present 单实例 + 自身双 URL; 一母体一个活跃容器, 现有容器不处理; 信箱询问设备 agent 查网址并回话/代开, 明确当前设备而非按轮询猜; 接受重建后重新分享 URL, LAN 地址不确定才问. 六项验收已确认, 实施归 M05, 真机验收归 M09.
- [MILESTONE-06](MILESTONE-06.md) — 窗口直飞设计关闭 ([账本](../milestone-06/DECISIONS.md), ADR [0013](../../../adr/0013-waypipe-trigger-via-mailbox-zero-param-exec.md)): 触发走信箱 exec 零参数指令 (幂等+限频, 删 URL 参数防注入), (c3) 常驻隧道仅文档备选; 音频同条 ssh -R unix 为主/独立 -R 为备/TCP 救场, 排序挂 M07 必测; 启动脚本母本制 (birth 解析 chromium 路径, records-root 留档, 只读挂载) + preflight 管机械判定; base 层三项 (SetEnv 合并单行/目录保障/StreamLocalBindUnlink yes) 搭车 D017 级联; STATE 不动; 三态选路默认投信, ack 后轮询容器内会话 socket 判活, 超时落 noVNC; B 端前提文档声明+设备侧执行前自动检查本地通知. 反方攻击 6 条 5 采纳 (堵 ack 静默黑洞, 白名单零参数加严). 双机实测归 M07, 实施归 M08.

## 前沿

<!-- 开放 + 已解除阻塞 + 未被认领的 Milestone -->
- [MILESTONE-07](MILESTONE-07.md) — `task` — waypipe 双机实测: (b) 链路端到端 / 音频 7 必测点 (含备胎排序) / StreamLocalBindUnlink 行为 / 跨版本兼容

## 进行中

- [MILESTONE-05](MILESTONE-05.md) — 网页访问实施 (另一会话)

## 未决迷雾

<!-- 范围内但尚无法精确表述为 Milestone 的模糊视图; 随前沿推进而转化 -->
- ~~信箱实时性~~ — 已关闭 (M01 D008: 长轮询秒级, 无需 inotifywait/ssh -R 升级)
- Rust 版 waypipe (0.10+) 删除了断线重连 (recon/--control): base 层未来换发行版时回访重连策略
- mac/windows 的 noVNC 隧道仍手工: 目的地已排除, 信箱已落地 (M03✅) 自动化前提就绪 — 用户改主意时回访
- ~~分享给同事的 URL 稳定性~~ - 已关闭 (M04 D004: 用户接受重建后取得并重新分享新 URL, 不另立 Milestone)

## 范围外

<!-- 目的地之外, 有意识排除的工作; 标注排除原因 -->
- mac/windows 无感化 — 目的地明确排除, noVNC 兜底
- 跨互联网访问 — 只覆盖局域网
- web 服务认证/TLS — 与用户已拍的 "直达开放" 相反
- present 常驻展示服务自身改造 (present-web-server 会话跟踪中) — 本路线只消费其结果
- 现有容器的网页能力改造/迁移/重建 - 用户明确不处理, M05 只面向改动后新建容器
- 为假想 Vite/Next.js 竞争增加停服务切换或反向代理 - 当前组件没有该流程, M04 不据此扩需求
- 旧 Roadmap (use-sandbox-worktree/roadmap) 的 M10/M13 验收 — 另一会话推进

## 阻塞关系

```
M01(信箱盘问)✅ ──→ M02(信箱原型)✅ ──→ M03(信箱实施)✅ ────────────┐
                                                                ├─→ M08(直飞实施) ──┐
M06(直飞盘问)✅ ──→ M07(双机实测) ────────────────────────────────┘                  │
                                                                                   ├─→ M09(真机验收) ──→ 目的地
M04(网页盘问)✅ ──→ M05(网页实施, 进行中) -------------------------------------------┘
```

- 前沿: M07 (M06 关闭后解除阻塞); M05 进行中 (另一会话), 与 M07 互不阻塞; M08 仍被 M07 阻塞 (M03 侧已通)
- M05 网页直达不依赖信箱运行, 自动查网址/回话/代开复用已交付的 M03 能力; M09 验证实际双机路径
- M05 不再保证无镜像更新: 修改的规则必须实际进入新容器, 如涉及镜像更新则与 M08/M09 协调; 现有容器仍不处理
