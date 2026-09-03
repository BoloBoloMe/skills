# 状态: 待处理
# 类型: task
# 阻塞于: MILESTONE-03, MILESTONE-06

## 问题

镜像制备实现:

- host llm 依赖件分析 → 检查 host 已有镜像 → 选最适版本, 失配则换版/新建 → 记录元数据 (按 MILESTONE-06 拍板)
- Containerfile 由分析结果生成 (fat 分层原则: 稳定在前常变在后), build 验证
- 端口动态分配: `-p <容器端口>` 省宿主侧, `podman port` 事后发现; 容器内端口固定 (22/8800/6080), 宿主端口不钉
- skills 同步: COPY 进镜像 + 容器内 uv sync 重建依赖 (host .venv 不可复用, 调研 §8)
