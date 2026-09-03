# 状态: 已关闭
# 类型: deliberate
# 阻塞于: 无

## 问题

sandbox-worktree 从生到灭的状态机, worktree 与容器两个资源面一起拍 (决策互相咬合, 分开拍会拍出矛盾语义):

1. **worktree 面**: sandbox/work 分支生灭 (每会话 reset 到最新 main? gate 仓随会话新建销毁?) / 与 use-worktree 的交互方式.
2. **容器面**: 容器生灭与分支的同步关系 / 允许 stop 还是只许 rm (stop/start 后 netns 重建, 网络规则全失须重注入) / 镜像换版时存活容器怎么处置 / 孤儿容器清理.
3. **终结面**: 拆的顺序 / 脏状态检查 (容器内有未 push 的工作怎么办).
4. **端口分配**: 动态分配的宿主端口算不算 sandbox-worktree 的身份信息, 需要记录吗 (容器 restart 后宿主端口会变).

## 结论 (2026-09-03 盘问关闭)

拍板全貌 (细节与理由见 [../DECISIONS.md](../DECISIONS.md)):

- **母体模型** (D007): gate 重定义为主仓 linked worktree (母体), 容器代码 = 母体分支克隆, push 直写主仓 ref, 推送落地; 一名贯穿四物. 原独立 clone + hooks 方案废弃 (D001/D005 被替代)
- **无 hooks 拓扑** (D008): 主仓 config (hideRefs 否定例外 + denyNonFastForwards + denyDeletes + updateInstead) 收敛写面为仅母体分支 ff-only; 原生英文报错 + 文档译解表 (D006 被替代); HEAD tip 泄露知情接受
- **分支语义** (D009): 容器分支与母体同名, 跨容器累积, 无 reset, 无 freshness 观测 (D002 废弃, D003 废弃); 换基底/合流纯 host 侧; `sandbox/work` 名词废弃
- **单活动母体不变量** (D010): 同仓同时至多一个活动母体; 多容器共享允许, 冲突容器侧 fetch→解冲突→重推; 母体复用/存删用户自决; 同仓不同母体并发入未决迷雾
- **入口默认行为与恢复** (D011): worktree 检测 → 容器检测 → 询问重启/新建; 重启序列 fail-closed (砌墙→守护进程→校验→start); 无 --restart=always / systemd 自启
- **终结** (D012): 脏检查阻塞, 明示强拆, rm 容器; 母体不随终结删
- **镜像换版** (D013): 不动存活容器, 诞生时 digest 比对提示
- **守护进程**: 每容器一个随容器生灭 (D004 保留进 D008)
- **端口** (F006): 动态端口跨 stop/start/restart 稳定, 不记录; 占用则 start 失败, 原生报错透明
- **术语**: 母体 / git 守护进程 / 推送落地 入词汇表; ADR 0008 已记

产物: [拓扑实测 findings](../milestone-02-worktree-topology-findings.md) (F007), [反方审查](../milestone-02-opposing-review.md) (F008, 两项攻击均成立, 已转为 D010/D011 修正)
