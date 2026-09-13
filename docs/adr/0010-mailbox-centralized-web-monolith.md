# 信箱: host 中心化 web 服务单体而非容器内文件队列

Status: accepted

sandbox-worktree 需要容器侧→设备侧的传话通道. 可行性调研 (docs/changes/swt-cross-host-access/recon/01-llm-channel.md) 的原主候选是"容器内文件队列 + 设备侧常驻会话经 ssh 拉取", 核心理由是零新增网络面/凭证. 用户拍板改为: 与 llm-proxy 合并为一个 host 常驻 web 服务单体 (基础服务), 理由 — llm-proxy 反正常驻 (零新增进程), 中心化天然解决多容器与多设备路由, 消息存 host SQLite 比容器内文件队列更持久, 且局域网内所有机器天然可达. 安全立场相应从"零新增网络面"调整为"签名密钥认证 + 服务端授权".

备选方案: 文件队列 + ssh 拉取 (传输零新增但多容器轮询/实时性/持久性都弱); 容器直驱设备 herdr (白名单+凭证双违背, 维持淘汰); ssh -R 反带 socket (曾列为实时性升级项进迷雾; 长轮询已秒级, 失去意义, 随 D008 关闭, 见 docs/changes/swt-cross-host-access/milestone-01/DECISIONS.md).

后果: swt 白名单需对容器放行宿主网关 IP (IP 级粒度, 容器因此可达宿主全部 0.0.0.0 端口, 已接受, 各服务自有认证兜底); host 上出现第一个常驻业务组件, "host agent 只管生命周期"的角色边界由用户明确放宽给基础服务.
