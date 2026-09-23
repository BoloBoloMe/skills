# 信箱独立为 mailbox skill, pi 连接器扩展合法化

信箱原为 use-sandbox-worktree skill 的内置脚本. 经三方实操 (2026-09-21 报告) 与盘问, 决定: 信箱拆为独立 skill `mailbox` (含 LLM 中转面), 客户端/服务端全部收纳其中, swt 只经机器子命令 (discover/register-session/revoke-session) 使用不实现; 全部配置/运行时文件集中 `~/.agents/mailbox/`. 同时部分推翻 ADR-0014 对 "pi 扩展" 的排除: 允许 pi 扩展作为 mailbox skill 的**纯连接器**存在 (命令 /mail, /mail-listen, /mail-send, 取信守护注入会话), 禁止重实现脚本能力 — 脚本仍是唯一跨 agent 实现, codex/kimi 裸用脚本不受损. 理由: 信箱已是通用 agent 基础设施 (设备/容器/host 平权), 不该绑在沙盒工作树 skill 里; 扩展要的是 pi 侧优雅 (后台守护/来信唤醒/交互投信), 不是替代脚本. 完整决策与可用性改造范围见 `docs/changes/mailbox-standalone/DECISIONS.md`.

## 备选方案

- 信箱留在 use-sandbox-worktree 内: 被拒绝 — 信箱服务与沙盒工作树生命周期无关, 设备侧取信根本不需要 swt.
- pi 扩展承载信箱逻辑 (ADR-0014 当时排除的形态): 仍被拒绝 — 只覆盖 pi; 本次合法化的仅是连接器.
- 拆分时保留 swt.py 自带信箱客户端: 被拒绝 — 用户要求客户端/服务端同收一个 skill, swt 不重复建设.

## 后果

- ADR-0014 备选方案中 "pi 扩展命令 /swt-relay: 被拒绝" 一条被本 ADR 部分推翻 (仅限纯连接器形态).
- swt.py 依赖 mailbox.py 的机器子命令契约, 经 `__file__` 相对路径定位 (仓库与部署同构).
- 容器契约 env (`SWT_MAILBOX_URL`/`SWT_SESSION_*`) 保持不变; 容器内 pi 拿到扩展需等 base 镜像重建.
- 旧路径 (`~/.local/state/swt-mailbox/`, `~/.agents/sandbox-worktree/mailbox.json`) 首次运行自动迁移; 不留兼容 shim (旧容器已清空).
