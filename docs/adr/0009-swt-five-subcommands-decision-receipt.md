# swt 单模块五子命令 + 决策收据协议

use-sandbox-worktree 的五个生命周期场景 (诞生/恢复/查询/终结/换母体) 收敛为**一个 host 侧 module** (`swt`), 对外五个子命令 birth/resume/status/terminate/switch, 统一 exit code 协议 (0 成 / 1 DECIDE / 2 前置 / 3 中途可重入 / 4 环境). 用户决策走**决策收据** (D026): 脚本非交互, DECIDE 绑定资源指纹 (容器 Podman ID, 母体 ref tip, config 指纹, 脏计数等), 用户答后带 flag 重跑, 重跑先比对指纹, 变了重新问 — 防止 "确认拆 A 实际拆了同名重建的 B". 危险操作显式独立: switch 与 --force 不藏进通用入口.

## 备选方案

- **2 入口 (up/down, 状态机全藏)**: leverage 最高, 但换母体藏进 `up --yes switch-mother`, 危险操作在敲下命令那一刻不够无可误会 — 拒绝.
- **9 入口 (含 config/daemon 修复原语)**: 顺序约束把复杂性泄回调用方 (host llm), 原语扩可误用面 — 修复原语推迟, 其余拒绝.
- **五个独立脚本**: 探测/config 模板/输出协议复制五份, 漂移风险 — 拒绝.

## 后果

- MILESTONE-12 范围含 net-firewall.py 接口扩展 (按容器源地址删规则, 多容器共享 `inet swt` 表不再互删, D032) 与 e2e-smoke 缓退役 (等价矩阵全绿才删, D036).
- resume 带 DECIDE gate (D030), D011 的确认义务在代码里不在文档里.
- 多容器身份分两层 (母体 id + 容器实例名, D031), D007 一名贯穿在单容器缺省名下保留.

2026-09-14 补充: [D054](../changes/use-sandbox-worktree/DECISIONS.md#d054-一母体一个活跃容器-2026-09-14-m04) 收窄新 birth 为一母体至多一个活跃容器. 上述身份区分和既有多容器清理/隔离保障保留, 不再以 D031 授权新建同母体第二个活跃容器; 现有容器不迁移, 实施归 M05.

2026-10-01 补充: [swt-list-sandbox](../changes/swt-list-sandbox/DECISIONS.md) 增设只读跨仓清单子命令 `list` (枚举本 host 全部带 label 的容器, 供 pi 扩展 `/list-sandbox` 纯连接器消费): 末行 `LIST {...}` 单行 json + 退出码仅 0/4, 为 D027 协议的又一显式例外 (先例 display-check 与 enroll-device-key, 后者例外补记于 [D057](../changes/use-sandbox-worktree/DECISIONS.md)); 支持 `--records-root` (与生命周期子命令对齐); 容器状态用双轴 (podman 运行态透传 × swt 生命周期) + record-state 三态, 记录未匹配不称孤儿; 展示条目命名 "访问入口" (交付包的入口子集), 多网卡候选地址是对 swt-cross-host D010 的 list 语境修订. 同批补记: switch 子命令已删 (D056), 命令面现为 birth/resume/status/terminate + display-check + enroll-device-key.

详见 [DECISIONS.md](../changes/use-sandbox-worktree/DECISIONS.md) D025-D038 与 [反方审查](../changes/use-sandbox-worktree/milestone-11-opposing-review.md).
