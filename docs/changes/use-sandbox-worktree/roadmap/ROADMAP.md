# use-sandbox-worktree Roadmap

## 目的地

use-sandbox-worktree skill 落地并经端到端演练验证可用 — 它管理 **sandbox-worktree** (host git worktree + 容器的绑定对) 的完整生命周期: 诞生 (use-worktree 建工作树 + 拉起容器, 镜像由 host llm 按项目推导制备) → 存续 (用户 ssh 入容器驱动容器内 pi 干活, 产物经 gate 门禁 `sandbox/work` ff-push + `updateInstead` 回流 host, 展示链与登录墙容器内可用) → 终结 (删容器 + 删 worktree).

完成判据: 端到端演练跑通 建 → 干 → 回流 → 拆. 交付物是可工作的 skill, 不是又一份设计文档.

## 笔记

- 背景调研: [2026-09-01-research.md](../2026-09-01-research.md) (硬约束实测: nft 白名单注入点 / git gate 门禁 / VNC 通道, 全部已验证); [2026-08-31-sandcastle-design.html](../2026-08-31-sandcastle-design.html)
- 每个会话应查阅的 skill: present (展示链), use-worktree (诞生步骤), access-web (登录墙消费方)
- 固定偏好: 硬约束交给环境; 容器内 agent 自由驰骋, 容器之外用户说了算
- 新概念入领域语言: **sandbox-worktree** = git worktree + sandbox 容器的绑定对; skill 原名 use-sandbox 已改名
- agent 位置: agent 就在容器内 (镜像打包 pi CLI + skill 库 + 部分扩展); ssh 入容器的是用户; use-sandbox-worktree 会话只管理生命周期

**路线侦查结论 (2026-09-01 后绘制会话)**:

- **路线 A「垂直切片先行」— 已选定**: 最瘦闭环 (git+pi+ssh 镜像 + gate + 全通网络) 先跑通, 再逐层加固. 理由: 单项机制已被调研全部实测, 仅存不确定性是集成咬合, 垂直切片最早兑现它; 切片骨架与完成判据同形; SKILL.md 最后写 = 记录实证现实而非设计虚构
- 路线 B「契约先行」排除: 先写 SKILL.md 有写出不可执行文档的真实风险 (集中在集成缝); 其 "规格逼决策" 收益已由前置 deliberate Milestone 获得
- 路线 C「自底向上组件先行」排除: 组件各自验收但集成期才暴露接缝 (容器内 pi 真跑通 / 展示链 / ufw), 谨慎买不到新信息

**绘制会话拍板与修正**:

- 调研 §4.1 "白名单单模式" 修正为 **黑/白双模式**, host llm 创建容器前询问用户选定; 运行期不切换
- 镜像内容 **不钉死**: host llm 按项目推导依赖件 (运行环境/构建工具/harness/浏览器/系统工具), 镜像 = 带元数据的缓存制品, 记录优先用 podman 原生能力; 镜像/容器是环境信息, 不落项目 git
- 端口 **动态分配**: 宿主端口不钉死 (`-p 6080` 省宿主侧), `podman port` 事后发现; 容器内端口固定
- 白名单盘点确认是 sandbox-worktree 诞生步骤的 **固定环节**, 非可选

## 已关闭决策

<!-- 每个已关闭 Milestone 一行: 链接 + 一句话摘要 -->
- [MILESTONE-05](MILESTONE-05.md) — podman 元数据能力实测 ([findings](../milestone-05/MILESTONE-05-findings.md)): image label 可查询可过滤, 项目标识/构建事实入 label; 版本 = digest 精确 + tag 可读; 内容物清单走外部制品 + label 存摘要; sandbox-worktree 身份入容器 label (镜像 label 自动继承, create --label 覆盖)

## 前沿

- [MILESTONE-01](MILESTONE-01.md) — `deliberate` — gate 设计: 读通道 / gate 服务形态 / gate 干净保障
- [MILESTONE-02](MILESTONE-02.md) — `deliberate` — sandbox-worktree 生命周期语义 (worktree 面 + 容器面 + 终结面)
- [MILESTONE-06](MILESTONE-06.md) — `deliberate` — 镜像制备策略 (依赖件推导 / 版本语义 / 记录位置 — M05 结论在手)

## 未决迷雾

- 运行期新站点需求的处理流程形态 (回父会话确认 → 更新容器的具体动作)
- 多 sandbox-worktree 并发 (动态端口分配后可能缩水为资源限额问题)
- rootless netns 清理偶发失败的编排兜底是否够用 (MILESTONE-04 后回访)
- 镜像版本积累后的 GC 策略
- 镜像复用的项目边界 (严格按项目隔离, 还是允许跨项目匹配)
- 容器崩溃 / host 重启后的恢复语义 (可能与孤儿清理同解, MILESTONE-02 后回访)

## 范围外

- subagent 工具容器化 / sandcastle 集成落地 — 已否定方向 (调研 §6)
- pi 整进程容器化 (gondolin / whole-process-docker / OpenShell) — 隔离对象不同, 形态不同
- present web_server ISSUE-02/04 实现本体 — present-web-server 会话跟踪中, 本路线只消费其结果
- 云端 provider (vercel / daytona) — 本地 rootless podman 已够

## 阻塞关系

```
M01 ────────┐
            ├─→ M03 ──┬─→ M04 ────────────────┐
M02 ────────┘         │                       │
                      ├─→ M08 ────────────────┤
M05(已关闭) ─→ M06 ───┴─→ M07 ─→ M09 ────────┴─→ M10 ─→ 目的地
```

- M01, M02, M06 互相独立, 可并行开工 (均为 HITL 盘问)
- M03 瘦闭环是全局咽喉; 关键路径: M01/M02 → M03 → (M06 →) M07 → M09 → M10
