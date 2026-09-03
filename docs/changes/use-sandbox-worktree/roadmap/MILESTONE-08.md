# 状态: 待处理
# 类型: task
# 阻塞于: MILESTONE-03

## 问题

展示链接线:

- 容器内 present web_server `start <port> <root> --bind 0.0.0.0`, 经端口映射向 host 浏览器交付 URL
- present SKILL.md 加容器分支; present / explain-diff / probe 等跟随

考察点: 此路径不经 host 常驻展示服务, present ISSUE-02 (add-dir) / ISSUE-04 (复用挂载) / stop 缺失是否真有影响 — 预期无 (stop 随容器灭; add-dir 可用重启或多挂目录绕过), 须实测确认而非假设.
