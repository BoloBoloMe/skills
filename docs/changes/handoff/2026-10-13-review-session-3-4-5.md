# 交接: 复盘候选 3/4/5

## 目标
我已采纳原会话复盘中的候选 3/4/5, 下一会话负责在 `skills-v2` 仓库落实并验证这些改进, 然后提交和推送. 原会话唯一一手来源为 ID `01a11b20-9107-70b3-a8fe-c9333f9203fc`, 日志 `/home/bolo/.pi/agent/sessions/--home-bolo-Workspace-ChangZhi-cz_sdk-cz_sdk-master--/2026-10-08T10-48-01-543Z_01a11b20-9107-70b3-a8fe-c9333f9203fc.jsonl`.

## 路线图
1. `2026-10-08 10:48` 我要求为 MyCard 补单金额校验需求创建沙盒工作树. agent 只建了 Git worktree; `11:00` 我追问 `"容器呢?"`, 随后才补建 Podman 沙盒. 这暴露普通 worktree 与容器沙盒的入口名称容易混淆.
2. `2026-10-09` agent 在沙盒完成 MyCard 代码和测试, 但私有 Maven 依赖无法取得, 当时没有 Maven 构建和测试结果.
3. `2026-10-10 07:44` 我要求 noVNC 直接开放到局域网; agent 建立了无认证 noVNC 的局域网转发服务.
4. `2026-10-13 03:49-03:52` 容器和 MyCard worktree 已终结/移除, `git worktree prune` 已执行, 远端分支保留. noVNC 转发服务也已移除, 本轮不需要恢复它.
5. 复盘后我只采纳候选 3/4/5: noVNC 局域网暴露的风险提示, `swt.py status` 的网络状态误报, 以及 `"沙盒 worktree"` 意图的技能路由. 其他候选不在本次交接范围.

## 已采纳项
### 3. noVNC 局域网暴露前说明安全边界
原会话 `2026-10-10 07:44:50` 收到直接开放局域网的要求; `07:49:04` agent 宣布将 `192.168.65.165:6080` 转发到容器 noVNC, 并创建用户级 systemd 服务; `07:53:40` 局域网入口返回 HTTP 200. 现有 noVNC 无认证, 可控制已登录浏览器. 改进应在 `workflow/use-sandbox-worktree/SKILL.md` 的对应流程中, 明确要求在暴露回环以外前读取 `reference/risks.md`, 说明风险并取得明确确认, 再决定是否增加认证或开放.
### 4. 修正 status 对容器防火墙状态的误报
原会话 `2026-10-09 02:21:52` 的 `swt.py status` 报 `table-present=false`; `02:37:00` 通过 `net-firewall.py show --netns <容器 SandboxKey>` 证实目标容器的 `inet swt` 表实际存在. 当时的诊断指出 status 的探测用了默认网络命名空间, 而 `resume_network_status()` 使用容器自己的命名空间. 改进应让状态检查针对每个目标容器的实际 SandboxKey, 并在 `tests/test_swt_m12.py` 增加回归覆盖.
### 5. 区分 Git worktree 与容器沙盒
原会话 `2026-10-08 10:48:01` 开始创建 `"沙盒工作树"`; agent 按 `use-worktree` 只创建 Git worktree, `10:59:31` 汇报完成后, 我于 `11:00:41` 追问 `"容器呢?"`. 改进应在 `workflow/use-worktree/SKILL.md` 与 `workflow/use-sandbox-worktree/SKILL.md` 之间加清楚的入口指针: 前者只处理 Git worktree, 要求创建容器沙盒时还须走后者.

## 当前仓库状态与约束
仓库 `/home/bolo/Workspace/skills/skills-v2`, 分支 `v2`, HEAD `0888f97`, 跟踪 `origin/v2`. 交接开始时工作区已有未提交更改, 与本次改进重叠的文件包括 `workflow/use-sandbox-worktree/SKILL.md`, `workflow/use-sandbox-worktree/reference/risks.md`, `workflow/use-sandbox-worktree/scripts/swt.py`. 其他未提交项还包括 `reference/errors.md`, `reference/image-prep.md`, `reference/ops.md`, `scripts/image-prep.py`, `tests/test_agent_templates.py`, `tests/test_agent_templates_safety.py` 及 `agent-templates/`, `reference/agent-templates.md`, `scripts/agent-launch.py`, `scripts/agent-runtime.py`, `scripts/agent-template.py`, `scripts/agent_config/`.
这些现存改动不属于本交接文档, 本文档提交只包含自身. 下一会话先查看实际差异, 保留原有修改; 若与候选 3/4 重叠且无法安全合并, 先向我确认. 不要用全量 `git add` 把这些内容带入提交.

## 必读推荐
1. `docs/changes/handoff/2026-10-13-review-session-3-4-5.md` - 本文记录我采纳的范围, 原会话证据, 当前仓库状态和需要保护的未提交修改.
2. `/home/bolo/.pi/agent/sessions/--home-bolo-Workspace-ChangZhi-cz_sdk-cz_sdk-master--/2026-10-08T10-48-01-543Z_01a11b20-9107-70b3-a8fe-c9333f9203fc.jsonl` - 唯一一手来源; 需要核实候选原话, 具体时间和工具结果时查阅, 不用其他会话代替.
3. `workflow/use-sandbox-worktree/SKILL.md` 与 `workflow/use-sandbox-worktree/reference/risks.md` - 分别说明 noVNC 的现行端口流程和无认证风险, 决定候选 3 应放在哪个入口及如何表达确认边界.
4. `workflow/use-sandbox-worktree/scripts/swt.py` 与 `tests/test_swt_m12.py` - `pasta_netns()`, `resume_network_status()` 和 status 汇总在这里; 前者是修复候选 4 的实现入口, 后者是现有测试套件.
5. `workflow/use-worktree/SKILL.md` - 普通 Git worktree 的实际职责, 用于落实候选 5 的交叉指针, 不改变既有 Git 安全规则.
6. `README.md` - 说明本仓库内容如何通过 `uv run python sync-to-pi.py` 部署到 Pi; 若需要同步生效, 按仓库现有流程处理.
