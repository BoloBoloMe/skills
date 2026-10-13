# 原生报错译解表

swt 生态里原生报错的含义与处置. 脚本 stderr 透传原生报错原文, 看不懂时查本表.

| 原生报错 | 含义与处置 |
| --- | --- |
| `deny updating a hidden ref` | push 目标不在允许写入的范围内 (新分支/tag/删除); 容器只准推本对母体分支 |
| `denying non-fast-forward` | 母体分支有别人/别容器的新提交; 容器内 fetch → 解冲突 → 重推 |
| `Working directory has unstaged changes` | 母体目录跟踪文件被 host 侧改脏; 还原母体改动后重推 |
| `Address already in use` (pasta, exit 125) | 容器宿主端口被占, start 失败; 不自动换端口, 释放端口或重建容器 (exit 3 可重入) |
| `AGENT-CONTRACT` / 镜像缺少 agent-template 契约 | 旧镜像不能用于新模板, 按 base/display/项目构建审批准备新镜像, 不改旧容器 |
| `MODEL-CONFIG-IN-IMAGE` | 清单包含旧静态模型配置条目, 新镜像模型配置只走 birth 模板 |
| 模板安装/验收失败 | 不交付; 使用固定快照重跑同一 birth, 或按 terminate 门禁终结该新容器. 原始诊断可能含 Key, 不直接打印 |
| 创建绑定/容器 ID 不匹配 | 同名容器已被替换或不是本次创建, 不写入/不启动, 先由用户处理记录冲突 |
| 模型/业务共用环境变量需用户决定 | 不自动继承或丢弃云/Git 业务凭据, 用户决定本次 env.conf 清单后再重跑 |
| `APPLY-CONFLICT` | 防火墙表内有其他容器规则, apply 拒覆盖; 走 swt 编排 (--merge) 不手调 |
| `access denied or repository not exported` | daemon 拒服务该路径: 请求路径不是本 daemon 的母体目录, 或母体私有 git 目录缺 git-daemon-export-ok; 经桥的 remote 路径段必须是母体目录名, 别用旧版主仓名 |
