# 状态: 待处理
# 类型: deliberate
# 阻塞于: 无

## 问题

sandbox-worktree 从生到灭的状态机, worktree 与容器两个资源面一起拍 (决策互相咬合, 分开拍会拍出矛盾语义):

1. **worktree 面**: sandbox/work 分支生灭 (每会话 reset 到最新 main? gate 仓随会话新建销毁?) / 与 use-worktree 的交互方式.
2. **容器面**: 容器生灭与分支的同步关系 / 允许 stop 还是只许 rm (stop/start 后 netns 重建, 网络规则全失须重注入) / 镜像换版时存活容器怎么处置 / 孤儿容器清理.
3. **终结面**: 拆的顺序 / 脏状态检查 (容器内有未 push 的工作怎么办).
4. **端口分配**: 动态分配的宿主端口算不算 sandbox-worktree 的身份信息, 需要记录吗 (容器 restart 后宿主端口会变).
