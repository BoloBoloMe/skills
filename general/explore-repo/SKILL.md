---
name: explore-repo
description: explore 远程 git 仓库. 当我提到仓库 URL 并需要了解时.
---

# explore-repo

### 1. 验证 URL

只接受 git URL (HTTPS 或 SSH). 非 git 链接直接拒绝, 并提示提供 git URL.
完成标准: URL 确认为合法 git URL, 或拒绝并停止.

### 2. 克隆

克隆到系统临时目录的独立子目录. 命名: `<repo-name>-<timestamp>`. 默认 `--depth 1`.
完成标准: 仓库成功克隆到临时子目录, 路径已记录.

### 3. 探索报告

- `路径`: 仓库本地绝对路径
- `目录树`: 顶层 2 级目录结构
- `README 摘要`: 不超过 200 字
- `语言/框架`: 主要语言和框架
- `文件数`: 源代码文件统计

完成标准: 报告含以上五项, 声明仓库就绪, 等待指示.
