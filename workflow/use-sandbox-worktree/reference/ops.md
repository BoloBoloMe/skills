# 容器操作与救场

排查 Podman/Git 桥/防火墙/本机显示直通, 以及 swt 编排之外手工收敛时读本文件. 本文是命令和失败原因的操作参考, 实际编排行为以 scripts/swt.py 等脚本为准; 更换容器运行方式必须连同脚本检查, 仅修改本文不会改变功能.

## 容器命令收拢

- 生命周期: `podman create --name <名> --label ... -p 22 -p 127.0.0.1:6080:6080 (被占时 -p 127.0.0.1::6080) --shm-size=1g -v <records-root>/runtime/<identity>/git-bridge:/run/swt-git -v <records-root>/runtime/<identity>/agent-prompts/<容器>/<agent>_AGENTS.md:<agent 配置路径>/AGENTS.md:ro -v <records-root>/runtime/<identity>/agent-prompts/<容器>/docs:/home/bolo/docs:ro [-v <records-root>/runtime/<identity>/maven/<容器>/settings.xml:/home/bolo/.m2/settings.xml:ro] [-e 继承env] <镜像>` / `podman start|stop|rm -f` (容器不设内存/CPU 上限); Maven 可选挂载只在 host 原文件可读且快照暂存成功时加入, 容器启动后修正 `~/.m2` 目录属主以便 Maven 写本地仓库; 旧记录的 auth.json 不走挂载, 启动后 `podman exec -i <容器> sh -c 'install -d -o bolo -g bolo ...; cat > .../auth.json; chown bolo:bolo; chmod 600' < host-auth.json` 注入 (host 缺失则跳过并警告)
- 新模板模型初始化: `agent-template.py install|check --runtime-file <创建记录> --name <目标>`; 固定工具核对完整 ID/仓库/母体/创建令牌/快照摘要后, 以 `podman exec -i --user root <完整ID> uv run --no-project --offline python /opt/swt-agent-config/runtime.py ...` 接收 stdin. Key 不放 argv/create -e/SSH environment, 只存容器 bolo 所有的 600 文件. 旧容器/旧记录被 installer 拒绝, 不迁移. 新 resume 只检查, 不重装或复制主机 OAuth.
- git 通道: 每对一个 daemon (并行母体): host 侧 `git daemon --enable=receive-pack --base-path=<主仓父目录> --listen=127.0.0.1 --port=<动态> --reuseaddr --log-destination=none <母体目录>` (git-daemon-export-ok 落母体私有 git 目录, 经 `git -C <母体> rev-parse --git-dir` 推导); host 侧桥 `socat UNIX-LISTEN:<git-bridge>/git.sock,fork,mode=600 TCP:127.0.0.1:<daemon端口>`; 容器内 `podman exec -d <容器> socat TCP-LISTEN:9418,bind=127.0.0.1,fork,reuseaddr UNIX-CONNECT:/run/swt-git/git.sock`; 桥进程发现: `pgrep -f 'socat.*UNIX-LISTEN:.*git-bridge/git.sock'`
- 本机直通: create 时 `-v <宿主wayland socket>:/run/swt-wayland/wayland-0 -e XDG_RUNTIME_DIR=/run/swt-wayland -e WAYLAND_DISPLAY=wayland-0 [--device /dev/dri]` (宿主机 socket 存在才挂); 仅挂 Wayland, 不挂 X11 socket (X11 允许客户端嗅探/注入). rootless 映射使 socket 在容器内属于 root, bolo 在原权限下连不上; 宿主 `chmod 0777 <宿主wayland socket>` 才能连接, 新模板 birth 遇权限不足会先请求我决定而不擅自放宽, 旧容器 resume 重保权限. 父目录 `/run/user/<uid>` 权限 0700 限制其他宿主账户; 会话重启会重置 socket 权限. 禁用 socat 中继: Wayland 依靠 SCM_RIGHTS 传文件描述符, 中继截断后 Chromium 会报通信错误. 直通不通时回退 `DISPLAY=:99` noVNC, 状态记 ok/degraded/absent. 风险见 [risks.md](risks.md).
- 端口发现: `podman port <容器名>` (22 = ssh, 6080 = noVNC); 状态: `podman ps -a --filter label=sandbox-worktree.repo=<主仓>`
- 镜像: `podman build` / `podman images --filter label=run.sandbox-worktree.project-id=<主仓路径>` / `podman inspect`
- 容器内操作: `podman exec` (key 注入 / swt-vnc start|stop|status / display 检查经 swt-display.py); 防火墙注入: `podman unshare nsenter --net=<容器网络命名空间> nft -f -`
- daemon 发现: `pgrep -af 'git[ -]daemon.*--base-path=<主仓父目录>'` 后核对命令行末位服务目录 (每对一个, 勿误伤同父目录其他对)

## 网络控制 (net-firewall, 一般由 swt 编排)

普通白名单增删/补理由先用 `swt.py network show/update --name <目标>`, 不手拼完整 allow 或调用底层 apply 绕过审批. network 输出末行 `NETWORK {...}`, 0 成功/无变化, 1 等待差异审批, 2 输入或前置不足, 3 执行失败 (即使已回退), 4 缺工具/环境不支持. 只改指定目标, 自动项由目标事实维护. 旧条目缺理由可保留或如实补写"继承自旧任务,用途未核实", 不编造为当前任务必需.

