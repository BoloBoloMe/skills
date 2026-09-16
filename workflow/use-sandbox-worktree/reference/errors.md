# 原生报错译解表

swt 生态里原生报错的含义与处置. 脚本 stderr 透传原生报错原文, 看不懂时查本表.

| 原生报错 | 含义与处置 |
| --- | --- |
| `deny updating a hidden ref` | push 目标不在允许写入的范围内 (新分支/tag/删除); 容器只准推本对母体分支 |
| `denying non-fast-forward` | 母体分支有别人/别容器的新提交; 容器内 fetch → 解冲突 → 重推 |
| `Working directory has unstaged changes` | 母体目录跟踪文件被 host 侧改脏; 还原母体改动后重推 |
| `Address already in use` (pasta, exit 125) | 容器宿主端口被占, start 失败; 不自动换端口, 释放端口或重建容器 (exit 3 可重入) |
| `APPLY-CONFLICT` | 防火墙表内有其他容器规则, apply 拒覆盖; 走 swt 编排 (--merge) 不手调 |
| `access denied or repository not exported` | daemon 拒服务该路径: 请求路径不是本 daemon 的母体目录, 或母体私有 git 目录缺 git-daemon-export-ok; 经桥的 remote 路径段必须是母体目录名, 别用旧版主仓名 |
