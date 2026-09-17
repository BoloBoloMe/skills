# 状态: 已完成 (2026-09-17)
# 类型: task
# 前置: MILESTONE-03, MILESTONE-05, MILESTONE-08 (均已过)

## 问题

真机验收 (HITL): 目的地完成判据 — 三类场景 (headed 浏览器 / present 展示 / web 服务) × 两个访问位置 (宿主本机 Wayland 桌面 / 局域网远程 Linux Wayland 设备) 各跑通一次, 全程零手工命令. SKILL.md 记录实证现实.

网页部分按 [M04 账本](../milestone-04/DECISIONS.md) D011 的六项标准验收, 只用改动后新建的容器, 不改造现有容器. present 展示页与可访问的静态网站内容复用现有服务, 不为验收假设必须启动 Vite/Next.js.

设备代开须额外覆盖 D012 的实际条件: 两台设备同时取信时只在本次已确定的设备打开, 用户换设备并更新记录后改在新设备打开. 信件须能定位原容器/会话并回告正确 URL. 核对新容器内实际生效的规则版本, 不能仅以仓库修改或 EXPOSE 声明作为交付证据.

## 验收结论 (2026-09-17 全部通过, 用户逐格亲眼确认)

前置已落地: 并行母体改造 (同仓多对并存) + cross-host 对迁移 (resume 自愈, 推送落地验证过) + display 层重建 (base 2026.09.15-2 / display 2026.09.15-1, waypipe 0.8.4 + libpulse0 实测在) + 基础服务真机常驻 (systemd user, 38417) + swt-m09-accept 验收容器开出并与 cross-host 并存.

- 场景 C web 服务: 本机格 ✓ (127.0.0.1:33037, 容器内 present 服务 200) + 远程格 ✓ (工作站浏览器直开 192.168.131.194:33037)
- 场景 B 信箱代开: 本机格 ✓ (容器投 request 信 → bolo-Yoga 取信会话实测查得真实端口后 Chrome 代开并回告) + 远程格 ✓ (open_url 定向投 Ubuntu-Workstation, 设备本机浏览器代开, 用户确认; 09-16 首投未获确认, 09-17 重投两轮均确认)
- 场景 A 窗口展示: 本机格 ✓ (chromium 经 wayland 直通落宿主桌面) + 远程格 ✓ (waypipe 窗口直飞工作站, 全链零人工, 详见下)
- 多对并存 ✓: 两对同时 born, 各自 daemon/桥/容器, status mothers[] 齐全
- 推送落地 ✓: 容器试推空提交, 母目录 HEAD 即时前进 (fcbec3f); 顺带验证历史分叉时 git 原生拒绝 → fetch 重推 的文档化流程
- D012 双设备定向双投 ✓ (2026-09-17): 两台设备同时在线轮询. 第一轮 open_url to=bolo-Yoga → 仅笔记本代开 (Chrome 实际建立连接, 取信会话核实过); 容器 AI 被告知换设备后更新记录, 第二轮 to=Ubuntu-Workstation → 仅工作站代开 (用户确认). 机制核对: 服务端 _deliverable 对显式 to 硬过滤 (`to == dev.name`), 信一经投递出 queued 即不可再投, 串门在协议层不可能

### 场景 A 远程格攻关记录 (2026-09-17)

1. **waypipe 世代分裂 (前一会话遗留阻塞) → 方案 B 拍板并落地**: 用户选 B (统一 C 版, 否 A=Rust 构建链攻坚). 上游 master 的 minimal_build.sh 在 debian:12 容器跑通 (gcc+libc6-dev+python3, 交互 read 喂回车), 产物 208KB 实测只动态链 libc. 经信箱 request 信遥控工作站取信会话安装: 遮蔽式装 ~/.local/bin/waypipe (备份 Rust 0.11.0 为 .bak, 不卸原版), 验证输出 "waypipe minimal", 用户确认. 旧验证容器已删, 产物未留档 (可按同法重建).
2. **设备免密自动化**: enroll-device-key 的公钥传递环节用信箱遥控替代人工 — 工作站本机生成专用密钥 → SSH_ASKPASS (REQUIRE=force) + 固定密码 sandbox 免交互 ssh 进容器装公钥 (公钥经 stdin, 不落命令行) → BatchMode 验证. 私钥全程不出工作站, 约 1 分钟, 免 sudo. 容器 authorized_keys 实测新增 workstation-relay 条目.
3. **首跑暴露隐形窗口**: socket token 出现 + AI 汇报成功, 但用户端只见任务栏图标无可见窗口 — token 只证明会话建立, 证明不了可见渲染. 病根: chromium GPU/dmabuf 缓冲过不了 minimal C 版 waypipe 通道. 修复: 拉窗命令追加 `--disable-gpu --disable-gpu-compositing` (软件渲染), 用户确认可见. 次要修复: 拉窗命令直接附带页面 URL (--no-first-run --no-default-browser-check --start-maximized), 不依赖容器 AI 事后导航 — 实测 AI 导航不可靠且曾误用局域网映射地址 (容器内访问 host LAN IP 的已发布端口被拒, hairpin 不通; 容器内页面地址只有 127.0.0.1:8800).
4. **终跑通过**: 清场 (旧会话/死壳/浏览器档案) 后容器 AI 全套自治: preflight 86 → exec 信直批 → 轮询新 token → 软件渲染窗口带页面落工作站, 全程零人工零兜底. 死壳容忍 (新 token 差集判定) 在真实环境验证通过.

