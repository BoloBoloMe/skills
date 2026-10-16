---
name: use-sandbox-worktree
description: 管理 sandbox-worktree (host worktree 母体 + sandbox 容器绑定对) 的生命周期与配套镜像/网络/显示栈.
disable-model-invocation: true
---

# use-sandbox-worktree

**管理单位**: 一个宿主机上的 Git worktree (母体) + 它的 sandbox 容器. 母体是主仓同级的工作树, 目录名按 `use-worktree` 的 slug 规则生成, 不等于分支名; 容器从母体克隆, 快进 `git push` 使成果落回母体 (有秒级短延迟). 一母体同一时刻至多一个活跃容器 (含已停止但未终结的容器), 不同母体可并存. 每对的 git daemon 仅听宿主回环, 容器通过固定 git 桥连接它; 不向容器暴露真远端. 旧部署留下的容器按其原有形态处理, 不追溯改造.

你在宿主机侧管理生命周期, 交付与接入, 实际开发交给容器内 pi, 不在母体编辑跟踪文件. 脚本要我拍板时会输出 DECIDE: 逐字转述, 等我答复后带所选 flag 重跑同一命令, 不代答. 机制描述与实际 Git 配置/防火墙/拓扑冲突时以环境硬约束为准, 报告我. 手救场或修改容器原生操作见 [reference/ops.md](reference/ops.md). 沙盒维护中查凭据/比较远端提交/截取命令输出也先读该参考的低开销取证规则.

## 前置与决策协议

- 使用 rootless Podman (pasta 网络), nftables, Git; birth 会用一次性小仓库验证 Git 支持所需的 `hideRefs` 与 `extensions.worktreeConfig`, 不支持退出 4. 全部脚本从本 skill 目录按相对路径运行, 使用 `uv run python`.
- 记录根缺省 `~/.agents/sandbox-worktree/`, 可用 `--records-root` 覆盖 (设备密钥登记命令除外). host `~/.agents/skills/` 全树需让容器用户可读 (rootless uid 映射下靠 other 位); 带依赖的 skill 须携带已部署的 `uv.lock`. 可选 Maven settings 快照可能含凭据, 记录目录须保密, 终结容器时清除该容器快照, 细节见 [reference/risks.md](reference/risks.md).

四个生命周期子命令 birth/resume/status/terminate 非交互, 返回码: 0 成功 (含幂等操作), 1 有 DECIDE 待我, 2 前置不足, 3 中途失败须按 PARTIAL 指引重入/救场, 4 环境不支持. exit 1 时 stdout 有 `DECIDE <id> <kind> <问题> 选项: <flag>`; 一次列出可预见的拍板点, 答案由一次性收据绑定当时的资源状态, 状态变了就重新问. 执行中冒出的失败按 PARTIAL 报, 不由你自作决定. 输出中查找 `STATE {...}` 这行 JSON (status 可能在它后面附 URL/窗口入口行), 据字段判断状态; 错误详情看 stderr 的 FAIL/PARTIAL/ENV 行. 脚本原生错误看不懂时查 [reference/errors.md](reference/errors.md).

## 入口: 先盘点

```text
uv run python scripts/swt.py status [--repo <主仓>]
```

`--repo` 不给则从 cwd 推导. status 只读, `STATE.mothers[]` 逐对列分支/目录/daemon/容器, 顶层兼容字段表示主对. 已健康运行的容器 → 报告现有入口, 我需要完整接入信息时按 [reference/delivery.md](reference/delivery.md) 核对, 不另建/恢复; 没有记录或记录为 idle → birth; 容器停止, daemon/网络规则缺失或 git 桥异常 → 定位目标对后 resume; retired 容器 → terminate (resume 拒绝). 多对按母体分支或容器名消歧, 不把别的对当成目标.
已知任务开始前 (含健康容器接新任务), 增加操作/依赖或环境变化时, 必须按 [reference/task-conditions.md](reference/task-conditions.md) 检查本次需要的实际操作; 默认只读, 写入探测先批准范围. 缺条件只阻塞依赖它的工作. 没给具体任务则标任务条件未检查, 不猜服务清单.
完成标准: 明确当前目标对与下一步, 或确认现有容器基础通道健康并交付现有入口; 任务条件另按事实分项报告.

## 诞生 (birth)

