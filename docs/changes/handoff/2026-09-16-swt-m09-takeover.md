# 交接: swt 并行母体改造落地 + M09 真机验收接管 (2026-09-16)

上一会话 (herdr 标签 host-fix-do, 窗格 wX:pD) 的完整交接. 用户偏好: 大白话沟通 (wtf skill 已两次触发), 授权 agent 在其拍板框架内代行决策 ("你来决定怎么做吧" 模式).

## 路线图 (用户真实意图脉络)

1. 实施 `docs/changes/swt-multi-mother/2026-09-13-proposal.md` (并行母体改造) → **已完成**, commit f33f4e1; 开放写单位从主仓下沉到母体工作树, switch 子命令删除, STATE schema 2 + mothers[], identity 按对派生 (旧 scheme 兼容铁律落实, skills-v2-71170aeb 原地沿用).
2. 子代理冷审 → **已完成**: 审出 4 问题 (retired 残留 terminate 回归 / 双 daemon 孤儿 / 迁移中断重跑翻倍 / 预检缺 worktreeConfig 探测), 全部修复 (fa64b93), 第二轮复审确认对症无新问题.
3. 真机迁移 cross-host 对 (旧形态 → per-mother) → **已完成**: 用户确认 DECIDE 后 resume 自愈成功, 推送落地实测 (容器试推空提交, 母目录 HEAD 即时前进至 fcbec3f).
4. 解锁 host-exe 会话 (其卡在 "一母体一容器" 旧约束) → **已完成**: 告知改造落地, host-exe 自行开出 m09-accept 验收对 (并行母体首次生产验证).
5. 接管 host-exe 的 M09 真机验收 (其 kimi 用量耗尽) → **进行中**, 进度账本见必读推荐 1. 已过: 场景 C 本机+远程, 场景 B 本机 (信箱全链路: 容器投信→取信会话实测查端口→Chrome 代开→回告), 场景 A 本机 (wayland 直通窗口落宿主桌面), 多对并存, 迁移, 推送落地. 未过: B 远程 (open_url 信已定向投到工作站, 设备弹窗未获用户确认), A 远程 (见下), D012 双设备定向双投 (就绪未跑).
6. **悬而未决 (用户尚未拍板)**: waypipe 统一方案. 背景: 工作站 (Ubuntu-Workstation) waypipe 0.11.0 为 Rust 新实现 (反向隧道拓扑), 容器 0.8.4 为 C 旧实现 (stdio 拓扑), 互不兼容 (客户端在其监听通道读握手头即 EOF, src/main.rs:709). 已排除: 容器升 0.11.2 C 版 (waypipe-c, 拓扑仍不同). 方案 A = 统一 Rust 版, 需重建 display 镜像, 其构建链 (cargo + bindgen CLI + glslc + wrap-* 生成器) 在 debian:12 连环失败, 未走通; 方案 B = 统一 C 版, 上游 minimal_build.sh 纯 gcc+python3 兜底构建已在 debian:12 容器内验证跑通 (产物 build-minimal/waypipe-c, libc-only 可跨发行版, 特性协商降级无视频/加速), 尚未分发给工作站. 用户叫停攻坚, 拍板待续.

## 环境现状 (其他文档未记)

