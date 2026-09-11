# Handoff 2026-09-11 (三) — M10 验收中止, 移交: netns 多容器串台根治 + m12 测试改造

## 使命与现状

M10 全链重跑验收在 "建" 后连环暴露权限类故障, 用户拍板**中止验收**, 已修部分提交在 `2803030` (v2 分支). 本会话接手的剩余修复任务见下. 完成后由用户通知原验收会话决定下一步 (是否重启 M10 全链).

## 环境现状

- 仓库 `/home/bolo/Workspace/skills` 分支 `v2` @ 2803030, 干净; 本地领先 origin 11 个提交未 push.
- 演练现场保留未拆: 容器 `swt-skill-optimization` (镜像 skills:2026.09.11-3) 运行中, 母体 `skills-v2-skill-optimization`, blacklist 模式. 它既是"另一个容器"测试场景的现场, 也会干扰需要独占机器的测试 — 跑全量 m12 前须先 `podman stop swt-skill-optimization`, 跑完 `swt.py resume --repo ... --confirm` 恢复 (可能需答 DECIDE 收据重问).
- 镜像: base 2026.09.10-2 / display 2026.09.11-4 / skills 2026.09.11-3 (后两者含 home 属主兜底 RUN).

## 已修勿重复 (2803030 内)

1. auth.json: ro 挂载 → birth/resume 启动后注入 (D046, F014).
2. 构建期 home 属主: 清单条件 chown + image-prep 收尾 `chown -R bolo:bolo /home/bolo` 兜底 (F013).
3. swt-display 体检改 `--user bolo` (运行期 root 残留).
4. birth 新增 hostname DECIDE + `--hostname` (D047, 用户拍板: 主机名由 host-llm 推荐, 用户确认); m12 run_swt 对 birth 自动补 `--hostname swt-m12-host`.

## 待办任务 (用户已拍板方案)

### 任务 1: netns 张冠李戴根治 (安全事故级)

机制: `swt.py pasta_netns()` 用 `pgrep -af "pasta --config-net"` 取**第一个** pasta 进程的 `--netns`. 多 swt 容器并存时返回的可能是别的容器的 netns → nft 规则注入错命名空间; whitelist 模式下目标容器裸奔 (fail-open). 实测: 演练容器存活时 `TestTS5Resume.test_missing_target_rule_with_table_present_reopens_and_repairs` 必红, 停掉即绿. 另注意 stop/start 后容器 SandboxKey 可能变, runtime 里存的 netns 会过期.

修复方向 (用户已认可):
- 全程只用 `podman inspect` 的目标容器 SandboxKey 定位 netns.
- `pasta_netns()` 全局猜测降级: 仅当全机**唯一** pasta 进程时才可信, 多实例判不可用/报错, 绝不猜; 或按容器 PID 关联 pasta 进程 (更优, 若可行).
- 审计所有 `pasta_netns()` 调用点 (birth/resume/resume_network_status/terminate 清理), terminate 的候选并集逻辑也要审 (别往别人 netns 里注入/删除).
- DECISIONS.md 补 F015 (机制+实测) 与相应决策记录; SKILL.md 风险明示补一笔.

### 任务 2: m12 测试去独占假设

- `vnc-port == 6080` 类断言改为: 6080 空闲时断言 6080, 被占时断言回环动态端口 (HostIp==127.0.0.1, 端口>0). grep `6080` 全量过一遍.
- 新增回归用例: 并存一个干扰容器时 birth/resume 的 nft 注入落在目标容器自己的 netns (可复用 swt-m03 裸容器当干扰).
- hostname 专项用例 (test_ts1xx_hostname_*): 无 --hostname 出 DECIDE; 带 --hostname 落地 (`podman inspect .Config.Hostname`); 非法主机名 exit 2. (run_swt 自动应答不干扰, 专项用例显式传/不传.)

### 任务 3: 双场景全量回归

- m07/m09/m12 在 "无其他 swt 容器" (先停演练容器) 与 "有并存容器" 两种场景各跑一遍, 全绿.
- m04 的 `test_01_whitelist_default_deny` 环境性失败是既有挂账, 不在本次范围, 别追.

### 收尾

- 全部修复+测试绿后: 提交 (可分多笔), 恢复演练容器运行, 写新 handoff 汇报, 等用户通知原验收会话.
- skill 改动生效需 `uv run python sync-to-pi.py` — 不擅自跑, 留给用户决定.

## 必读

1. `workflow/use-sandbox-worktree/SKILL.md` — 现行操作手册 (含 D046/D047 新措辞).
2. `docs/changes/use-sandbox-worktree/DECISIONS.md` — D039-D047, F012-F014.
3. 本目录 `2026-09-09-m10-fix-session.md` 与 `2026-09-09-m10-fresh-rehearsal.md` — 背景 (登录墙环节已作废, 勿参考其形态).
