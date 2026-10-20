# pi 会话收发信

pi 中启用收信或准备本会话投信身份时读本文件. 公共投信与授权规则以 [SKILL.md](../SKILL.md) 为准.

## 收信与地址

1. **开启本会话收信**: 需要反馈时就在委派/请求前调用 `mailbox_listen(action="start")`; 要在交付后收信也在交付前开启. 由你直接调用工具, 不让我的手动操作或 bash 阻塞长轮询代替守护. 完成标准: 工具成功且 `running=true`, 已取得 `piSessionId` 和 `mailboxSessionId`; 失败则报告原因.
2. **交出收信地址**: 对端 `send --to` 用实际返回的 `mailboxSessionId`, 不从 Herdr 名称, 窗格或目录推算. host 为每个 pi 会话注册独立信箱; 容器沿用 birth 注入凭据, 同一容器多个 pi 可能共用一个地址, 不能靠正文标识避免互相抢信. 完成标准: 对端拿到明确地址, 定向协作的各收件人地址独立; 共享地址时改用已有的会话通信方式.

守护收到信会唤醒空闲会话; pi 忙时排队, 本轮结束后再取下一封, 因而不保证即时反馈. 无其他工作可做时结束当前回复, 由来信唤醒, 不占着前台等待. 处理完守护转交的信, 由守护续取, 不再另起取信 CLI.

`status` 查询本会话运行态, `stop` 停止本会话并清除其监听标记. 同一会话续接/重启可按标记恢复, 其他新会话不会因此自动收信. 需要后续反馈时保留守护; 只管理自己的守护.

## CLI 投信身份

- **host**: 仅投信时用工具的 `status` 取得 `piSessionId`, 需收信则先完成上面的开启步骤. 将 `piSessionId` 交给 `ensure-session <piSessionId>`, 从 JSON 应答取 `config` 路径. 执行 `presence`/`send` 时为该命令设置 `MAILBOX_CONFIG` 指向此路径. 目录规整和凭据准备由命令完成, 不手算路径或复制密钥. 完成标准: CLI 使用的配置属于本 pi 会话, 而非机器级 `<hostname>-host`.
- **容器**: 原样使用 birth 注入的 `SWT_MAILBOX_URL`/`SWT_SESSION_*`, 无需 `ensure-session`, 也不清除这些环境变量. 完成标准: 投信身份与实际 `mailboxSessionId` 一致.

开启守护只给其子进程设置环境, 不会让另一次 bash 的裸 `send` 自动改用本 pi 会话身份. 我手动使用 `/mail-send` 时扩展会选择本会话凭据; `/mail` 查看总览, `/mail-listen` 管理守护.

工具缺席, 凭据准备失败或接口不兼容时, 读 [配置与排障](mailbox.md). Herdr 协作的地址交换和推送优先纪律由 `use-herdr` skill 的 `PI.md` 维护.