- 双对 runtime: `~/.agents/sandbox-worktree/runtime/skills-v2-71170aeb.json` (cross-host, ssh 端口 35625) 与 `skills-v2-dc145395.json` (swt-m09-accept, ssh 42947, web 映射 33037, display ok). 两对同时 born, daemon 各自独立.
- 验收页仍在 m09-accept 容器 8800 服务 (宿主回环 33037 与局域网 192.168.131.194:33037 均 200), 页面源在容器内 /home/bolo/Workspace/m09-accept/accept-page/.
- 笔记本取信会话仍在轮询: herdr 窗格 wX:pG, agent 名 swt-relay, glm-5.3-flash; 不用时可关停.
- 工作站已配置: 信箱扩展两件 + ~/.config/swt/mailbox.json (直连 http://192.168.131.194:38417, 设备名 Ubuntu-Workstation; 凭证为敏感值, 见该文件, 勿入档); pi 0.85.1 + waypipe 0.11.0 已装; 其取信会话曾成功连上信箱. 工作站会话类型为 wayland (已实测), ssh 到 host 仅密码认证 (host ~/.ssh/config: office-ubuntu-workstation).
- 基础服务 (信箱+LLM 中转) 已 systemd user 常驻, 38417/38416 在线; admin 凭证读 ~/.local/state/swt-base-server/state.json (敏感).
- herdr 标签: host(t2) / host-exe(t7, kimi 已耗尽配额闲置) / sandbox(t9) / host-fix(tB) / host-fix-do(tC, 本会话) / S-reviewer-1(tD, 冷审会话闲置可关) / 新交接会话.
- 分支 swt-cross-host-access 近期提交 (新会话工作基底): f33f4e1 改造主体, fa64b93 冷审修复, dbb7c7d 回话两步制, 4aa5f23 display-check PYTHONPATH 修复 (host-exe), 3d5fe28 M09 账本; fcbec3f 为验证用空提交 (留档可 drop).
- 测试基线: tests/test_swt_m12.py 96 项全绿; m04/m07/m09 存量失败为环境漂移且原树同败, 与本轮无关 (详见 M09 账本).

## 本轮实测发现 (已固化, 避免重踩)

- 信箱回话送达标准: 把回话打进对方输入框不算送达, 必须 send-text+提交键两步 (SKILL.md 已修).
- 新版 waypipe: 远端命令必须单条简单命令 (复合命令被其 `waypipe --unlink-socket ... server` 包装撕碎); socket 落 /tmp/waypipe-server-*.sock, display 名随机后缀.
- 容器 /home/bolo/.local/bin 为 root 属主 (podman 单文件挂载自建目录, M14 发现 2 同款), 需放脚本时先修属主或另择目录.
- 工作站直连信箱 38417 (裸连+签名, 降级路径) 替代 ssh -L 隧道; 隧道不通原因未查明 (疑似首次连接的隐藏 hostkey/密码确认), 已记遗留疑点.
- 容器 ssh 会话环境: XDG_RUNTIME_DIR=/tmp/xdg-1001 (sshd SetEnv) 与烘死的 WAYLAND_DISPLAY=wayland-0 组合指向不存在的 socket — 本机直通场景需显式 XDG_RUNTIME_DIR=/run/swt-wayland 启动.

## 遗留清理项 (均为状态描述, 非指派)

- cross-host 容器 pasta 配置与宿主网络失配 (宿主换过网络): 建议 terminate + 重新 birth.
- 工作站 ssh -L 隧道不通原因未查明 (已用直连绕过).
- 两代 waypipe 并存的长期策略待用户拍板 (见路线图 6).

## 必读推荐

1. `docs/changes/swt-cross-host-access/roadmap/MILESTONE-09.md` — M09 验收进度账本 (已过/受阻/实测发现/遗留清理项的权威清单), 本文档只写其增量.
2. `workflow/use-sandbox-worktree/SKILL.md` — 沙盒操作手册与信箱协议; 含本轮修的 "回话两步制" 与设备协作节; 驱动验收/投信/waypipe 流程前必读.
3. `docs/changes/swt-multi-mother/2026-09-13-proposal.md` — 并行母体改造方案全文 + 附录 C 实施记录 (与本轮相关的兼容铁律与迁移机制).
4. `workflow/use-sandbox-worktree/scripts/swt.py` — 生命周期脚本本体; 多对并存下 runtime 定位 (locate_pair_runtime / resolve_pair_identity) 与迁移 (migrate_legacy_pairs) 的实现细节在此.
5. `tests/test_swt_m12.py` — 96 项生命周期测试与夹具约定 (lan-address 预写, pair_runtime_path 定位), 改 swt.py 前必读.
