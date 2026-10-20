# 接入信息与交付

birth/resume 成功, 或交付健康容器的现有入口前必读. 只用本次目标容器的实际 STATE/脚本输出, 缺项紧跟原因; 地址/端口未确认就标缺席, 不夹带其他母体对. 不自动打开页面.

## 当前会话持续取信

交付前调用 `mailbox` skill, 在当前宿主会话用 `mailbox_listen(action="start")` 开启/复用持续取信, 核对返回 sessionId 就是当前会话且正在监听. 交付后保留守护, 不停/覆盖其他会话, 不用阻塞裸脚本代替. 服务/扩展缺席则报告未监听及原因, 仍可交付基础入口, 不声称随时可收信.
容器回信目标来自 birth 创建者真实 `PI_SESSION_ID`, 固定在目标记录/生成提示词/`identity.md` 中, 重入/resume 不改投. 将该目标与当前监听 sessionId 对照报告: 两者不同就说明仍回原会话, 当前监听不会接管原目标的信. 缺值标未登记, 不用容器/Herdr pane ID 或机器级 host 名代替.

## 展示方式

**按用途找信息, 不按脚本打印顺序抄一大串.** 会话输出与 `/list-sandbox` 详情页使用同一套分区思路:

1. **概况**: 容器名, 分支, 母体路径, 基础通道状态. 最前放需要我处理的阻塞/降级; 无则写无.
2. **SSH 登录**: 本机/局域网命令分行, 明确在哪台机器执行.
3. **Herdr 工作区**: 宿主侧栏的 machine 名称/登记状态, 以及普通终端的远程连接备选命令.
4. **Web 展示页**: 本机/局域网 URL 各占一行.
5. **桌面与浏览器**: noVNC 本机/局域网 URL, 本机直通状态, 窗口直飞及前提.
6. **凭据与路径**: 密码, 私钥路径, 容器代码路径, 提示词/小抄位置, host 收信会话与监听状态.
7. **检查与注意事项**: 任务条件, 缺席原因, 风险, 母体纪律.

会话里用短标题和空行隔开各区, 命令独立代码块, URL 独立一行; 不把多个命令挤进一条项目符号, 不用宽表格装长命令, 不整段粘贴 STATE JSON. 标签与实际值分开, 缺席原因紧跟对应入口, 最后只归纳待处理项, 不重复所有信息.

pi 的 `/list-sandbox` 可分区查看容器详情, 不把凭据/入口注入 LLM 上下文. 已采集概况不是交互登录或任务验证的证据.

## SSH 登录

- 本机: `ssh -p <宿主端口> bolo@127.0.0.1`.
- 局域网: `ssh -p <宿主端口> bolo@<已确认的 host-LAN-IP>`.

端口用脚本交付行/STATE 的 `ssh-port`, 必要时 `podman port <容器名>` 核对. pasta 下容器没有可交付的独立 IP, `STATE.network-ip` 不是 SSH 入口. stop/start 端口不变, rm 重建重新取得.

局域网地址只用已确认值, 不猜首个网卡. 地址保存在 records_root 根级; 首次 birth 未确认会出 DECIDE, 答复后带 `--lan-ip <ipv4>` 重跑, 换网络也用此 flag 重确认. 未确认时本机入口照交付, 局域网明确标未附发.

## Herdr 工作区

SSH 就绪后脚本自动把容器加入**宿主 Herdr** 的远程机器列表, machine 标签为容器名, 通过本容器专用 SSH 别名/私钥连接远端 default session. 已在宿主 Herdr 中就选侧栏该 machine, 不在 Herdr 内嵌套启动 Herdr. 交付核对目标记录 `herdr-machine.status/id/label`, 已登记不等于已验证所有远端 agent 可用.

宿主 `~/.ssh/config` 只增加本工具标记的 Include, 指向本容器 `runtime/<identity>/herdr/<容器>/ssh.conf`, 使用独立 known_hosts, 不改其他 SSH 主机条目. 主配置为符号链接或本工具的 Include 被手改时停止并报告, 不强行覆盖.

普通终端的备选入口分别列出:

- 本机: `herdr --remote ssh://bolo@127.0.0.1:<宿主端口>`.
- 局域网: `herdr --remote ssh://bolo@<已确认的 host-LAN-IP>:<宿主端口>`.