**第一步, 准备母体**: 调用 `use-worktree` skill 先按其建树流程确定目标分支与工作树, `--branch` 始终用分支名原文. 母体已存在则脚本复用; 缺席时 birth 可按 `--base`/缺省来源创建对应工作树, 但先完成 `use-worktree` 的布局/分支/授权检查, 不能绕过它直接让 birth 猜项目布局. 分支是每对的钥匙: 已有别的对存活, 仍可对新分支 birth.
完成标准: 主仓, 目标分支与对应母体路径已由 `use-worktree` 核实, 母体工作区干净.

**第二步, 决定网络**: 创建容器前与我确认 whitelist/blacklist, 运行期不切换. whitelist 默认拒绝其他出站, 脚本自动放行网关地址 (全端口), 容器实际 DNS 解析器 (仅 udp/tcp 53), 已建立连接的返程, `--allow-entry CIDR "理由"` 再补工作需要的 IPv4/IP 网段; git 经 Unix socket 桥, 不占网络白名单. blacklist 默认放行, `--deny` 阻断指定 IP/CIDR, 适合保护宿主特定服务. 防火墙只认 IP, 放行一个地址就是放行其所有端口; 与我盘点所需站点并解析后再传, 换 IP 时重新盘点. 新站点需求在运行期发生时回本会话问我, 使用下方 network 入口预览审批, 不手拼整份名单; 自动放行网关/DNS 的残余风险见 [reference/risks.md](reference/risks.md).
完成标准: 我已确认网络模式与条目, 白名单新增是具体 IPv4/IP 网段并附用途理由, 不是域名. 新 birth 的裸 --allow 会被拒绝; 历史理由未知不编造.

**第三步, 镜像**: birth 自动匹配项目需求清单 `<records-root>/<项目slug>/requirements.md` (或指定 `--requirements`). 缺清单时 birth 退出 2; 从项目的 AGENTS.md/README/依赖文件推导并把清单展示给我, 明示构建会运行安装脚本, 获确认后才落盘并重跑. REUSE 可直接继续; BUILD-NEW 时 birth 停下出 DECIDE, 我确认后单独运行 `image-prep build`, 构建完成用 `--image <ref>` 重跑 birth. base/display 仅在我明确要求时重建; 缺失/过期 display 须先按审批链制备, 不私自构建. 清单格式, 父层匹配与重建见 [reference/image-prep.md](reference/image-prep.md); 模板/镜像契约见 [reference/agent-templates.md](reference/agent-templates.md).
完成标准: 清单已确认且有可用镜像, 或已经把待批准构建明确交还给我.

**第四步, 创建并交付**:

```text
uv run python scripts/swt.py birth [--repo <主仓>] --branch <母体分支名原文>
    [--base <来源ref>] [--name <容器名>]
    [--mode whitelist [--allow-entry <CIDR> "理由"]...] | [--mode blacklist [--deny <CIDR>]...]
    [--agent-template <名称>] [--image <ref>] [--requirements <file>]
    [--new-mother | --reuse-mother] [--lan-ip <ipv4>]
```

脚本依收据提示的 DECIDE 收齐模板/网络/主机名/局域网地址/镜像选择; 即使只有一个模板也由我选. `--name` 只是自定义名称, 不能绕过同母体活跃容器唯一约束. 新容器使用兼容通用镜像契约的模板, 不复制主机 OAuth/旧模型凭据; 失败重入和固定快照规则见 [reference/agent-templates.md](reference/agent-templates.md). 旧容器不自动套新模板. display 检查失败时遵照脚本给出的 DECIDE 再问我, 不因显示问题擅自终结工作容器.

成功后读取 [reference/delivery.md](reference/delivery.md), 按目标容器的实际 STATE/脚本输出交付 ssh/noVNC/web/herdr 入口, 凭证, 窗口状态/缺席原因以及 [reference/risks.md](reference/risks.md) 的风险; 不拼猜来的地址, 不静默丢项. 母体使用纪律一并转述: 只读审阅/diff/试跑, 跟踪文件保持不变, 否则容器 push 会被拒; 未跟踪文件不阻塞.
完成标准: STATE `stage=born`, 容器检出分支与母体分支相同, 交付包与缺席原因齐全; 已知任务的条件按 [reference/task-conditions.md](reference/task-conditions.md) 分项报告, 可登录不代表任务条件齐备.

## 恢复 (resume)

```text
uv run python scripts/swt.py resume [--repo <主仓>] [--branch <母体分支名原文>] [--name <容器名>] [--confirm]
```

