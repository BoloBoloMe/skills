# 母体直连主仓 + 无 hooks config 收敛写面, 废弃独立 clone gate 与 pre-receive 钩子

use-sandbox-worktree 的容器回流端点 (原 gate) 改为主仓的 linked worktree (**母体**): 容器经 git 守护进程克隆母体分支, push 直写主仓的母体分支 ref, 推送落地 (updateInstead) 即时更新母体工作区. 不加任何 git 钩子 — 写面收敛由主仓 config 承担: `receive.hideRefs = refs/heads` + `!refs/heads/<母体分支>` + `refs/tags`, 配 `denyNonFastForwards` + `denyDeletes`, 实测 (git 2.53.0) 收敛为仅母体分支 ff-only. 读面同配 `uploadpack.hideRefs`.

## 备选方案

- 独立 clone gate + pre-receive 钩子 (原 D001/D005 方案): 被用户砍层 — 多一层中转仓与同步编排; 且 gate 若改 worktree 形态, 共享 hooks 目录的钩子会误伤主仓, 用户的解法是 "不要加 hooks".
- shared pre-receive 按 REMOTE_ADDR 分流 (只对 daemon 来源生效): 实测 REMOTE_ADDR 可被本地调用者注入伪造, 不宜作安全凭据; 用户亦明确不要 hooks.
- per-worktree core.hooksPath: 实测 daemon 的 receive-pack 不读取, 不可行.

## 后果

- 主仓成为 receive 端: config 常驻主仓, 只约束主仓作 receive 端, 用户日常 push 真远端无影响; 用户手动 push 进主仓会被 hideRefs 拒, 需文档明示.
- 拒绝信息退回 git 原生英文 (无自定义钩子人话), skill 文档附译解表 (D006 降级).
- HEAD 协议广告无法隐藏, 容器物理可读 main tip 对象 — 用户知情接受.
- **单活动母体不变量**: 主仓 config 是全局策略, 守护进程无认证, 无法表达每容器分支授权映射; 同一主仓同一时刻至多一个活动母体. 未来若要同仓不同母体并发, 须重开本决策 (恢复独立 receiver 或钩子).
- `!` 否定例外语法依赖 git 版本, 部署时须按目标版本重验.

详见 [DECISIONS.md](../changes/use-sandbox-worktree/DECISIONS.md) D007/D008/D010 与 [拓扑实测 findings](../changes/use-sandbox-worktree/milestone-02-worktree-topology-findings.md).