备选命令不自带私钥, 远程机先拷贝私钥或用密码. 自动登记失败会保留容器与 runtime 并报 PARTIAL, 修复后重跑同一 birth/resume, 不另建容器. 不自动批准替换不兼容的远端 server. 旧容器可在下一次 birth 重入/resume 时补登记; status/list 仍只读. terminate 只删除本容器登记的 machine/SSH 配置, 不停其他远端会话.

## Web 展示页

容器有 `web-port` 时:

- 本机: `http://127.0.0.1:<web-port>`.
- 局域网: `http://<已确认的 host-LAN-IP>:<web-port>`.

无已确认地址时标局域网未附发. 旧容器无 web-port 时写明原因. 分享端口随 rm 重建可能改变.

## 桌面与浏览器

### noVNC

- 本机 (宿主浏览器): `http://127.0.0.1:<vnc-port>/vnc.html?resize=scale`.
- 局域网 (访问设备浏览器): `http://<已确认的 host-LAN-IP>:<vnc-lan-port>/vnc.html?resize=scale`.

直接交付这两条 URL, 不附端口转发命令. 新容器将 6080 发布到宿主 `0.0.0.0`, 优先宿主 6080, 被占时自动分配动态端口. 两条 URL 使用本次实际 STATE 的 `vnc-port`/`vnc-lan-port`, 通常相同; 无已确认地址时标局域网未附发.

旧容器若仅绑定宿主回环, `vnc-lan-port` 为空, 只交付本机 URL 并说明需经确认后重建; stop/start/resume 不改变端口映射, 不自动迁移. 栈降级/缺席时报告状态, 不把不可达 URL 当可用入口.

noVNC 无密码/无认证, 同网段设备可直接查看和控制桌面, 不再经过 SSH 登录. 仅在可信内网使用, 屏幕避开密钥与敏感内容.

### 本机直通与窗口直飞

按 `host-display` 报告: `ok` 可直接在宿主机桌面接窗口, `degraded` 已回退 noVNC, `absent` 是远程/无桌面宿主的常态. 无 headed 启动脚本就明确无远程直飞; 有脚本时调用 `mailbox` skill, 按其 `reference/pull-window.md` 代入本次端口/地址, 命令与设备前提分开列出.

## 凭据与路径

- 人工 SSH 密码: `sandbox`. 密码文件/脚本与 Herdr 私钥路径取目标记录的 `password_file`/`ssh_private_key`, 不自行计算 identity 或拼路径. 免交互命令用 `ssh -i <私钥> ...`, 不打印私钥正文; 两种凭据随 terminate 清除.
- 容器账户 `bolo`, home 为 `~`; 代码路径取目标记录的 `clone_dir`, 不拿母体目录名替代分支或代码路径.
- host `~/.agents/skills/` 同路径只读挂载, 项目 `.venv` 为可写匿名卷, pi 配置 `~/.pi/agent/`.
- pi/codex/kimi 全局指令为 birth 拼装的只读文件: `~/.pi/agent/AGENTS.md`, `~/.codex/AGENTS.md`, `~/.kimi-code/AGENTS.md`. 本容器事实小抄在 `~/docs/{identity,network,web-ports,agents}.md`, 不设 `~/AGENTS.md`.
- 收信信息列出上方已核对的当前监听状态与容器原回信目标.
- 按目标记录报告可选 Maven settings 快照是否挂载; 凭据暴露和更新边界见 [risks.md](risks.md).

## 检查与注意事项

按 [task-conditions.md](task-conditions.md) 分开报告容器可登录/依赖检查/测试条件/写权限的通过/受阻/未检查, 原因与检查时间. 未给具体任务就标任务条件未检查. 证据仍适用就复用, 无写入批准不跑会自清理的写探针. 条件缺口不阻塞独立工作或基础入口交付, 但不宣称全部任务条件具备.

读取 [risks.md](risks.md), 将风险同区交付, 尤其 Web 局域网无认证/noVNC 无密码/敏感显示内容, 并提醒主流程中的母体只读纪律.

完成标准: 目标基础通道与 Herdr 登记有事实依据, 当前收信状态与原回信目标已区分, 入口/凭据路径/缺席原因/任务条件/风险均按区可查.
