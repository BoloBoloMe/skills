# 状态: 待处理
# 类型: prototype
# 阻塞于: MILESTONE-01

## 问题

信箱通道粗糙原型: pi 扩展 (watcher/timer + triggerTurn 自循环) + 容器内文件队列 + 设备侧经 ssh 拉取, 与用户做一轮真跑, 验证 "pop→处理→pop 常驻循环" 的实际手感 (延迟/成本/herdr 咬合), 提升后续实施保真度.

依据: [recon/01](../recon/01-llm-channel.md) 考察点 1 (能力面) 与遗留疑问 (容器内 reply 注入的生命周期需实测).
