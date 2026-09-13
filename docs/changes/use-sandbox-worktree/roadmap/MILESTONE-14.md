# 状态: 已关闭 (2026-09-13: 三项修复 + 测试落地, m04 14 / m07 35 / m09 26 / m12 102 全绿; 展示端口项移交 swt-cross-host-access M05)
# 类型: task
# 阻塞于: 无 (MILESTONE-10 已关闭后路由)

## 问题

M10 终轮全链演练 (见 [../milestone-10-full-chain-run.md](../milestone-10-full-chain-run.md)) 暴露的代码侧缺陷集中修复, 共四项:

1. **母本挂载父目录根修** (发现 2): birth/resume 挂 agent 母本单文件时, 逐个 `install -d -o bolo -g bolo` 保证目标父目录存在且 bolo 属主 (与 D046 注入同模式). 现存实例: kimi-code 的 `~/.kimi-code` (每回必现 EACCES); 结构性防未来新 agent 母本再踩.
2. **展示链端口预留** (发现 5, D053 已拍板): swt create 预留展示端口映射 (回环), present 容器分支复用该端口; SKILL.md 存续节展示链段与 present skill 容器分支同步更新. 注意端口 create 时钉死, 实现后须重建容器生效.
   - **2026-09-14 移交**: 本项移交 swt-cross-host-access MILESTONE-05 — 用户拍板 web 端口 0.0.0.0 直达局域网 (含分享给同事场景), 双地址可达天然覆盖回环需求; D053 已标替代. 本 Milestone 缩为三项 (1/3/4).
3. **局域网入口 IP 选取** (发现 4): birth/resume 交付的局域网入口取默认路由接口地址, VPN (tun0) 在场时取错 (交付了 tun0 地址). 应选 LAN 口地址或两址并列标注.
4. **swt-vnc status 以 bolo 身份误报** (发现 7, 轻微): 栈由 root 拉起时 bolo 跑 status, `kill -0` 吃 EPERM 误报 down 而端口检查显示 listening, 输出自相矛盾.

## 完成判据

- 四项各有修复 + 测试 (m12/m09 回归绿).
- kimi 根修后: 新 birth 的容器内 `kimi` 直接可起 (不再 EACCES).
- 展示端口实现后: 容器内 present 起服, host 侧 `podman port` 发现映射端口组装 URL 可点开 (端到端复验一次).
- SKILL.md 与实现字面一致.

## 关闭记录 (2026-09-13)

- 发现 2 (母本挂载父目录): swt.py 新增 `ensure_agent_prompt_parents` (birth 启动后 `install -d -o bolo -g bolo` 逐父目录, 与 D046 同模式); m12 TS201 扩断言 (三个挂载点父目录 bolo 可写) 绿.
- 发现 4 (局域网 IP): lan_ip 改枚举全局 IPv4 排除隧道/虚拟接口前缀, 兜底回原口径 (F022); 4 个 mock 单测绿 (先红后绿).
- 发现 7 (swt-vnc status 误报): alive() 存活判定改 /proc 存在性 (F021); m09 新增 bolo 身份 status 用例绿.
- 回归: m04 14 / m07 35 / m09 26 / m12 102 全绿 (2026-09-13).
- 真实镜像已重建携带修复 (网络恢复后重跑成功): display:2026.09.13-5 + skills:2026.09.13-3, match=REUSE 指向新链, swt-vnc 新版已验证; 被取代的 -2 旧镜像已清.
- 移交项: 展示端口预留 → swt-cross-host-access M05 (D053 已标替代).
- 测试基建提速另立 MILESTONE-15 (优先级最高).
