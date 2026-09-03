# 状态: 已关闭
# 类型: deliberate
# 阻塞于: 无

## 问题

gate 设计三件套, 一次盘问拍完:

1. **读通道**: 真远端完全不对容器暴露, 读全走 gate 镜像 — 已拍板, 见 DECISIONS.md D001.
2. **gate 服务形态**: 每 gate 专属 git daemon (`--enable=receive-pack`, base-path 仅含本 gate, 不开 export-all, 动态端口, 随容器生灭), 拒绝 ssh — 已拍板, 见 D004 与 ADR 0007.
3. **gate 工作树的干净保障**: 专用目录纪律 (可试跑, 禁编辑跟踪文件) + host llm 诞生校验与 push 失败回流诊断兜底 — 已拍板, 见 D005.

附加拍板: gate 读侧同步时机 (D002), freshness 可观测 base commit + fetched_at (D003), 报错全路径透明化 (D006, MILESTONE-03 实现约束).

盘问产物: [../DECISIONS.md](../DECISIONS.md) D001-D006 / F001-F005; [../../adr/0007-gate-daemon-not-ssh.md](../../adr/0007-gate-daemon-not-ssh.md); 领域语言新增 sandbox-worktree, gate 两术语. 反方攻击已执行, 成立项 (freshness 契约, 报错覆盖范围) 已转化为 D003/D006, 不成立项 (接收/审阅分离) 经实测 F001 折损后拒绝.
