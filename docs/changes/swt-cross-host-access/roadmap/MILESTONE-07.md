# 状态: 待处理
# 类型: task
# 阻塞于: MILESTONE-06

## 问题

双机实测 (HITL, 须用户设备在场). 必测清单 (据 [recon/03](../recon/03-waypipe.md) 3.4 + 6):

1. 音频 ssh -R unix 形态端到端出声
2. 设备侧 PipeWire 对同 uid unix 连接的认证行为
3. sshd 转发 socket 容器内权限/属主 (rootless uid_map 呈现)
4. StreamLocalBindUnlink 缺省行为 (断线残留挡重建) + 加 directive 后生效
5. waypipe ssh 与用户 -R 并存端到端
6. 容器 0.8.2 与设备侧实际版本的跨版本兼容
7. pulse 过 ssh 隧道的延迟/抗抖动主观评价
8. (若采纳 c3) 常驻隧道 + 容器内按需 server 端到端
