---
name: use-sandbox-worktree
description: 管理宿主 worktree 与 sandbox 容器绑定对的创建, 恢复, 网络, 接入和终结.
disable-model-invocation: true
---

# use-sandbox-worktree

管理一对资源: 宿主 Git worktree (下称母体) 与从它克隆的 sandbox 容器. 容器只经本对 Git 桥快进推送母体分支, 不接触真远端; 推送落地有秒级短延迟. 每个母体至多一个未终结容器, 已停止也占用此名额; 不同母体可并存. 旧部署按原形态处理, 不追溯迁移.
你在宿主管理生命周期与接入, 开发交给容器内 pi. 母体仅供审阅/diff/不改跟踪文件的试跑: 跟踪文件变脏会拒绝容器 push, 未跟踪文件不阻塞.

## 调用与审批

本 skill 面向 Linux 宿主, 使用 rootless Podman/pasta, nftables, Git 和 Herdr. 脚本路径均相对本 skill 目录解析, 用 `uv run python` 调用; 从项目 cwd 引用脚本绝对路径, 或显式传 `--repo <主仓>`, 避免把 skill 仓库当目标. 参数以对应子命令 `--help` 为准. `--branch` 用分支名原文, 母体目录由 `use-worktree` 的 slug 规则确定, 两者不等同.
记录根默认 `~/.agents/sandbox-worktree/`, 生命周期和 network 命令可用 `--records-root` 覆盖. 记录可能含凭据, 保持私有; 不回显 Key/私钥正文. 机制说明与实际 Git 配置/防火墙/拓扑冲突时, 保留现场并向我报告, 不靠手工改资源绕过脚本检查.

birth/resume/status/terminate 非交互, 统一返回码:

| 码 | 你的动作 |
| --- | --- |
| 0 | 按实际输出核对结果, 包括幂等无变化 |
| 1 | 逐字转述 `DECIDE <id> <kind> <问题> 选项: <flag>`, 暂停等我答复, 再带所选 flag 重跑同一命令 |
| 2 | 报告输入或前置缺口 |
| 3 | 按 stderr 的 PARTIAL 指引重入/救场, 不当成功 |
| 4 | 报告环境不支持 |

DECIDE 收据绑定当时资源状态, 状态变化就重新问; 不代答或预填批准 flag/收据 ID. 找到输出中的 `STATE {...}` 行再读 JSON, 不假定它是末行; 错误看 stderr 的 FAIL/PARTIAL/ENV. 其他命令的输出协议见各自参考, 不套用 STATE.

## 先盘点

```text
uv run python scripts/swt.py status --repo <主仓>
```

status 只读. 从 `STATE.mothers[]` 定位目标母体/分支/容器, 顶层兼容字段不一定是本次目标. 多对时按母体分支或容器名消歧, 不确定就问我. 按目标事实选择下一步:

- 有未完成 `network-change`: birth/resume/update 前先走 network recover; 若我明确要求终结原目标, 仍走 terminate 的保护检查.
- retired: 只能 terminate, 不恢复.
- birth 初始化未完成: 重跑同一次 birth, 不用 resume 补安装.
- 健康运行: 复用现有入口, 不另建/恢复.
- 容器停止, daemon/Git 桥/网络规则异常: resume.
- 无记录且无遗留资源, 或记录为 idle: birth. 有容器却缺记录时先报告, 不当空现场.

只要求查询时到此结束; 要交付入口则继续下方交付流程.
完成标准: 已报告主仓, 目标母体路径/分支, 容器和实际状态, 并明确下一步或待我消歧的问题.

## 按目标操作

**新建/补完 birth**: 先读 [birth.md](reference/birth.md), 完成母体, 网络, 镜像与模板的确认后再创建. 新建与失败重入共用该入口, 不能换名字绕过已有容器约束.
完成标准: birth 参考中的创建检查全部通过; 随后执行交付.

**恢复 resume**:

```text
uv run python scripts/swt.py resume --repo <主仓> --name <容器名>
```

脚本需要恢复时先出 DECIDE, 我确认后才加 `--confirm`. 恢复只作用于目标对, 具体操作顺序交给脚本. 新模板只检查固定配置/凭据/网关, 不重装或换 Key. 旧形态配置冲突按 [ops.md](reference/ops.md) 处理; 宿主换网后的 pasta 失配按告警交我决定是否重建. 显示失败可降级到终端, 不擅自终结工作容器.
完成标准: 目标 running, STATE 指向本对母体分支, 防火墙/Git 通道及适用的模板检查通过, Herdr machine 已核对, 显示状态明确; 随后执行交付.

**网络维护 network**: 查询规则, 增删白名单/补理由或恢复未完成事务前, 先读 [network.md](reference/network.md).
完成标准: 已按 `NETWORK.stage/checks/pending` 报告本次结果; 回退后仍报告原操作失败, 未完成事务明确交还给我.

**终结 terminate**:

```text
uv run python scripts/swt.py terminate --repo <主仓> --name <容器名>
```

未提交改动 (含未跟踪文件), 未落母体的提交, 或无法检查均按脏处理; 仅落后母体不算脏. 脏时转述 DECIDE, 等我确认容器内 agent 已停手及同意强拆后才加 `--force`. 只清目标容器及其规则/Herdr machine/SSH 接线/凭据/Maven 快照; 本对最后一个容器终结才收 daemon, 其他对保留. 母体目录与配置留存, 存删由我另走 `use-worktree` 流程决定. PARTIAL 时保留记录供同一 terminate 重入, 不宣称清理完成.
完成标准: 目标及应收的本对资源已清除, 母体未改; 本对已无容器时记录为 idle, 尚有历史容器时保留其记录与服务.

## 交付与接手

每次交付新建/恢复/健康容器的入口前, 必须读 [delivery.md](reference/delivery.md), 完成其中的当前会话持续取信与分区核对.
已知任务开始前 (含健康容器接新任务), 增加操作/依赖或环境变化时, 必须读 [task-conditions.md](reference/task-conditions.md), 按实际操作检查并分项报告. 未给任务就标未检查, 不猜服务清单.
完成标准: 基础通道/接入入口, 当前收信状态, 任务条件与风险分别有事实结论, 不把可登录当全部就绪.

## 按需参考

- 登录/委派容器内 pi, 审阅母体或排查 Web/显示: [living.md](reference/living.md).
- headed 浏览器退出 86 或设备侧收到拉窗信: [pull-window.md](reference/pull-window.md).
- 手工救场, 改原生操作, 查凭据/比较远端提交/截取命令输出: 先读 [ops.md](reference/ops.md). 原生错误含义不明时查 [errors.md](reference/errors.md).
- 修改提示词/env.conf 或部署仓库变更: [maintenance.md](reference/maintenance.md). 修改验收不自动授权同步部署.
