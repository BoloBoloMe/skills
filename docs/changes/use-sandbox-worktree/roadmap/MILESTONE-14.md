# 状态: 开放
# 类型: task
# 阻塞于: 无 (MILESTONE-10 已关闭后路由)

## 问题

M10 终轮全链演练 (见 [../milestone-10-full-chain-run.md](../milestone-10-full-chain-run.md)) 暴露的代码侧缺陷集中修复, 共四项:

1. **母本挂载父目录根修** (发现 2): birth/resume 挂 agent 母本单文件时, 逐个 `install -d -o bolo -g bolo` 保证目标父目录存在且 bolo 属主 (与 D046 注入同模式). 现存实例: kimi-code 的 `~/.kimi-code` (每回必现 EACCES); 结构性防未来新 agent 母本再踩.
2. **展示链端口预留** (发现 5, D053 已拍板): swt create 预留展示端口映射 (回环), present 容器分支复用该端口; SKILL.md 存续节展示链段与 present skill 容器分支同步更新. 注意端口 create 时钉死, 实现后须重建容器生效.
3. **局域网入口 IP 选取** (发现 4): birth/resume 交付的局域网入口取默认路由接口地址, VPN (tun0) 在场时取错 (交付了 tun0 地址). 应选 LAN 口地址或两址并列标注.
4. **swt-vnc status 以 bolo 身份误报** (发现 7, 轻微): 栈由 root 拉起时 bolo 跑 status, `kill -0` 吃 EPERM 误报 down 而端口检查显示 listening, 输出自相矛盾.

## 完成判据

- 四项各有修复 + 测试 (m12/m09 回归绿).
- kimi 根修后: 新 birth 的容器内 `kimi` 直接可起 (不再 EACCES).
- 展示端口实现后: 容器内 present 起服, host 侧 `podman port` 发现映射端口组装 URL 可点开 (端到端复验一次).
- SKILL.md 与实现字面一致.
