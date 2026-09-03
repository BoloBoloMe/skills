# 状态: 待处理
# 类型: task
# 阻塞于: MILESTONE-01, MILESTONE-02

## 问题

瘦闭环端到端 (路线 A 的第一刀):

- 最简镜像: 仅 git + pi CLI + openssh-server (无 jdk/maven/playwright/VNC), 能起, ssh 能入
- gate 工作树仓 + pre-receive 钩子 (仅 sandbox/work + ff-only + updateInstead) 按 MILESTONE-01 拍板落地
- 编排脚本雏形: 建 worktree → 起容器 → ssh 入 → 容器内 clone/干活 → ff-push 过门禁回流 host 工作树 → 拆 (删容器+删 worktree)

全通网络中间态 (白名单未上) 须守 T7b 拓扑铁律: real 仓永不落在任何可写服务端点路径内.

完成判据: 整条 建 → 干 → 回流 → 拆 用 podman exec / ssh 实际跑通一次, 结果事实记入产物文件.