出现 network-change 时先 show 看 pending/checks, 再 `network recover --name <目标>` 预览旧配置恢复, 我批准后带 `--confirm <收据ID>` 重跑. 有限恢复不接管未知规则/同名新 ID, 停止目标只恢复记录而不 start. 恢复失败保留标记, 不通过自动 stop/restart/clear 救场; 不要用旧版脚本处理新事务. 若我显式终结事务原目标, 脚本保留私有事务审计并清活动标记, 不报告为恢复成功. 实际规则与记录不一致须先报告差异让我决定, 对应人工收敛需另行授权, 不以重新审批收编未知状态.

底层正常由 birth/resume/terminate/network 自动调用. 以下是另行授权的手救场原语, 必须从目标 inspect 的 SandboxKey 核对 netns, 不用缺省路径猜业务目标:
```text
uv run python scripts/net-firewall.py show --netns <目标SandboxKey>
uv run python scripts/net-firewall.py remove --container-ip <IP> --netns <目标SandboxKey>
uv run python scripts/net-firewall.py clear --netns <目标SandboxKey> # 删整表, 会影响共享该表的其他目标
```
机制: 规则注入容器所在网络命名空间的自有表 `inet swt`, 过滤覆盖 forward/input/output 三链 (output 管容器主动出站, 2026-09-14 出站链修复), 按容器源地址限定, 容器内任意 uid (含 root) 不可达不可删. 容器停 → 命名空间拆 → 规则全失是固有形态, 故每次 start 后必须重注入. 多容器共享一张表: apply 不带 `--merge` 见别的容器规则即拒 (APPLY-CONFLICT, 译解见 errors.md). whitelist 手工 apply 必须带 `--dns <IP>` (容器实际解析器, 从 `podman exec <容器> cat /etc/resolv.conf` 取, 仅 53 端口放行) — 只放网关在 pasta 拓扑解析不通.

## 沙盒维护中的低开销取证

- 找凭据先沿配置字段指向的来源/仓库/已知配置位置定向查找; 已找到充分证据就停止. 相关仓库/配置目录内可继续定向查找, 不为每个文件都问; 要扩到整个家目录前先说明必要性与范围, 等我决定. 只报告来源与结果, 不回显秘密值.
- 只判断已核实的同一分支是否有新增提交待推时, 先成功取得两端完整提交 ID (例如明确 `refs/heads/feat/example`). ID 相同即可停止, 不为比较再完整克隆/抓历史. 结论仅限该分支提交相同, 不外推其他分支或未提交文件. 查询失败/空输出不能当相同. 确需历史/内容时再取必要数据, 不是全面禁止克隆.
- 截取输出前单独保存原命令退出码, 后续 head/过滤成功不代替它. 已有 swt.run 保留真实 returncode, 不为临时 shell 管道问题重写公共封装. 例如 Bash 中先落临时输出, 再截取 (文件可能含敏感输出, 用私有权限并清理):

```bash
output=$(mktemp) || exit 2
if git ls-remote "$remote" "$branch" >"$output" 2>&1; then
    original_rc=0
else
    original_rc=$?
fi
# 显示前先确认输出不含秘密; 不适合回显时只报告返回码/脱敏摘要.
head -n 20 "$output"
filter_rc=$?
rm -f "$output"
printf 'original_rc=%s filter_rc=%s\n' "$original_rc" "$filter_rc"
exit "$original_rc"
```

原查询 128 即报告失败, 不能因 head 为 0 推断成功或无提交待推. 任务所需的构件/认证/写入检查另按 [task-conditions.md](task-conditions.md), 不把维护取证扩大成项目默认探测.

## 救场 (无通用修复原语)

swt 无 config/daemon 修复子命令. exit 3 的 PARTIAL 文案给出该半状态的唯一人工恢复路径; 更深的救场由你敲原生命令: `git config --get-all` / `git -C <母体> config --worktree --get-all` / `pgrep -af 'git[ -]daemon'` / `net-firewall.py show` / `podman ps -a`, 诊断后手工收敛. 已知救场场景:
- **主仓 config 残留旧形态 hideRefs** (并行母体改造前的旧部署形态) → 不要手工改. 仅旧记录的 resume 沿原有自愈路径迁移配置并重摆该对 daemon; 新模板 birth/resume 遇旧形态残留会报告并停止, 不能靠重跑新模板迁移旧对, 须先向我报告并决定怎么处理.
- **母体 config.worktree 值错误** (birth 报 `git config ... 已有错误值` **exit 2**) → 人工修正该母体的 config.worktree (只许改正 `!refs/heads/<本对分支>` 的例外值), 或 `git -C <母体> config --worktree --unset-all <key>` 清空后重跑 birth. **禁止手工往母体 config.worktree 写任何值**: 开了 `extensions.worktreeConfig` 后, host 侧在某工作树内跑的普通 git 命令会读该工作树的 config.worktree, hideRefs 只影响 serve 行为无害, 但手写其他值会被所有在该工作树内运行的 git 命令读到.
- **孤儿 daemon** (runtime 记录已失但进程在) → 按母体目录精准收: `pkill -f 'git daemon.*<母体目录路径>'` (勿按 base-path 全杀, 会误伤其他对/他仓).
- 显示栈降级/失联: `podman exec <容器名> swt-vnc start` 手动重拉; 深度诊断跑 `swt display-check --name <容器名>` (PPM 证据落 evidence 目录).
真实救场需求暴露时回报我.
