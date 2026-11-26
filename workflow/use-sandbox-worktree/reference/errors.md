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
| `PARTIAL 容器检出不符 (...)` | 重入时已有检出不是预期 Git 桥/分支/提交, 或脏/有未推送提交. birth 已把该检出原样保留 (不 `rm` 不重克隆), 先人工确认里面没有要留的东西, 再决定删除或按 runtime 状态恢复; 不要盲目重跑 birth 期望它自愈 |
| `PARTIAL 容器检出不符 (工作区状态不可读 ...)` | 容器内 `git status` 自己失败 (例如坏 index/权限), 脏不脏未知. 检出已原样保留; 进容器处理该工作树 (如重建 index) 后再按同一 birth 重入, 不要 `rm -rf` |
| `记录的镜像 digest ... 在本地不可解析` | 旧创建记录只有 digest 没有固定镜像 ID, 且本地找不到该镜像. 不会退回未经核对的 tag 去建容器; 重新准备兼容镜像后重跑, 或按 terminate 保护流程处理该记录 |
| `记录镜像 digest ... 与容器实际 ImageDigest ... 不符` | 记录里的镜像与同名容器实际跑的不是同一镜像 (被替换/记录错位). 不接管该容器; 先人工核对该容器再决定 |
| `无法确认镜像 ... 内工具是否支持只读预检` | 镜像里既没有 `agent-tool-actions` 标记, 也读不到工具实现文件. 按不兼容处理, 不复用该镜像 |
| `PARTIAL 读取宿主分支 refs/heads/<分支> 提交失败` | 母体分支 ref 不存在或无权限; 核对母体与分支名 (分支名用原文), 不要改 Git 引用绕过 |
| `镜像内模板解析器不接受本次模板快照` (整句见 [`agent-templates.md`](agent-templates.md)) | 选定镜像自带的解析器拒收本次模板快照 (例如旧镜像要求模型 `cost` 字段). 文案末尾带目标镜像 ID 与白名单原因. 按 [image-prep.md](image-prep.md) 审批构建/发布含兼容解析器的新镜像后, 用 `--image <ref>` 重跑; 不手改快照, 不补假价格, 不改旧容器 |
| `镜像内工具自检失败` (预检失败原因之一) | 预检容器内工具因身份/契约文件没通过自检, 不是模板字段问题. 核对镜像 `/etc/swt-agent-template-contract` 与 label `run.sandbox-worktree.agent-template-contract` 是否一致, 正常镜像不该出现 |
| `无法确认镜像 ... 内工具是否支持只读预检` | 能力探针没能跑起来 (镜像不完整/缺 python). 按不兼容处理, 不复用该镜像 |
| 模板安装/验收失败 | 不交付; 使用固定快照重跑同一 birth, 或按 terminate 门禁终结该新容器. 原始诊断可能含 Key, 不直接打印 |
| 创建绑定/容器 ID 不匹配 | 同名容器已被替换或不是本次创建, 不写入/不启动, 先由用户处理记录冲突 |
| 模型/业务共用环境变量需用户决定 | 不自动继承或丢弃云/Git 业务凭据, 用户决定本次 env.conf 清单后再重跑 |
| `APPLY-CONFLICT` | 防火墙表内有其他容器规则, apply 拒覆盖; 走 swt 编排 (--merge) 不手调 |
| `access denied or repository not exported` | daemon 拒服务该路径: 请求路径不是本 daemon 的母体目录, 或母体私有 git 目录缺 git-daemon-export-ok; 经桥的 remote 路径段必须是母体目录名, 别用旧版主仓名 |
