---
name: mailbox
description: "信箱 mesh: 设备/容器/本机 session 间传信的单文件服务, 配置集中 ~/.agents/mailbox/."
disable-model-invocation: true
---

# mailbox

**术语**:
- **信箱 (mailbox)**: 每台机器一个的服务实例, session 间传信的通用基础设施; 设备/容器/host 身份统一为 session, 地位平等. 自 use-sandbox-worktree skill 拆出独立 (不再绑沙盒工作树).

## 文件布局 (全部集中 `~/.agents/mailbox/`)

`config.json` (本机取信/投信凭证, 0600) / `neighbors.json` (邻居表) / `cli-state.json` (取信侧状态) / `state.json` (serve 状态) / `server.db` (session/邻居持久化); 父目录 0700.

**每 pi 会话独立信箱**: `sessions/<session-id>/` 下各会话独立 `config.json` (凭证 0600) / `cli-state.json` (取信状态) / `listen.json` (取信守护开关标记). 多 pi 会话可同时取信, 互不覆盖不串信.

旧路径 (`~/.agents/sandbox-worktree/mailbox.json`/`neighbors.json`/`mailbox-state.json`, `~/.local/state/swt-mailbox/`, 老老路径 `~/.config/swt/mailbox.json`) 首次运行自动迁移并提示; 不留兼容 shim.

## 常用命令

```text
uv run python scripts/mailbox.py serve                                  # 前台启动 (无 systemd 无自启)
uv run python scripts/mailbox.py send --to <session.id> --type notify --body "..."
uv run python scripts/mailbox.py ensure-session <session-id>            # 本会话独立凭证 (stdout JSON id/config/server/created)
uv run python scripts/mailbox.py presence <session-id>                  # 查目标在线状态 (online/offline/unknown)
uv run python scripts/mailbox.py send --to <id> --type notify --body "..."  # 目标明确离线会拒发; --force 强制投递
uv run python scripts/mailbox.py config set <field> [value]             # 密钥项经 stdin, 不回显
uv run python scripts/mailbox.py status                                 # 配置状态, 密钥脱敏
uv run python scripts/mailbox.py                                        # 缺省 = 取信 (阻塞长轮询)
```

**投信纪律**: 写正文前先跑 `presence <目标 session>`; 目标 id 不知道就先问我, 不猜. 查到 online / unknown 才写正文; offline 就停下, 报告"对方没在收信", 由我决定等它开守护还是 `--force` 先排队. 空 `--to` 查不了状态, 只用于谁收都行的通知. 完成标准: 每条信都能说出目标当时的在线结论 (离线强投的能说出是我确认过的).

serve 启动自动注册 `<hostname>-host` session 并写本机配置 — 本机取信零配置. 容器内凭证走 env (`SWT_MAILBOX_URL`/`SWT_SESSION_*`, birth 烘入; 契约名不可改, 非测试注入 env).

## pi 会话取信

pi 扩展按当前会话 session id 使用独立信箱: host 上调用 `ensure-session` 在本机 serve 注册独立 session (幂等, 不吊销既有), 取信子进程经 env `MAILBOX_CONFIG`/`MAILBOX_CLI_STATE` 指向 `sessions/<sid>/`; 容器内直接沿用 birth 注入的 `SWT_SESSION_*` 凭据, 不 ensure 也不清容器 env. 与他人会话相互 start/stop/重启不覆盖. 收信地址 = 返回的 `mailboxSessionId` (host = pi session id; 容器 = `SWT_SESSION_ID`).

agent 在交付前自行开启本会话取信守护, 调工具 `mailbox_listen(action=start|stop|status)` (或命令 `/mail-listen`); 不要只提示用户手输, 也不要用 bash 长轮询阻塞.

**接口版本提示**: `/admin/sessions/ensure` 是 serve 新增 admin 口; 运行中的旧 serve 进程不会因脚本更新而获得该接口 — 请重启 serve, 并重载 pi 扩展后再用.

## 在线状态 (心跳 presence)

服务端在长轮询 hold 中每 5 秒回一次心跳应答 (`payload.heartbeat=true`, 客户端立即重连), 据此维护每个 session 的 `online`/`offline`/`unknown` (缺省 15 秒无心跳算离线; 在等 poll 也算在线). 目标明确离线时 `send` 直接拒发 (exit 3), `--force` 跳过预查强制投递. 本机不认识的目标由服务端向邻居问一层 (1.5 秒预算), 都不认识 → `unknown`, 照常尝试投递. 已吊销 session 不再排队 (404).

完整协议 (HMAC 签名/时间窗/租约重投/mesh 洪泛/邻居配置/admin 口/指令集) → reference/mailbox.md.
