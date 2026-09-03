# 状态: 待处理
# 类型: task
# 阻塞于: MILESTONE-03

## 问题

网络访问控制, **双模式** (绘制会话拍板, 修正调研 §4.1 的白名单单模式):

- **黑名单**: 默认放行 + 拒指定 IP/域名 (护特定环境数据库/redis 的场景)
- **白名单**: 默认拒 + 放行清单, 含创建时盘点确认环节 (host llm 盘点任务所需域名/IP → 用户确认 → 静态注入)
- host llm 创建容器前询问用户选哪种; 运行期不切换, 换模式回父会话

技术路线 (调研 §4.1 已实测): 桥 netns (rootless-netns) netavark 表 nft 注入, 容器内 root 也拦截; 两套规则同一脚本两个分支; `podman network create --subnet` + `run --ip` 静态 IP; 启动后重注入 (netns 重建规则全失); IPv6 兜底 DROP.
