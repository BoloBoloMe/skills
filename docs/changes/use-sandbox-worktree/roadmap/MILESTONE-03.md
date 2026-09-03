# 状态: 待处理
# 类型: task
# 阻塞于: 无 (MILESTONE-01/02 已关闭)

## 问题

瘦闭环端到端 (路线 A 的第一刀):

- 最简镜像: 仅 git + pi CLI + openssh-server (无 jdk/maven/playwright/VNC), 能起, ssh 能入
- 母体 worktree + 无 hooks config 收敛 (hideRefs 否定例外 + denyNonFastForwards + denyDeletes + updateInstead) 按 MILESTONE-02 拍板落地 (DECISIONS D007/D008)
- 编排脚本雏形: 建 worktree 作母体 → 起容器 → ssh 入 → 容器内 clone -b <母体分支>/干活 → ff-push 推送落地回流母体目录 → 拆 (删容器; 母体留存)

全通网络中间态 (白名单未上) 须守: 真远端永不暴露给容器; 主仓 receive 写面已按 D008 config 收敛后方可拉起守护进程 (T7b 铁律在新拓扑下的对应形).

完成判据: 整条 建 → 干 → 回流 → 拆 用 podman exec / ssh 实际跑通一次, 结果事实记入产物文件.
