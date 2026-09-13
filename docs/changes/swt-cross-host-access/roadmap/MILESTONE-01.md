# 状态: 已关闭
# 类型: deliberate
# 阻塞于: 无

## 问题

信箱通道 (容器侧→设备侧 LLM 传话) 的设计盘问. 已定型: 队列放容器内, 设备侧常驻 pi 会话 (挂 herdr) 由 pi 扩展驱动 pop→处理→pop 循环, 经既有 ssh 入口拉取.

待盘点 (依据 [recon/01](../recon/01-llm-channel.md)):

- 队列格式与目录布局 (pending/replies/done, 单文件单消息)
- 消息类型枚举 (notify/open_url/file/exec/request) 与各类型审批边界 — exec 默认必问, "设备侧 LLM 是门卫不是全权代理"
- 请求-回复关联与容器侧非阻塞语义 (at-most-once, ttl)
- 设备侧常驻会话形态: 命名约定, 启动/自启方式, 空转成本
- 多容器并存: 设备侧轮询 N 个容器 (先) vs 宿主侧汇聚 (缓)
- 定时拉 (先) 与长连推 (后) 的分界
