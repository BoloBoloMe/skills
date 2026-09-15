# 状态: 已关闭
# 类型: task
# 阻塞于: 无 (MILESTONE-06 已关闭)

## 问题

双机实测 (HITL, 须用户设备在场). 必测清单 (据 [recon/03](../recon/03-waypipe.md) 3.4 + 6):

1. 音频 ssh -R unix 形态端到端出声
2. 设备侧 PipeWire 对同 uid unix 连接的认证行为
3. sshd 转发 socket 容器内权限/属主 (rootless uid_map 呈现)
4. StreamLocalBindUnlink 缺省行为 (断线残留挡重建) + 加 directive 后生效
5. waypipe ssh 与用户 -R 并存端到端
6. 容器 0.8.2 与设备侧实际版本的跨版本兼容
7. pulse 过 ssh 隧道的延迟/抗抖动主观评价
8. (若采纳 c3) 常驻隧道 + 容器内按需 server 端到端

## 实测结论 (2026-09-15, 真机)

环境: 设备侧 Ubuntu Workstation (waypipe **0.11.0** Rust 版, lz4/zstd/dmabuf/video) ↔ 容器 cross-host Debian 12 (waypipe **0.8.4** C 版, libpulse0 16.1, playwright chromium-1234). 接入形态: 设备经宿主机发布端口 `ssh -p 35625 bolo@192.168.131.194` 进容器 (设备→容器直连 IP 不可达, 只能走发布端口).

| 必测点 | 结果 |
|---|---|
| 1 音频端到端 | ✅ 客观形态: `-R` 反带 pulse unix socket, chrome 客户端出现在设备 `pactl list clients`, sink-input 活跃 (s16le 2ch 44100Hz). 主观出声未测 — 该设备无音频输出接口 |
| 2 PipeWire 同 uid 认证 | ✅ 默认放行, 无需 cookie/匿名模块 |
| 3 转发 socket 权限 | ✅ `srw------- 600 bolo:bolo` (StreamLocalBindMask 0177, `sshd -T` 核对) |
| 4 StreamLocalBindUnlink | ✅ 双向实证: 缺省 no 时干净断线仍残留 `/tmp/swt/pulse-b.sock`, 重连报 `Warning: remote port forwarding failed for listen path` 音频断; 加 `StreamLocalBindUnlink yes` 后残留原地转发成功. D004 第 3 项必要性实锤 |
| 5 waypipe + 用户 `-R` 并存 | ✅ **0.11 Rust 版照常透传用户 ssh 参数** (F004 最大风险点排除), 画面/音频同条 ssh 端到端成立, D002 主形态成立, 备胎排序无需启用 |
| 6 跨版本兼容 | ✅ 0.11.0 ↔ 0.8.4 互通; 设备侧 wrapper 自动给远端 server 加 `--compress lz4 --unlink-socket --threads 0` |
| 7 音频延迟主观评价 | ⏭️ 跳过: 设备无音频输出接口, 无主观对象 |
| 8 (c3) 常驻隧道 | ⏭️ 不测: D001 未采纳 (仅文档备选) |

### 新事实 (M08 输入)

- **N1 waypipe server 不经 shell 直接 exec 命令**: `PULSE_SERVER=... chrome` 赋值前缀被当程序名 (Spawn failure). 必须 `env VAR=... cmd` 或由启动脚本内部设 env — D003 脚本母本内部 export 即可, 交付包命令模板不得用赋值前缀.
- **N2 sshd 不清理转发 socket**: 干净断线后 `/tmp/swt/pulse-b.sock` 仍残留. waypipe 会话 socket 的消失靠 waypipe 自己 `--unlink-socket`, 且仅干净退出时 — spawn 失败/异常死亡的 `waypipe-server-<token>.sock` 会留尸体 (现场累积 2 具). **F005 修正**: socket 出现 = 会话已起的可靠信号, 但 socket 存在 ≠ 会话存活; D007 轮询新 token "出现" 仍有效, 判死不能只靠 socket 消失, 且残留文件会累积.
- **N3 XDG_RUNTIME_DIR 缺位即翻车**: ssh 会话原本无此变量, waypipe server 无法放置 display socket 直接报错. 本次经 `~/.ssh/environment` (base sshd_config 已有 `PermitUserEnvironment yes`) 注入解决 — D004 的 SetEnv 合并方案之外多一条已实证路径, M08 二选一.
- **N4 设备→容器当前是密码登录**: 取信会话自动化代执行不能每次输密码, M08 须含设备密钥Enrollment (或交付包提示).
- **N5 容器 uid 是 1001 不是 1000**: D004 的 `/tmp/xdg-1000` 命名假设 1000, 应改为 uid 派生或固定常量.
- **N6 容器内 apt waypipe 是 0.8.4** (recon 假设 0.8.2), 同为 C 版, recon 结论不受影响.
