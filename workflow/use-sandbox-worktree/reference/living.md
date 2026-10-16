# 容器存续时的使用说明

只有我需要接入正在运行的容器, 审阅母体, 或排查展示/登录窗口时读本文件. host 侧 agent 负责接入和转交, 具体编码工作由容器内 pi 完成, 避免误把母体当成可写开发目录.

- **母体审阅**: 母体目录是容器 push 后的审阅现场. 可只读查看 diff/试跑, 保持跟踪文件不变: 母体工作区脏会拒容器 push; 未跟踪文件不阻塞. 不在母体使用会自动修改文件的工具. 容器成果以快进 `git push` 为准, 落地后文件有秒级短延迟.
- **SSH 与 Herdr**: birth 在 SSH 就绪后把容器登记为宿主 Herdr 的 machine, 直接从侧栏选择容器名. agent 控制前读 `use-herdr` 的 `machine.md`, 命令统一带 `--machine <记录中的id>`, 先在该远端重新发现 pane/agent ID; 不把宿主 ID/`--current` 当远端 ID. 旧容器未登记时用 birth 重入/resume 补登记, status/list 不做写入. 普通 SSH 仍可用交付包入口与私钥. 委派先确认远端 agent idle, pi 提交键取容器内 keybindings, 无则 alt+enter. 窗格输入无任务 id/退出码/重试保证, 需要确定性结果时用 `pi -p "<任务>"` 批处理.
- **向 host 发信**: 容器生成提示词/`~/docs/identity.md` 记有创建者 host 会话 sessionId, 用 mailbox 定向发送; 宿主当前会话在交付前开启持续取信. 两边 sessionId 是否一致要核对, 不把恢复容器等同于改写原回信地址. 多个 host 会话并行收信正常, 不互相接管或共用取信状态.
- **web 展示**: 容器内展示由 `present` skill 的容器分支负责. host 将容器 8800-8805 发布到宿主 0.0.0.0 动态端口 (局域网直达, 无认证), 8800 给 present, 8801 起给 navigate 等按需服务; `STATE.web-port` 是 8800 的宿主端口, `web-port-2`..`web-port-6` 对应 8801-8805. 交付包只列 8800. `present` 在容器内用 `start 8800 <root> --bind 0.0.0.0 --fixed-port`, 多页复用同一服务. birth/resume 与 status 对运行中容器直接输出 web 双 URL, 停止时 status 不附 URL, 查 STATE/`podman port <容器名> <端口>`. 容器内可用 `SWT_HOST_WEB_PORT`/`SWT_HOST_WEB_PORT_2`..`_6` 和 `SWT_HOST_LAN_IP` 组 URL; 已确认地址缺席时通过可用信箱问宿主会话, 否则问我, 不猜.
- **显示栈**: VNC 来自 display 镜像, 含 Xvfb/x11vnc/websockify/noVNC/chromium; 6080 仅发布到宿主 127.0.0.1, 与 web 口的局域网公开不同. birth 跑全量显示检查, 失败出 DECIDE (继续只开终端/重验/终结); resume 只做秒级检查, 显示失败降级但不阻断终端. 手动拉起用 `podman exec <容器名> swt-vnc start|stop|status`; 深度诊断 `uv run python scripts/swt.py display-check [--name <容器>]` (退出 0 全过, 1 检查未过, 2 传输失败, 不走 DECIDE/STATE). 旧镜像没有 swt-vnc 时标 absent, 不算失败. 浏览器登录态留在容器 /tmp, stop/start 保留, rm 消失.
- **登录窗口**: 在本机有桌面时 headed 浏览器优先宿主 wayland 直通, 失败回退 `DISPLAY=:99` noVNC; 在远程设备需用 waypipe 拉窗时, 容器侧与设备侧的做法见 [pull-window.md](pull-window.md). headed 启动脚本不存在时只用 noVNC/终端, 报告缺席原因. 宿主直通的挂载/权限与风险由 [ops.md](ops.md) 的本机直通段和 [risks.md](risks.md) 说明.
- **旧容器 Kimi 登录**: 新模板使用固定客户端 Key, 不需 `/login`. 旧容器需独立登录 Kimi OAuth, 不能复制 host 凭据共用: refresh token 轮换后先刷新者生效, 另一端会 invalid grant; 旧 resume 不加新模板.
- **多对**: 不同母体各自配 daemon/容器, 容器只见本对分支. 历史残留的多容器同推一个母体时, 后推若因分叉被拒, 在容器内 fetch/解冲突/重推; 快进推送由 git 串行化.
