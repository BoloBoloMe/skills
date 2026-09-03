# use-sandbox-worktree Roadmap

## 目的地

use-sandbox-worktree skill 落地并经端到端演练验证可用 — 它管理 **sandbox-worktree** (host git worktree + 容器的绑定对) 的完整生命周期: 诞生 (use-worktree 建工作树作母体 + 拉起容器, 镜像由 host llm 按项目推导制备) → 存续 (用户 ssh 入容器驱动容器内 pi 干活, 产物 push 到母体分支, 推送落地回流 host, 展示链与登录墙容器内可用) → 终结 (删容器; 母体存删用户自决).

完成判据: 端到端演练跑通 建 → 干 → 回流 → 拆. 交付物是可工作的 skill, 不是又一份设计文档.

## 笔记

- 背景调研: [2026-09-01-research.md](../2026-09-01-research.md) (硬约束实测: nft 白名单注入点 / git gate 门禁 / VNC 通道, 全部已验证); [2026-08-31-sandcastle-design.html](../2026-08-31-sandcastle-design.html)
- 每个会话应查阅的 skill: present (展示链), use-worktree (诞生步骤), access-web (登录墙消费方)
- 固定偏好: 硬约束交给环境; 容器内 agent 自由驰骋, 容器之外用户说了算
- 新概念入领域语言: **sandbox-worktree** = git worktree + sandbox 容器的绑定对; skill 原名 use-sandbox 已改名
- agent 位置: agent 就在容器内 (镜像打包 pi CLI + skill 库 + 部分扩展); ssh 入容器的是用户; use-sandbox-worktree 会话只管理生命周期
- MILESTONE-01 盘问补充 (2026-09): 反方攻击已执行 (成立项转为 D003 freshness 可观测 / D006 报错全路径透明); 实测: 未跟踪文件不阻塞 updateInstead push, 跟踪文件脏拒 push 且原生报错半可读; daemon 无身份/审计为已认知限制 (D004)
- MILESTONE-02 盘问 (2026-09-03): gate 概念被用户重拍为**母体** (主仓 linked worktree), 独立 clone 与 hooks 废弃, 写面靠主仓 config 收敛; MILESTONE-01 的 D003/D006 两项反方修正随之废弃/降级; 术语入词汇表: 母体 / git 守护进程 / 推送落地
- 脚本封装决策 (2026-09-03): host llm 容器操作脚本化方向确认, 但 [反方审查](../milestone-02-scripting-opposing-review.md) 成立 — 首次完整流程未跑前不得冻结五场景接口; M03 只交可观测/可清理/可重跑的瘦 E2E 编排器 + 负向断言 + checklist, 五场景入口拆出为 MILESTONE-11 (用户在场盘问方案) → MILESTONE-12 (实现)

**路线侦查结论 (2026-09-01 后绘制会话)**:

- **路线 A「垂直切片先行」— 已选定**: 最瘦闭环 (git+pi+ssh 镜像 + 母体 config 拓扑 + 全通网络) 先跑通, 再逐层加固. 理由: 单项机制已被调研全部实测, 仅存不确定性是集成咬合, 垂直切片最早兑现它; 切片骨架与完成判据同形; SKILL.md 最后写 = 记录实证现实而非设计虚构
- 路线 B「契约先行」排除: 先写 SKILL.md 有写出不可执行文档的真实风险 (集中在集成缝); 其 "规格逼决策" 收益已由前置 deliberate Milestone 获得
- 路线 C「自底向上组件先行」排除: 组件各自验收但集成期才暴露接缝 (容器内 pi 真跑通 / 展示链 / ufw), 谨慎买不到新信息

**绘制会话拍板与修正**:

- 调研 §4.1 "白名单单模式" 修正为 **黑/白双模式**, host llm 创建容器前询问用户选定; 运行期不切换
- 镜像内容 **不钉死**: host llm 按项目推导依赖件 (运行环境/构建工具/harness/浏览器/系统工具), 镜像 = 带元数据的缓存制品, 记录优先用 podman 原生能力; 镜像/容器是环境信息, 不落项目 git
- 端口 **动态分配**: 宿主端口不钉死 (`-p 6080` 省宿主侧), `podman port` 事后发现; 容器内端口固定
- 白名单盘点确认是 sandbox-worktree 诞生步骤的 **固定环节**, 非可选

## 已关闭决策

<!-- 每个已关闭 Milestone 一行: 链接 + 一句话摘要 -->
- [MILESTONE-01](MILESTONE-01.md) — gate 初版设计拍完 (后已被 MILESTONE-02 的母体模型替代修订) — 详见 [../DECISIONS.md](../DECISIONS.md) D001-D006
- [MILESTONE-02](MILESTONE-02.md) — 生命周期语义拍完: 母体模型 + 无 hooks config 收敛 + 单活动母体不变量 + fail-closed 入口恢复 + 终结脏检查; 反方攻击两项成立已转为修正 — 详见 [../DECISIONS.md](../DECISIONS.md) D007-D013, [拓扑实测](../milestone-02-worktree-topology-findings.md), [反方审查](../milestone-02-opposing-review.md)
- [MILESTONE-05](MILESTONE-05.md) — podman 元数据能力实测 ([findings](../milestone-05/MILESTONE-05-findings.md)): image label 可查询可过滤, 项目标识/构建事实入 label; 版本 = digest 精确 + tag 可读; 内容物清单走外部制品 + label 存摘要; sandbox-worktree 身份入容器 label (镜像 label 自动继承, create --label 覆盖)

## 前沿

- [MILESTONE-03](MILESTONE-03.md) — `task` — 瘦闭环端到端 (镜像 + 母体 config 拓扑 + 编排脚本雏形, MILESTONE-02 决策已就位)
- [MILESTONE-06](MILESTONE-06.md) — `deliberate` — 镜像制备策略 (依赖件推导 / 版本语义 / 记录位置 — M05 结论在手)

## 未决迷雾

- 运行期新站点需求的处理流程形态 (回父会话确认 → 更新容器的具体动作)
- 多 sandbox-worktree 并发, 含同仓不同母体并发 (动态端口分配后可能缩水为资源限额问题; 不同母体并发被 D010 单活动母体不变量挡住, 须重开 receiver 隔离: 独立 clone 或钩子)
- rootless netns 清理偶发失败的编排兜底是否够用 (MILESTONE-04 后回访)
- 镜像版本积累后的 GC 策略
- 镜像复用的项目边界 (严格按项目隔离, 还是允许跨项目匹配)

## 范围外

- subagent 工具容器化 / sandcastle 集成落地 — 已否定方向 (调研 §6)
- pi 整进程容器化 (gondolin / whole-process-docker / OpenShell) — 隔离对象不同, 形态不同
- present web_server ISSUE-02/04 实现本体 — present-web-server 会话跟踪中, 本路线只消费其结果
- 云端 provider (vercel / daytona) — 本地 rootless podman 已够

## 阻塞关系

```
M01(已关闭) ──┐
              ├─→ M03 ──┬─→ M04 ────────────────┐
M02(已关闭) ──┘         │                       │
                        ├─→ M08 ────────────────┤
                        │                       │
                        └─→ M11 ─→ M12 ───────────┤
M05(已关闭) ─→ M06 ─────┴─→ M07 ─→ M09 ────────┴─→ M10 ─→ 目的地
```

- M03, M06 均已解阻塞, 互相独立, 可并行开工 (M03 为 AFK 编码任务, M06 为 HITL 盘问)
- M03 瘦闭环是全局咽喉; 关键路径: M03 → (M06 →) M07 → M09 → M10
- M11 (五场景脚本抽取**方案**盘问, HITL) → M12 (脚本实现, AFK) 阻塞 M10 (SKILL.md 引用场景脚本)