有未完成 network-change 时先停止并走 network recover, 不靠 resume 绕过. 多对必须指定分支或容器名. 有可恢复对象会先出 DECIDE, 我确认后加 `--confirm` 重跑. 恢复只收敛目标对: 收残留 daemon/旧 git 桥, 重启容器并重建本对 daemon/桥, **start 后立即重注入防火墙规则**, 再检查显示栈与 git 通道 (remote ls-remote/fetch), git 通道通过前不交付工作. 显示栈失败标降级但不阻断终端, 旧镜像无显示栈时标 absent; retired 容器只能 terminate. 旧记录可沿原有恢复机制处理; 新模板 birth/resume 遇主仓旧形态配置会停止, 不自动迁移其他对, 处置见 [reference/ops.md](reference/ops.md). 初始化未完成要重跑同一次 birth 而不是 resume. 宿主换网后 pasta 旧配置可能失配, 按脚本告警评估是否重建.

完成后按 [reference/delivery.md](reference/delivery.md) 与 [reference/risks.md](reference/risks.md) 齐发交付, 不沿用停止前未经核对的入口.
完成标准: 容器 running, 防火墙已重注入, git 桥校验通过, 显示状态已标注; 新模板的固定配置/凭据/网关检查也通过, STATE 指向本对母体分支.

## 网络维护 (network)

```text
uv run python scripts/swt.py network show --name <容器名> [--repo <主仓>]
uv run python scripts/swt.py network update --name <容器名> [--repo <主仓>]
    [--add <CIDR> "理由"]... [--remove <CIDR>]... [--reason <CIDR> "新理由"]...
    [--confirm <收据ID>]
uv run python scripts/swt.py network recover --name <容器名> [--repo <主仓>] [--confirm <收据ID>]
```

均可加 `--records-root`. show 只读, 地址旁显示用途/历史未记录理由及自动项, 不一致只报告. update 仅运行中 whitelist 的独占配置目标; 停止/retired/旧共享记录/身份替换/未知规则均拒绝, 不自动迁移或收编. 同一请求可增删多条, 未涉及条目/自动项/其他容器保留. 仅 --reason 更正理由不重建规则; 自动项已变化时先用无用户变更的 update 单独审批同步, 再改理由.

有变化先出 DECIDE 和差异, 逐字转述, 等我批准后带指定 `--confirm 收据ID` 重跑, 不凭空填写 ID. 相关状态变化重新批准. 注意网段实际范围/重叠提示: 删 /32 不等于收回更大网段或自动 DNS 仍放行的权限, /0 是全部 IPv4/全部端口. 无变化直接返回 0. NETWORK 是末行 JSON, 返回码沿用 0/1/2/3/4, 不解析成 STATE. 成功检查包含规则/SSH/只读本地 Git 桥/DNS 规则, 不代表上游 DNS 或任务服务已实测.

中断/回退失败保留 network-change, update/birth/resume 不得绕过. recover 只恢复本工具事务的旧状态, 也先预览并审批; 原完整 ID 仍在的停止目标只恢复记录, 不启动. 未知状态或写进程未确认结束先报告, 不自动停/重启/清表. 细节见 [reference/ops.md](reference/ops.md).
完成标准: 按 NETWORK.stage/checks/pending 如实报告, 失败回退仍是失败, 未完成状态明确交还给我.

## 终结 (terminate)

```text
uv run python scripts/swt.py terminate [--repo <主仓>] [--branch <母体分支名原文>] [--name <容器名>] [--force]
```

按容器定位, 多个候选时指定 `--name` 或先用 `--branch` 缩小范围. 未提交改动 (包括未跟踪文件), 有未落母体的提交, 或无法检查 (ssh 不通/容器已停) 均按脏处理; 仅落后母体不算脏. 脏时脚本出 DECIDE 并提醒确认容器内 agent 已停手, 我答复后带 `--force` 重跑, 先留审计记录再删. 成功时删目标防火墙规则与容器, 本对最后一个容器终结才收本对 daemon, 其他对不动. **母体目录与配置留存**, 母体存删由我另走 `use-worktree` 流程决定. 运行记录留存并置为 idle, 本容器 ssh 私钥/密码记录和 Maven settings 快照清除.
完成标准: 目标容器及应收的本对 daemon 已灭, 母体未被修改, 运行记录为 idle, 目标凭据/快照已清除.

## 按需参考

- 登录/委派容器内 pi, 审阅母体或排查 web/显示 → [reference/living.md](reference/living.md); 设备侧拉窗/容器投信 → [reference/pull-window.md](reference/pull-window.md); 信箱服务/配置 → `mailbox` skill 的 `reference/mailbox.md`. 信箱缺席不阻断 birth/terminate.
- 修改容器提示词/env.conf 或将仓库变更同步到使用现场 → [reference/maintenance.md](reference/maintenance.md).
