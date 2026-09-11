# Handoff 2026-09-11 (四) - netns 多容器修复完成, 等原验收会话通知

## 使命与结果

已按 `2026-09-11-netns-multi-container-fix.md` 完成三个任务. 代码和测试提交在 `c4131a8` (`v2` 分支).

### 任务 1: netns 根治

- birth/resume/resume 网络状态检查/terminate/switch 清理全部按目标容器当前 `podman inspect` 的 `NetworkSettings.SandboxKey` 定位.
- runtime 中的旧 netns 不再作为 stop/start 后的定位依据.
- `pasta_netns()` 的无目标兼容兜底只接受全机唯一 pasta 实例, 多实例直接报错, 不再取首个进程.
- terminate 只处理目标容器和 runtime 中已登记兄弟容器的 inspect netns, 不会把 nft 规则写入或删除到未登记干扰容器.
- 新增真实回归: 干扰容器先启动时, birth/resume 的目标规则仍只落在目标容器自己的 netns.

### 任务 2: m12 测试改造

- 6080 断言按宿主端口状态分支: 空闲时要求 6080, 被占时要求回环动态端口.
- 多容器 nft 断言改为逐容器读取 SandboxKey, 不再通过 pasta 进程顺序找 netns.
- 新增 `test_ts1xx_hostname_*`: 无 `--hostname` 出 DECIDE, 显式 hostname 落到 `.Config.Hostname`, 非法 hostname 在资源创建前 exit 2.
- 新增 birth/resume 干扰容器回归.
- m07 的旧 Containerfile 断言和 alpine 构建夹具同步到已有的 `chown -R bolo:bolo /home/bolo` 镜像契约.

### 文档

- `DECISIONS.md` 补 D047, D048, F015.
- `SKILL.md` 补 netns 身份绑定风险说明, 保留原 whitelist 风险说明.
- ISSUE-11 等价矩阵更新为当前测试名和逐容器 SandboxKey 核验方式.

## 验证

- m12 修复后独立全量: `90 passed`.
- 无其他 swt 容器场景:
  - m07 最终全量: `35 passed`.
  - m09/m12 在同一场景全量通过; 初次合跑仅暴露 7 个 m07 旧夹具/断言问题, 修正后 m07 单独复跑全绿.
- 有并存 swt 容器场景:
  - `uv run --with pytest pytest -q tests/test_swt_m07.py tests/test_swt_m09.py tests/test_swt_m12.py`
  - `150 passed`.
- 额外定向 netns/hostname/6080 回归: `6 passed`.
- `uv run python -m py_compile ...` 和 `git diff --check` 通过.

## 现场状态

- 演练容器 `swt-skill-optimization` 已恢复 `running`.
- restore 使用了 `swt.py resume --repo /home/bolo/Workspace/skills --confirm`.
- 恢复后显示栈为 `degraded`: `x11vnc` 未监听 5900; swt 已按既有 D041 语义继续提供终端工作, 不阻断恢复. 该状态不是本次 netns 修复引入, 需原验收会话后续决定是否诊断.
- 当前演练容器 SandboxKey: `/run/user/1000/netns/netns-5cf13bee-a999-097a-4d28-413a0083b6f5`.
- 未运行 `uv run python sync-to-pi.py`, 因交接要求留给用户决定.
- 未 push 到 origin.

## 下一步

本会话已完成实现、回归、提交和现场恢复. 等用户通知原验收会话决定是否重启 M10 全链验收.

## 涉及文件

- `workflow/use-sandbox-worktree/scripts/swt.py`
- `workflow/use-sandbox-worktree/SKILL.md`
- `tests/test_swt_m12.py`
- `tests/test_swt_m07.py`
- `docs/changes/use-sandbox-worktree/DECISIONS.md`
- `docs/changes/use-sandbox-worktree/issues/ISSUE-11-equivalence-retire.md`