## 实测发现 (实证现实, 已回填 SKILL.md/swt.py/母本)

- **跨网窗口必须软件渲染**: minimal C 版 waypipe 无视频/加速通道, chromium 默认 GPU 路径产出不可见窗口 (任务栏有图标, 无画面). 设备侧拉窗模板已加 `--disable-gpu --disable-gpu-compositing --no-first-run --no-default-browser-check --start-maximized` (SKILL.md 窗口直飞节 + swt.py headed_delivery_lines).
- **页面 URL 随拉窗命令附带**: 容器 AI 事后导航不可靠 (且容器内禁用局域网映射地址, hairpin 拒连); URL 由前置编排写进设备侧拉窗模板. 通用化的 URL 传递机制 (exec 信形状锁死, 无 URL 字段) 是遗留设计题, 不阻塞使用.
- **socket token ≠ 窗口可见**: 拉窗成功判据若要严格到用户可见, 需设备侧回执或人眼确认; 现行 token 判据保证会话建立, 可见性由模板修复保障.
- **设备免密自动化路**: enroll-device-key 需要设备公钥传到 host, 工作站无 ssh 钥匙通道 (host 配置显式 PubkeyAuthentication no). 信箱 request 信遥控取信会话完成密钥生成+SSH_ASKPASS 免交互安装+BatchMode 验证, 全自动. 私钥不出设备.
- **容器 pi 母本契约缺口 (已修)**: agent-prompts 三母本的 headed 选路原为两态 (直通/noVNC), 无 pull-window/信箱编排 — 86 后容器 AI 不知道要投信, 现容器靠任务文本桥接 (AI 读容器内挂载的 SKILL.md 后能正确执行全链, 本次验收即如此). 母本已补三态选路 + 86 投信指针, 只影响新 birth 容器.
- **pull-window 全链实测数字**: exec 信投出→设备取走处理约 1 分钟, waypipe 建连+窗口落屏约 70 秒 (含 chromium 启动); C 版 waypipe server 形态: `waypipe -c none --unlink-socket -s /tmp/waypipe-server-<token>.sock --display wayland-<token> server <命令>`, socket 与 display 名同 token.
- **设备侧代开的健壮性**: bolo-Yoga 取信会话实测 xdg-open 静默失败后自行换显式 chrome 命令重试并核实连接 — 设备侧 AI 的 "不信信件字段, 实测核实" 纪律有效.
- **死壳容忍实测**: 异常死亡会话残留 /tmp/waypipe-server-*.sock, 新拉窗只看 token 差集, 残壳不挡判定 (UD-12/N2 在真实环境验证).
- 信箱回话送达标准: 把回话 "打进原会话输入框" 不算送达 → SKILL.md 已修为两步制 (send-text + 提交键).
- 新版 waypipe 远端命令必须是单条简单命令 (复合命令被其包装机制撕碎).
- 工作站直连信箱 (38417 裸连) 替代 ssh -L 隧道: 验收采用降级路径, 隧道不通原因未查明 (遗留疑点).
- 新验收容器 /home/bolo/.local/bin 为 root 属主 (podman 单文件挂载自建目录), 同 M14 发现 2 的模式.

## 遗留清理项 (均为状态描述, 非指派)

- 母本修补只影响新 birth 容器: 现役 m09-accept 容器仍是两态契约, 跨网拉窗靠任务文本桥接; 下次重建容器自然携带新母本.
- 通用化的 "页面 URL 传递到飞窗" 设计题: 现行靠前置编排把 URL 写进设备侧拉窗模板, 若未来 exec 信指令集扩展可考虑携带 URL 字段 (安全评审照旧).
- cross-host 容器 pasta 配置与宿主网络失配 (换过网络): 建议 terminate + 重新 birth.
- cross-host 分支历史上的验证用空提交 (fcbec3f) — 留作凭证, 可 drop.
- 笔记本取信会话 (herdr 窗格 wX:pG, 名 swt-relay) 与工作站取信会话为设备基础设施, 闲置时人工关停.
- 验收页仍在验收容器 8800 上服务 (宿主 33037 映射), 可随时复验.
- 工作站 ssh -L 隧道不通原因未查明 (已用直连绕过).
