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

未过 / 受阻:
- 场景 B 远程格: open_url 信已定向投到 Ubuntu-Workstation (投递正确, 笔记本侧取信会话保持沉默, D012 定向的一半证据), 但设备侧代开未获用户确认 — 补一次确认即过
- 场景 A 远程格 (waypipe 窗口直飞): 受阻于 **waypipe 世代分裂** — 工作站 0.11.0 为 Rust 新实现 (反向隧道拓扑, socket 建在 /tmp/waypipe-server-*.sock), 容器 0.8.4 为 C 旧实现 (stdio 拓扑), 客户端在其监听通道上读握手头即 EOF. 已试并排除: 容器升 0.11.2 C 版 (waypipe-c, 拓扑仍不同, 同错). Rust 版构建链 (cargo + bindgen + glslc + wrap-* 系列) 在 debian:12 上连环踩坑未走通. 待决策: 统一以哪一族为标准后重测 — 若定 Rust, display 层重建时一并解决构建链; 若定 C, 工作站需装 C 版 (minimal 构建二进制 libc-only, 可跨发行版)
- D012 双设备定向双投: 依赖工作站取信会话常驻 (已配置: 凭证/扩展/直连 38417; 工作站走直连降级路径, ssh -L 隧道未通原因已记遗留疑点), 未跑

实测发现:
- 信箱回话送达标准缺失: 取信会话把回话 "打进原会话输入框" 不算送达 (M09 实测) → SKILL.md 已修为两步制 (send-text + 提交键)
- 新版 waypipe 远端命令必须是单条简单命令 (复合命令被其包装机制撕碎); 其 socket 路径与 display 名与旧版不同
- 工作站直连信箱 (38417 裸连) 替代 ssh -L 隧道: 验收采用降级路径, 隧道不通原因未查明 (遗留疑点)
- 新验收容器 /home/bolo/.local/bin 为 root 属主 (podman 单文件挂载自建目录), 同 M14 发现 2 的模式, 若需往该目录放辅助脚本需先修属主

遗留清理项:
- cross-host 容器 pasta 配置与宿主网络失配 (换过网络): 建议 terminate + 重新 birth
- cross-host 分支历史上的验证用空提交 (chore: swt 迁移验证试推 ×2, fcbec3f) — 留作凭证, 可 drop
- 笔记本取信会话 (herdr 窗格 wX:pG, 名 swt-relay) 仍在运行轮询, 为验收基础设施, 不用时可手动关停
- 验收页仍在验收容器 8800 上服务 (宿主 33037 映射), 场景 C 可随时复验
