# 状态: 待处理
# 类型: research
# 阻塞于: 无

## 问题

podman 镜像元数据能力调研 — "镜像属于哪个项目 / 内容物有什么 / 版本号" 记录到哪的事实基础 (MILESTONE-06 在等它):

- image labels: 设置/读取/查询过滤 (`--filter label=...`) 的实际能力与限制
- `podman image inspect` 可读到什么 (sandcastle 已用作预检)
- 镜像命名与 tag 策略能承载多少语义 (项目标识 / 版本号)
- 容器侧是否也有 label 机制可记录 sandbox-worktree 身份

委派子代理探索, 产出分析文件.
