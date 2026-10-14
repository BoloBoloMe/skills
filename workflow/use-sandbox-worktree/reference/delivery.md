# birth/resume 交付包

birth/resume 到达成功交付时读本文件; status 显示已有健康容器且我需要完整接入信息时也可按此核对. 逐项把脚本输出与 STATE 中属于目标容器的实际值转交给我; 缺项须说明原因, 不能默默略过. 显示栈缺席/降级, 旧容器无 web 口, 无已确认局域网地址等情况, 交付状态与缺席原因, 不拼一个看似可用的入口. 风险项见 [risks.md](risks.md), 一并交付. 不因容器出生自动打开 web 页面.

- **ssh 双入口**: 本机 `ssh -p <宿主端口> bolo@127.0.0.1`, 局域网 `ssh -p <宿主端口> bolo@<已确认的 host-LAN-IP>`. pasta 下容器没有可交付的独立 IP, `STATE.network-ip` 不是容器 ssh 入口. 用脚本交付行/STATE 的 `ssh-port` 或 `podman port <容器名>` 核对端口; stop/start 不变, rm 重建须重新取得. 局域网地址只用已确认值, 不从首个网卡猜: 地址保存在 records_root 根级, 首次 birth 未确认会出 DECIDE, 答复后带 `--lan-ip <ipv4>` 重跑; 换网络后也用此 flag 重确认.
- **noVNC**: 本机 `http://127.0.0.1:<vnc宿主端口>/vnc.html?resize=scale`, 使用 STATE 的 `vnc-port`. 局域网通过 `ssh -p <宿主端口> -L 6080:127.0.0.1:<vnc宿主端口> bolo@<已确认的 host-LAN-IP>` 建隧道, 再在远程机浏览器打开 `http://127.0.0.1:6080/vnc.html?resize=scale`. noVNC 无密码, ssh 凭据是访问门槛; 栈降级/缺席时报告状态而非交付不可达 URL.
- **web 双 URL**: 容器有 `web-port` 时, 本机 `http://127.0.0.1:<web-port>`, 局域网 `http://<已确认的 host-LAN-IP>:<web-port>`; 只交付本次母体目标容器, 不把其他对的 URL 混入. 地址未确认时局域网行明确写未附发; 旧容器没有 web-port 时报告原因. 分享出去的端口随容器 rm 重建可能改变.
- **本机直通**: 按 STATE 的 `host-display` 报告: `ok` 可直接在宿主机桌面接窗口, `degraded` 已回退 noVNC, `absent` 是远程/无桌面宿主的常态. 容器没有 headed 启动脚本时报告无远程直飞, 不假装可用; 有脚本时远程直飞命令模板见 [pull-window.md](../../mailbox/reference/pull-window.md) 的设备侧拉起模板, 使用本次交付的端口/地址代换.
- **登录凭证**: 密码固定 `sandbox`, 留档 `<records-root>/runtime/<identity>/ssh/<容器名>.password` (0600), 供人登录; 密钥 `<容器名>.ed25519` 用于脚本/herdr 的免交互登录 (`ssh -i <私钥> ...`). identity 是对级目录 `<项目slug>-<sha1(母体目录路径)前8位>`, 每对一套; 两种凭证随 terminate 清除.
- **herdr 双入口**: 本机 `herdr --remote ssh://bolo@127.0.0.1:<宿主端口>`, 局域网 `herdr --remote ssh://bolo@<已确认的 host-LAN-IP>:<宿主端口>`. 在普通终端执行, 不在 herdr 内套 herdr; 已在 herdr 中时用 [living.md](living.md) 的开窗格配方. 远程机需先拷贝私钥或使用密码.
- **容器内路径**: 容器账户 bolo, home `/home/bolo`, 代码在 `/home/bolo/Workspace/<母体分支名原文>` (含 `/` 时为嵌套目录). skill 库从 host 同路径只读挂载到 `~/.agents/skills/`, 项目 `.venv` 为可写匿名卷, pi 配置在 `~/.pi/agent/`. host `~/.m2/settings.xml` 可读时 birth 留一份私有快照并只读挂到容器同路径, `~/.m2/` 仍可写入 Maven 本地仓库; host 文件缺失/不可读就跳过, 不影响 birth, resume 不为旧容器增补. host 文件后续更新不实时同步. pi/codex/kimi 全局指令为 birth 拼装的只读单文件, 分别挂到 `~/.pi/agent/AGENTS.md` / `~/.codex/AGENTS.md` / `~/.kimi-code/AGENTS.md`; 四份本容器事实小抄 (`identity.md`/`network.md`/`web-ports.md`/`agents.md`) 只读挂到 `~/docs/`; 不设 `~/AGENTS.md`.

检查结果: STATE `stage=born`, 容器检出的分支与母体分支一致, 全部可用入口/缺席原因/登录凭证/风险均已交付. 交付脚本已打印大部分入口, 优先核对并转交实际输出, 不凭本文模板猜端口或地址.
