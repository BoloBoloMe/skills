# gate 通道形态: 专属 git daemon + 读走 gate 镜像, 拒绝 ssh

use-sandbox-worktree 的 gate (agent 唯一可写的 host 端点) 采用每 gate 一个专属 `git daemon --enable=receive-pack` 实例: base-path 仅含本 gate 仓, 不开 `--export-all`, 端口动态分配, 随容器生灭. 容器的 git 读也全走 gate 镜像, 真远端对容器完全不暴露.

## 备选方案

git-over-ssh 被排除: 私钥必须进入容器 = 凭据泄漏面 (与 host↔真远端共用密钥直接判死); 且 ssh 默认可对用户有写权限的任意路径执行 git-receive-pack (容器可写穿 host 上其他仓库), 锁住路径需 authorized_keys forced command, 复杂度白付. daemon 的无认证由 Git 访问白名单 + base-path 拓扑兜底 — 门禁由拓扑保证, 不由钩子或认证保证 (T7b 教训, 调研 §4.2).

## 后果

daemon 无身份认证与审计能力; 威胁模型仅限"单容器单 gate, 本机 netns 白名单". 未来若要多 gate 并发隔离或会话级审计, 须重审本决策 (详见 docs/changes/use-sandbox-worktree/DECISIONS.md D004).
