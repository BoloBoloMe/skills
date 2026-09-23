---
name: mailbox
description: 信箱 mesh + LLM 中转: 设备/容器/本机 session 间传信的单文件服务 (serve/send/取信/config/status) 与 OpenAI 兼容中转, 全部配置集中 ~/.agents/mailbox/.
---

# mailbox

**术语**:
- **信箱 (mailbox)**: 每台机器一个的服务实例, session 间传信的通用基础设施; 设备/容器/host 身份统一为 session, 地位平等. 自 use-sandbox-worktree skill 拆出独立 (不再绑沙盒工作树).
- **LLM 中转 (relay)**: OpenAI 兼容端点 (`/v1/chat/completions`, `/v1/models`), sk- key 认证. 与信箱同住本单文件/单进程/单 SQLite, **二合一不拆** (拆开是大手术).

## 文件布局 (全部集中 `~/.agents/mailbox/`)

`config.json` (本机取信/投信凭证, 0600) / `neighbors.json` (邻居表) / `cli-state.json` (取信侧状态) / `state.json` (serve 状态) / `server.db` (session/邻居/中转 key 持久化); 父目录 0700.

旧路径 (`~/.agents/sandbox-worktree/mailbox.json`/`neighbors.json`/`mailbox-state.json`, `~/.local/state/swt-mailbox/`, 老老路径 `~/.config/swt/mailbox.json`) 首次运行自动迁移并提示; 不留兼容 shim.

## 常用命令

```text
uv run python scripts/mailbox.py serve                                  # 前台启动 (无 systemd 无自启)
uv run python scripts/mailbox.py send --to <session.id> --type notify --body "..."
uv run python scripts/mailbox.py config set <field> [value]             # 密钥项经 stdin, 不回显
uv run python scripts/mailbox.py status                                 # 配置状态, 密钥脱敏
uv run python scripts/mailbox.py                                        # 缺省 = 取信 (阻塞长轮询)
```

serve 启动自动注册 `<hostname>-host` session 并写本机配置 — 本机取信零配置. 容器内凭证走 env (`SWT_MAILBOX_URL`/`SWT_SESSION_*`, birth 烘入; 契约名不可改, 非测试注入 env).

完整协议 (HMAC 签名/时间窗/租约重投/mesh 洪泛/邻居配置/admin 口/中转/指令集) → reference/mailbox.md.
