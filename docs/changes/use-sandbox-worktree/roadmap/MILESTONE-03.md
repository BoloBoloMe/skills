# 状态: 已关闭
# 类型: task
# 阻塞于: 无 (MILESTONE-01/02 已关闭)

## 问题

瘦闭环端到端 (路线 A 的第一刀):

- 最简镜像: 仅 git + pi CLI + openssh-server (无 jdk/maven/playwright/VNC), 能起, ssh 能入
- 母体 worktree + 无 hooks config 收敛 (hideRefs 否定例外 + denyNonFastForwards + denyDeletes + updateInstead) 按 MILESTONE-02 拍板落地 (DECISIONS D007/D008)
- 编排脚本雏形: 建 worktree 作母体 → 起容器 → ssh 入 → 容器内 clone -b <母体分支>/干活 → ff-push 推送落地回流母体目录 → 拆 (删容器; 母体留存)

**编排器交付边界** (脚本封装反方审查修正, 见 ../milestone-02-scripting-opposing-review.md): 交付物是**一个可观测/可清理/可重跑的瘦 E2E 编排器雏形** (内部阶段 birth/smoke/cleanup), 不是五个场景脚本 — 完整流程此前一次都没跑过, 先冻结接口等于固化未验证假设. 硬约束由可执行负向断言承担:

- config 写入后校验关键键值; daemon 只在 config 就绪后拉起
- clone 后必须检出母体分支 (非 HEAD detached); push 后母体目录文件必须变化
- 容器 remote 无真远端; 拆后母体留存
- 用户决策点 (母体复用/脏放行/黑白名单模式/端口冲突) 与失败清理未知项先入 checklist 登记, 不伪装成脚本交互

五场景入口 (诞生/恢复/查询/终结/换母体) 的抽取推迟到 MILESTONE-11.

全通网络中间态 (白名单未上) 须守: 真远端永不暴露给容器; 主仓 receive 写面已按 D008 config 收敛后方可拉起守护进程 (T7b 铁律在新拓扑下的对应形).

完成判据: 整条 建 → 干 → 回流 → 拆 用 podman exec / ssh 实际跑通一次, 上述负向断言全部通过, 结果事实记入产物文件.
