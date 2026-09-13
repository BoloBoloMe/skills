# MILESTONE-10 全链演练报告 (终轮)

日期: 2026-09-13. 性质: M10 验收 — SKILL.md 定稿核对 + 全链从零演练 (旧演练现场不复用). 网络模式: blacklist 无 --deny (用户拍板). 宿主环境: 演练中途宿主开启 VPN (tun0), 影响了部分观察 (见发现 4).

## 链路与结果

| 环节 | 结果 | 证据 |
| --- | --- | --- |
| 镜像从零制备 | ✓ | 用户拍板删三层镜像重建: base:2026.09.13-3 → display:2026.09.13-2 → skills:2026.09.13-2; match=REUSE; contents.md 实测 codex 0.154.0 / kimi-code 0.42.0 / codex-config 在位 |
| 建 (birth) | ✓ (经一次显示栈失败-修复-重建, 见发现 1) | 母体 `skills-v2-skill-improvement` 经 use-worktree 第零步建立; DECIDE mother-reuse/hostname 正常开出与消费; 第二轮 birth exit 0, display=ok, host-display=ok |
| 干 (用户 ssh 实操) | ✓ | 用户 ssh 进容器驱动容器内 llm 做真实 skill 改进, 6 提交 (e24551f access-web headed 最大化 / 609ef23 推送纪律 / a16eb9d probe 单一真相源 等) |
| 回流 (ff-push 落地母体) | ✓ | 容器 HEAD = 母体 tip = a16eb9d; 母体工作区推送落地即时更新且干净; 容器无未提交/未 push/未落后; 后已合流 v2 (merge commit 92713f5, 一处冲突人工解开) |
| 展示链 | ✓ 降级形态 | present 容器分支因无可用映射端口走失败出口 (见发现 5); 文件经既有 ssh 通道拉回 host 交付, 用户可看; 固定形态已拍板 A (见发现 5) |
| 登录墙 | ✓ | 容器内 headed chromium `--ozone-platform=wayland` 起 30 进程零 fatal, 窗口弹宿主机桌面, 用户亲眼确认 |
| 拆 (terminate) | ✓ | exit 0 无 DECIDE (容器干净); 容器/daemon/nft 全灭, 母体与主仓 config 原样保留, 本次容器凭证已清除; 顺带清理上轮遗留的旧容器凭证 (swt-skill-optimization.*) |

SKILL.md 定稿核对: 五子命令 + display-check + 全部 flag 与 swt.py 接口一致; image-prep 四子命令一致; reference/ 三文件与 agent-prompts/ 三母本在场. 发现 6 条文档/实现出入与缺陷, 见下.

## 演练发现 (按严重度)

1. **[已修复并验证] x11vnc 与 D051 wayland 环境变量冲突**: x11vnc 0.9.16 探测到 WAYLAND_DISPLAY 即误判 wayland 会话退出 ("Wayland display server detected... Exiting"), 有直通的容器 noVNC 兜底链必断 — D051 "VNC 保留兜底" 实际不成立. 修复: swt-vnc 启动 x11vnc 时 `env -u WAYLAND_DISPLAY -u XDG_RUNTIME_DIR`; 已提交 v2 (aaf1572), display+项目层镜像重建, 重 birth 后 display=ok. 是 M13 引入的真回归, 被本轮演练抓获.
2. **[待根修] kimi-code 母本挂载点父目录 root 属主**: `~/.kimi-code` 镜像内不存在, podman 为单文件挂载自动建的父目录 root 属主, 容器内 kimi 起步即 EACCES (`tui.toml` 写不了). 每回必现, 结构性. 本轮热修 (chown) 验证有效. 排查确认 swt.py 全部挂载点中现存仅此一处 (git 桥消费者是 root; wayland socket 0777 已覆盖; pi/codex 父目录镜像内已有), 注入通道 (auth.json/authorized_keys) 写法正确. 根修方案: swt.py 挂母本时逐个 `install -d -o bolo -g bolo` 保证父目录 (与 D046 注入同模式, 镜像无关, 防未来新 agent 再踩).
3. **[文档/实现二改一] 容器代码路径**: SKILL.md 写 "代码固定克隆在 /home/bolo/Workspace/<母体目录名> (与 host 母体路径字面一致)", 实现 (swt.py:1593) 实为 `/home/bolo/Workspace/<分支名>` (本轮 = skill-improvement, 非 skills-v2-skill-improvement).
4. **[实现缺陷] 局域网入口 IP 取默认路由接口**: birth 交付的局域网入口取到 tun0 地址 (192.168.216.53), 局域网机器够不着; 正确值是 LAN 口 192.168.31.252. VPN 在场即错. F017 的邻近问题.
5. **[设计缺口已拍板] 展示链无可用映射端口**: swt 只映射 22+6080, present 容器分支要求 "复用已映射端口" (M08 假设), 22 被 sshd 占, 6080 被 noVNC 占 → web 交付结构性走不通. F 轮挂账的 known gap 本轮实锤. 用户已拍板 **选项 A: swt create 预留展示端口映射** (回环), present 容器分支复用. 注: 端口 create 时钉死, 须重建容器生效.
6. **[文档/实现二改一] image-prep `--requirements`**: SKILL.md 标可选 (方括号), 实现 match/build 必填 (裸跑报 `REQUIREMENTS-REQUIRED --requirements <file>`).
7. **[轻微] swt-vnc status 以 bolo 身份误报 down**: 显示栈由 birth 经 podman exec (root) 拉起, bolo 跑 status 时 `kill -0` 吃 EPERM 判 down, 但端口检查正确显示 listening — 输出自相矛盾. 文档路径 (podman exec) 正常.

## 簿记与遗留 (收尾后状态)

- DECISIONS.md 已补: F020 (x11vnc×wayland 冲突实测, 已修 aaf1572) / D053 (展示链固定形态 = 预留展示端口, 用户拍板).
- 文档出入已修 (SKILL.md): 发现 3 (容器代码路径 = 分支名) 与发现 6 (image-prep 直用 --requirements 必填) 均按改文档落地.
- 代码侧 4 项已路由 [MILESTONE-14](roadmap/MILESTONE-14.md): 发现 2 根修 / 发现 5 (D053) 实现 / 发现 4 / 发现 7.
- 母体 `skills-v2-skill-improvement` 与分支 skill-improvement: 确认全部合流 v2 (merge 92713f5) 后已删 (worktree remove + prune + branch -d).
- `sync-to-pi.py` 与 push origin: 用户自执行.
- M09 挂起的 3840 疑点: 本轮未复现.
- MILESTONE-13 已据本轮实证关闭 (用户拍板 2026-09-13; fcitx 中文输入未单独验).
