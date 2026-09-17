# 状态: 进行中
# 类型: task
# 阻塞于: MILESTONE-03, MILESTONE-05, MILESTONE-08

## 问题

真机验收 (HITL): 目的地完成判据 — 三类场景 (headed 浏览器 / present 展示 / web 服务) × 两个访问位置 (宿主本机 Wayland 桌面 / 局域网远程 Linux Wayland 设备) 各跑通一次, 全程零手工命令. SKILL.md 记录实证现实.

网页部分按 [M04 账本](../milestone-04/DECISIONS.md) D011 的六项标准验收, 只用改动后新建的容器, 不改造现有容器. present 展示页与可访问的静态网站内容复用现有服务, 不为验收假设必须启动 Vite/Next.js.

设备代开须额外覆盖 D012 的实际条件: 两台设备同时取信时只在本次已确定的设备打开, 用户换设备并更新记录后改在新设备打开. 信件须能定位原容器/会话并回告正确 URL. 核对新容器内实际生效的规则版本, 不能仅以仓库修改或 EXPOSE 声明作为交付证据.

## 验收进度 (2026-09-16, host-exe 停机后由另一会话接管)

前置已落地: 并行母体改造 (同仓多对并存) + cross-host 对迁移 (resume 自愈, 推送落地验证过) + display 层重建 (base 2026.09.15-2 / display 2026.09.15-1, waypipe 0.8.4 + libpulse0 实测在) + 基础服务真机常驻 (systemd user, 38417) + swt-m09-accept 验收容器开出并与 cross-host 并存.

已过:
- 场景 C web 服务: 本机格 ✓ (127.0.0.1:33037, 容器内 present 服务 200) + 远程格 ✓ (工作站浏览器直开 192.168.131.194:33037)
- 场景 B 信箱代开本机格 ✓: 容器投 request 信 → bolo-Yoga 取信会话不信信件字段, 实测查得真实端口 (web 33037 + noVNC 42413) 后 Chrome 代开, 并回告原会话
- 场景 A 窗口直通宿主桌面 ✓: chromium 经 wayland 直通落在宿主桌面 (用户远程确认); 注意: 用户实际远程使用时此格价值有限, 它服务的是 "人坐在 host 前" 的场景
- 多对并存 ✓: 两对同时 born, 各自 daemon/桥/容器, status mothers[] 齐全
- 推送落地 ✓: 容器试推空提交, 母目录 HEAD 即时前进 (fcbec3f); 期间顺带验证了历史分叉时 git 原生拒绝 → fetch 重推 的文档化流程

未过 / 待确认:
- 场景 A 远程格 (waypipe 窗口直飞): **全链已跑通待用户确认** (2026-09-17) — 容器 AI 自治完成 preflight 86 → 投 exec 信 (直批) → 轮询出新 token waypipe-server-3dJUV63k.sock → chromium 带验收页落工作站, 未落 noVNC 兜底, 全程零人工. 解锁前提见实测发现 (方案 B 统一 C 版 + 设备免密自动化)
- 场景 B 远程格: open_url 已重投工作站本机浏览器代开 (2026-09-17, 上次 09-16 的弹窗未获确认), 待用户确认
- D012 双设备定向双投: 依赖工作站取信会话常驻 (已配置且实测在线), 未跑

**waypipe 统一方案 B 已拍板并落地 (2026-09-17)**: 用户选 B (统一 C 版, 否 A=Rust 构建链攻坚). 重建产物: 上游 master 的 minimal_build.sh 在 debian:12 容器跑通 (gcc+libc6-dev+python3, 交互 read 喂回车), 产物 208KB 实测只动态链 libc. 工作站安装: 经信箱 request 信遥控取信会话完成, 遮蔽式装 ~/.local/bin/waypipe (备份 Rust 0.11.0 为 .bak, 不卸原版), 验证输出 "waypipe minimal", 用户已确认. 旧验证容器已删, 产物未留档 (可随时按同法重建).

实测发现 (2026-09-17 增量):
- **设备免密自动化路**: enroll-device-key 需要设备公钥传到 host, 工作站无 ssh 钥匙通道 (host 配置显式 PubkeyAuthentication no). 解法 = 信箱 request 信遥控工作站取信会话: 本机生成专用密钥 → SSH_ASKPASS (REQUIRE=force) + 固定密码 sandbox 免交互 ssh 进容器装公钥 (公钥经 stdin, 不落命令行) → BatchMode 验证. 私钥全程不出工作站, 全自动约 1 分钟, 免 sudo. 容器 authorized_keys 实测新增 workstation-relay 条目
- **容器 pi 母本契约缺口**: agent-prompts/pi_AGENTS.md 的 headed 选路仍是两态 (直通/noVNC), 无 pull-window/信箱编排 — preflight 86 后容器 AI 不知道要投信, 现容器靠任务文本桥接 (实测 AI 读容器内挂载的 SKILL.md 后能正确执行全链). 修补 = 更新母本 (影响新容器) + 母本三份通用核同步纪律, 待办
- **pull-window 全链实测数字**: 信投出→设备取走处理约 1 分钟, waypipe 建连+socket 出现约 70 秒 (含 chromium 启动); 新版 waypipe server 形态: waypipe -c none --unlink-socket -s /tmp/waypipe-server-<token>.sock --display wayland-<token> server <命令>, socket 与 display 名同 token
- 信箱回话送达标准缺失: 取信会话把回话 "打进原会话输入框" 不算送达 (M09 实测) → SKILL.md 已修为两步制 (send-text + 提交键)
- 新版 waypipe 远端命令必须是单条简单命令 (复合命令被其包装机制撕碎); 其 socket 路径与 display 名与旧版不同
- 工作站直连信箱 (38417 裸连) 替代 ssh -L 隧道: 验收采用降级路径, 隧道不通原因未查明 (遗留疑点)
- 新验收容器 /home/bolo/.local/bin 为 root 属主 (podman 单文件挂载自建目录), 同 M14 发现 2 的模式, 若需往该目录放辅助脚本需先修属主

遗留清理项:
- cross-host 容器 pasta 配置与宿主网络失配 (换过网络): 建议 terminate + 重新 birth
- cross-host 分支历史上的验证用空提交 (chore: swt 迁移验证试推 ×2, fcbec3f) — 留作凭证, 可 drop
- 笔记本取信会话 (herdr 窗格 wX:pG, 名 swt-relay) 仍在运行轮询, 为验收基础设施, 不用时可手动关停
- 验收页仍在验收容器 8800 上服务 (宿主 33037 映射), 场景 C 可随时复验
