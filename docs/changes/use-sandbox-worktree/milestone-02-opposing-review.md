# MILESTONE-02 反方审查

## 正方还原

### 定义

`sandbox-worktree` 是 host 主仓的 linked worktree 母体与 rootless Podman 容器的生命周期绑定对. 容器克隆母体分支, 只能经专属 git daemon 对 host 主仓执行 git 读写, 合规 fast-forward push 由 `updateInstead` 立即落到母体工作区. Roadmap 原定义也是 `git worktree + sandbox 容器` 的绑定对, 且把 `ff-push + updateInstead` 作为存续期回流路径 [roadmap/ROADMAP.md:5](roadmap/ROADMAP.md#L5), [roadmap/ROADMAP.md:14](roadmap/ROADMAP.md#L14).

### 前提假设

1. host 本地调用者受信, 容器 agent 不受信. 主仓 config 和 host 网络规则都在容器不可修改的边界外.
2. `receive.hideRefs` 的允许例外, `receive.denyNonFastForwards`, `receive.denyDeletes` 足以把一个主仓的 receive 写面收敛到一个母体分支的 fast-forward 更新. 单分支实验支持这一点 [milestone-02-worktree-topology-findings.md:269](milestone-02-worktree-topology-findings.md#L269)-[milestone-02-worktree-topology-findings.md:277](milestone-02-worktree-topology-findings.md#L277).
3. 每容器一个 daemon, 每容器网络只放行自己的 daemon, 等价于每容器一个 git 权限边界. 但现有证据只承诺过 `单容器单 gate`, 并明确把多 gate 互隔留待重审 [DECISIONS.md:29](DECISIONS.md#L29).
4. 多个容器可以共享同一母体分支. ref 的 fast-forward 约束可把并发竞争退化为一方成功, 另一方 fetch 后解冲突再推.
5. 重启时重放静态网络规则和 daemon 就能恢复原安全状态. 已有实测只证明 stop/start 后规则会消失并必须重注入 [2026-09-01-research.md:78](2026-09-01-research.md#L78), 没有证明容器工作负载与规则恢复之间存在 fail-closed 启动屏障.
6. 同一主仓是否允许两个不同母体分支同时服务不同 sandbox-worktree: `未知`. 本任务允许母体独立存活/自由复用, 但只明确举出多容器共享同一母体. Roadmap 则仍把多 sandbox-worktree 并发列为未决项 [roadmap/ROADMAP.md:45](roadmap/ROADMAP.md#L45).

### 论据

1. `updateInstead` 已实测能识别 linked worktree 的当前分支, push 成功后对应工作区立即更新 [milestone-02-worktree-topology-findings.md:43](milestone-02-worktree-topology-findings.md#L43)-[milestone-02-worktree-topology-findings.md:55](milestone-02-worktree-topology-findings.md#L55).
2. 无 hooks 的 config 组合已实测拒绝新分支/tag/main/删除/non-ff, 接受目标分支 fast-forward [milestone-02-worktree-topology-findings.md:194](milestone-02-worktree-topology-findings.md#L194)-[milestone-02-worktree-topology-findings.md:210](milestone-02-worktree-topology-findings.md#L210).
3. `receive.*` 配置只约束该仓库作为 receive 端, 不妨碍 host 从主仓向真实远端 push [milestone-02-worktree-topology-findings.md:92](milestone-02-worktree-topology-findings.md#L92)-[milestone-02-worktree-topology-findings.md:119](milestone-02-worktree-topology-findings.md#L119).
4. 独立 clone 的主要价值曾是 hooks 隔离. 既然无 hooks 的 config 能完成 ref 级 allowlist, 正方认为可以删除中转 clone, 直接服务主仓.

### 推理链

主仓 config 能守住唯一母体分支, `updateInstead` 能把该分支映射到 linked worktree, 专属 daemon 与网络白名单又让容器只能到达这个 receive 端. 因而独立 gate clone 已无必要. 母体可以脱离容器生命周期持续存在并被多个容器复用, 并发冲突由 ff 拒绝和后续 fetch/重推消化. host 重启后只需自动重放同一组确定状态, 整套生命周期仍保持原硬约束.

## 主战场

**严重: 每容器授权关系被实现成主仓全局策略, 权限状态的作用范围与 sandbox-worktree 的作用范围不一致.**

这是整组决定的承重环节. D-A 把 receive 端收回共享主仓, D-B 把 allowlist 放进主仓 config, D-E 引入复用/并发, D-F 又声称每容器 daemon 是一对一边界. 但 receive-pack 最终读取的是同一仓库策略, daemon 又无认证. 实测报告明确写明, `receive.hideRefs` 是 host 仓库配置 [milestone-02-worktree-topology-findings.md:279](milestone-02-worktree-topology-findings.md#L279)-[milestone-02-worktree-topology-findings.md:281](milestone-02-worktree-topology-findings.md#L281), 且任何能到达 daemon 的对端共享同一 gate 身份和 ref 写权限 [milestone-02-worktree-topology-findings.md:282](milestone-02-worktree-topology-findings.md#L282).

拆掉这一前提, 一对一 daemon 只剩进程/端口粒度, 不能表达 `容器 A -> 母体分支 A`, `容器 B -> 母体分支 B` 的授权映射. 那么母体自由复用, 多 sandbox-worktree 并发, 无 hooks, 无中转仓这几项不能同时成立. 这不是报错文案或实现细节, 而是当前模型缺少表达目标策略所需的信息.

## 反方反驳

对同一主仓中的两个母体分支 `A` 和 `B`, 共享 config 只有三种直接配置方式:

| 配置方式 | 结果 |
| --- | --- |
| 只例外放行 `A` | `B` 的 sandbox-worktree 无法工作, 多母体并发不成立 |
| 同时例外放行 `A` 和 `B` | 连到任一 daemon 的任一容器都能 push `A` 和 `B`, 每容器单分支硬约束失效 |
| 容器/daemon 启停时把全局例外改成对应分支 | 后写配置立即改变其他存活 daemon 的策略, 生命周期操作互相踩踏 |

每容器起一个 daemon 不改变这个三难. 所有 daemon 服务同一主仓, 没有身份认证, 而已验证模板只证明固定 `wt-work` 这一条分支的单策略情形 [milestone-02-worktree-topology-findings.md:271](milestone-02-worktree-topology-findings.md#L271)-[milestone-02-worktree-topology-findings.md:274](milestone-02-worktree-topology-findings.md#L274). 旧决策甚至明确把威胁模型限定为 `单容器单 gate` [DECISIONS.md:29](DECISIONS.md#L29). MILESTONE-02 不能把单实例实验直接外推成多实例隔离.

per-worktree config 也没有现成证据能救场. 已有实验至少证明 receive-pack 不会按将被更新的 linked worktree 选择其 `config.worktree` 下的 `core.hooksPath`, 而是使用共享仓库上下文 [milestone-02-worktree-topology-findings.md:213](milestone-02-worktree-topology-findings.md#L213)-[milestone-02-worktree-topology-findings.md:232](milestone-02-worktree-topology-findings.md#L232). 用 daemon 进程环境注入不同 `receive.hideRefs` 也许可能, 但本任务没有提出这种机制, 指定产物没有验证其配置优先级/隔离性/重启恢复. 它若成立也是新的安全机制, 不能算现决定已有论据.

同一承重假设在 D-D 中再次出现. 网络规则实测会随 stop/start 消失 [2026-09-01-research.md:78](2026-09-01-research.md#L78), 而 `--restart=always` 先自动拉起容器, systemd 再重注入规则的描述没有给出启动顺序和工作负载屏障. `规则内容确定`只能证明可重建, 不能证明重建过程原子且 fail-closed. 如果 agent 在 nft 规则就绪前恢复执行, 即使窗口很短, 网络硬约束已经被绕过. Roadmap 原先也把 host 重启恢复语义列为待回访项 [roadmap/ROADMAP.md:49](roadmap/ROADMAP.md#L49). 这里的置信度为中, 因为 systemd unit 的具体依赖/屏障尚未给出.

因此反方结论是: 目前证据最多支持 `一个主仓在任一时刻只开放一个母体分支` 的单授权域模型, 不支持一般化的母体自由复用模型. 若设计声称本来就只允许同一主仓一个活动母体分支, 必须把它提升为硬不变量; 这会显著约束 D-E, 并使 D-F 的每容器 daemon 没有隔离收益.

## 反方立论

反方主张: 安全策略必须与它保护的对象同生灭, 且接收端必须能区分需要不同权限的请求. 在坚持无 hooks 的前提下, 只能二选一.

### 方案 R1: 单活动母体租约

1. 每个主仓同一时刻最多一个可写母体分支.
2. 任意数量容器可共享这个母体, 明确承认它们共享同一 git 身份/写权限/故障域.
3. 每主仓或每母体只起一个 daemon, 不再伪装成每容器权限隔离. 容器网络都只放行这个端点.
4. 创建第二个不同母体前, 必须停止旧母体全部容器/daemon, 校验 ref 与工作区干净, 原子替换 allowlist 后再开放新端点.
5. 自动恢复由一个 systemd 编排单元完成: 先恢复网络与 daemon, 验证策略, 再释放容器工作负载. `--restart=always` 不应独立抢跑.

这个方案保住 D-A/D-B/D-C 的主体, 也保住 D-E 中 `多容器共推同一母体` 的特例, 但明确放弃同仓多母体并发和 D-F.

### 方案 R2: 每授权域独立 receiver

如果同一主仓必须同时存在两个不同母体分支, 就恢复一个真正能承载不同策略的边界:

1. 每母体独立 gate clone/receiver, 各自 config 只例外自己的分支; 或
2. 允许 shared pre-receive 根据可信端点/身份分流; 或
3. 引入经验证的 daemon 进程级配置注入, 并证明不同 daemon 对同一仓库读取不同 receive 策略且不会被仓库 config 合并污染.

前两项正是已排除候选, 第三项尚无事实基础. 这说明用户当前的 `无中转 clone + 无 hooks + 多母体自由并发 + 每容器单分支硬约束` 不是一个已完成的取舍, 而是一组尚未证明可同时满足的要求. 反方不主张偷偷恢复复杂度, 而主张明确选择要牺牲并发, 还是接受一个可表达授权关系的接收层.

在进入 M03 前应增加最小反证矩阵: 同一主仓建 `A/B` 两个 linked worktree, 起两个 daemon, 两个容器端点分别尝试 push `A/B`, 并在任一 daemon/容器重启期间重复. 验收条件不是 `正确 push 成功`, 而是 4 个交叉 push 永远拒绝, 且 nft 规则就绪前 agent 工作负载不可运行.

## 幸存与比较

正方仍成立的部分很强:

- `updateInstead` 对 linked worktree 生效已被直接验证, 砍掉中转层确实能换来 push 即落地 [milestone-02-worktree-topology-findings.md:51](milestone-02-worktree-topology-findings.md#L51)-[milestone-02-worktree-topology-findings.md:55](milestone-02-worktree-topology-findings.md#L55).
- config-only allowlist 对单一固定分支有效, 且不会妨碍主仓作为发送方 push 真远端 [milestone-02-worktree-topology-findings.md:269](milestone-02-worktree-topology-findings.md#L269)-[milestone-02-worktree-topology-findings.md:277](milestone-02-worktree-topology-findings.md#L277).
- 同一母体的多个容器共享一个分支时, ff 拒绝至少能防止无声改写 ref 历史. 它不能防语义覆盖, 但用户已明确把冲突消化交给容器内 agent.
- HEAD 对象泄露和 daemon 无认证在给定威胁模型内可以接受, 前提是授权域确实只有一个.

但反方仍占优. 正方收益是少一个 clone/少一次同步和更直接的落地窗口. 反方风险是硬约束在第二个不同母体出现时确定性失效, 影响整个主仓的所有活动母体分支; 它不是低概率故障. 跨分支误写通常可借 Git 历史恢复, 但容器已获得本不应拥有的持久写能力, 安全契约一经违反不能用可恢复性抵销. 自动恢复窗口还可能触及网络外泄, 其后果不可由 Git 回滚. 因此即使完全接受单母体实验结果和砍层收益, 也应先收紧为 R1, 或重开 receiver 隔离机制选择, 再关闭 MILESTONE-02.

## 置信度

- 主结论 `共享主仓 config 无法表达每 daemon/每容器不同分支授权`: 高. 依据是配置作用域, daemon 无认证事实, 以及现有实验仅覆盖单分支策略.
- `当前决定必然要求同仓不同母体并发`: 未知. 任务文字没有明确这一点, Roadmap 仍将多 sandbox-worktree 并发列为未决. 但缺少 `每主仓仅一个活动母体` 硬不变量本身已足以阻止按一般生命周期模型落地.
- `--restart=always + 事后重注入 nft` 存在 fail-open 窗口: 中. 规则易失已有实测, 但尚未提供 systemd unit 的具体顺序与屏障实现.
- 综合置信度: 高. 当前决定组至少必须增加单活动母体限制和 fail-closed 恢复屏障; 若不接受这些限制, 核心拓扑需重开.

总结: 当前方案把每容器授权寄托在共享主仓 config 上, 一旦要求同仓不同母体并发, 每容器单分支硬约束便无法表达. 可成立的边界是单活动母体, 否则必须恢复独立 receiver, hooks, 或另一个经验证的端点级策略机制.
