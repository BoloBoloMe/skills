# 容器操作与救场

换/加容器 provider, 或 swt 编排之外手工收敛时读本文件. 全部容器操作命令集中此处, 换 provider 只改这里.

## 容器命令收拢

- 生命周期: `podman create --name <名> --label ... -p 22 -p 127.0.0.1:6080:6080 (被占时 -p 127.0.0.1::6080) --shm-size=1g -v <records-root>/runtime/<identity>/git-bridge:/run/swt-git -v <母本留档>/<f>_AGENTS.md:<agent 配置路径>/AGENTS.md:ro [-e 继承env] <镜像>` / `podman start|stop|rm -f` (容器不设内存/CPU 上限); auth.json 不走挂载, 启动后 `podman exec -i <容器> sh -c 'install -d -o bolo -g bolo ...; cat > .../auth.json; chown bolo:bolo; chmod 600' < host-auth.json` 注入 (host 缺失则跳过并警告)
- git 通道: host 侧 `socat UNIX-LISTEN:<git-bridge>/git.sock,fork,mode=600 TCP:127.0.0.1:<daemon端口>`; 容器内 `podman exec -d <容器> socat TCP-LISTEN:9418,bind=127.0.0.1,fork,reuseaddr UNIX-CONNECT:/run/swt-git/git.sock`; 桥进程发现: `pgrep -f 'socat.*UNIX-LISTEN:.*git-bridge/git.sock'`
- 本机直通: create 时 `-v <宿主wayland socket>:/run/swt-wayland/wayland-0 -e XDG_RUNTIME_DIR=/run/swt-wayland -e WAYLAND_DISPLAY=wayland-0 [--device /dev/dri]` (宿主机 socket 存在才挂); host 侧 `chmod 0777 <宿主wayland socket>` (birth/resume 重保, 会话重启重置); 禁 socat 中继
- 端口发现: `podman port <容器名>` (22 = ssh, 6080 = noVNC); 状态: `podman ps -a --filter label=sandbox-worktree.repo=<主仓>`
- 镜像: `podman build` / `podman images --filter label=run.sandbox-worktree.project-id=<主仓路径>` / `podman inspect`
- 容器内操作: `podman exec` (key 注入 / swt-vnc start|stop|status / display 检查经 swt-display.py); 防火墙注入: `podman unshare nsenter --net=<容器网络命名空间> nft -f -`
- daemon 发现: `pgrep -f 'git daemon.*<主仓路径>'`

## 网络控制 (net-firewall, 一般由 swt 编排)

正常路径不需要直接调用 — birth/resume/terminate/switch 自动注入与回收. 手救场用:
```text
uv run python scripts/net-firewall.py show                    # 列当前规则表
uv run python scripts/net-firewall.py remove --container-ip <IP>
uv run python scripts/net-firewall.py clear                   # 删整表 (幂等)
```
机制: 规则注入容器所在网络命名空间的自有表 `inet swt`, 按容器源地址限定, 容器内任意 uid (含 root) 不可达不可删. 容器停 → 命名空间拆 → 规则全失是固有形态, 故每次 start 后必须重注入. 多容器共享一张表: apply 不带 `--merge` 见别的容器规则即拒 (APPLY-CONFLICT, 译解见 errors.md).

## 救场 (无修复原语)

swt 无 config/daemon 修复子命令. exit 3 的 PARTIAL 文案给出该半状态的唯一人工恢复路径; 更深的救场由你敲原生命令: `git config --get-all` / `pgrep -f 'git daemon'` / `net-firewall.py show` / `podman ps -a`, 诊断后手工收敛. 已知救场场景:
- **主仓 config 残留旧 hideRefs** (上一次演练/换母体遗留, 指向已删旧分支) → birth 校验拒覆盖 **exit 2** (报 `git config ... 已有错误值`): 手工 `git config --unset-all uploadpack.hideRefs` (如有 receive.hideRefs 残留一并 unset) 后重跑 birth.
- 显示栈降级/失联: `podman exec <容器名> swt-vnc start` 手动重拉; 深度诊断跑 `swt display-check --name <容器名>` (PPM 证据落 evidence 目录).
真实救场需求暴露时回报我.
