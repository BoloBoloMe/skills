# use-sandbox-worktree 五场景脚本 (MILESTONE-12) Execution Spec

## 权威输入

- Decisions: `docs/changes/use-sandbox-worktree/DECISIONS.md` — 核心 D025-D038 (M11 拍板), 上游 D007-D013 (母体/写面/终结/换版), D014-D024 (镜像/记录根/herdr)
- 设计稿: `docs/changes/use-sandbox-worktree/milestone-11-design-caller.md` (caller 骨架; 凡与 D026-D038 冲突处以 D 账本为准 — 设计稿早于反方修正)
- ADR: `docs/adr/0009-swt-five-subcommands-decision-receipt.md`
- AFK 补钉: `docs/changes/use-sandbox-worktree/UNAUTHORIZED_DECISIONS.md` (U-001..U-009, 含收据机制/runtime 布局/自动 allow/扩展形态)
- 下沉来源 (只读, ISSUE-11 前禁删): `workflow/use-sandbox-worktree/scripts/e2e-smoke.py` (M03 已实跑验证的阶段函数)
- 复用接口 (只读调用, 各自测试已钉): `workflow/use-sandbox-worktree/scripts/image-prep.py` (match), `workflow/use-sandbox-worktree/scripts/net-firewall.py` (apply/show/clear; ISSUE-06 扩展), `workflow/use-worktree/scripts/slug.py`
- 时序事实: `docs/changes/use-sandbox-worktree/milestone-04/MILESTONE-04-findings.md` F-M04-02 (netns 生命周期, start 后立即注入)

## 全局允许范围

- 新建 `workflow/use-sandbox-worktree/scripts/swt.py`, `tests/test_swt_m12.py`
- 修改 `workflow/use-sandbox-worktree/scripts/net-firewall.py` (D032 扩展, U-008), 增补 `tests/test_swt_m04.py` (既有用例不改)
- 本 spec, `issues/ISSUE-05..11`, `UNAUTHORIZED_DECISIONS.md`
- ISSUE-11 限定: 删 `workflow/use-sandbox-worktree/scripts/e2e-smoke.py` 与 `tests/test_swt_m03.py`; 字面修补 `docs/changes/use-sandbox-worktree/TECHNICAL.md` (M03 遗留缺口 2/3)
- /tmp 测试夹具; `--records-root /tmp/...` 隔离

## 全局禁止范围

- 禁止修改其他 skills 的任何文件; 禁止触碰用户真实仓库 (测试全走 /tmp 夹具)
- 禁止新增 git hooks (BR-005); 禁止容器内真远端地址或凭据 (BR-001)
- 禁止 birth 自动构建镜像 (D035); 禁止 resume 走 clear+apply (D032); 危险操作禁止藏进通用入口 (D028)
- 禁止改 roadmap 状态文件 (probe 会话职责); 禁止改 DECISIONS.md — spec 与 D 账本冲突时停止上报
- 禁止删 e2e-smoke.py / test_swt_m03.py (ISSUE-11 等价矩阵全绿前保留为回归基线, D036)
- 禁止引入仓库新依赖 (单文件 stdlib, 沿用 M03/M07 形态)

## 完成定义

- 五子命令 (birth/resume/status/terminate/switch) 按 D025-D038 + 本 spec 实现, `uv run --with pytest pytest tests/test_swt_m12.py` 全绿
- D036 等价矩阵逐条有落点且断言独立外部状态 (`git config --get-all` / `podman ps` / nft 表 / 母体文件落地), 不只信 STATE
- e2e-smoke.py 退役 (删文件), test_swt_m04.py 既有用例 + 新增用例全绿, test_swt_m07.py / test_swt_m09.py 回归绿
- TECHNICAL.md 字面缺口 (2)(3) 修补 (M03 遗留)

## 测试策略

- 全部打在 swt CLI 接缝: 退出码 + stdout DECIDE 行 + 末行 STATE json + stderr 首行标签 + 独立外部状态; 无单元层 (例外: 纯计算 helper 若出现, 随用例需要)
- mock/fake 仅限 /tmp 文件系统夹具仓与 PATH 环境操控 (exit 4 路径); 容器/podman/git/nft 真跑 (M03 已证形态有效)
- 测试夹具: `/tmp/swt-m12-<rand>/srv/<reponame>/` 主仓 + `--records-root /tmp/swt-m12-<rand>/records`; 母体/客户端克隆在 srv 之外; 夹具仓无 origin (BR-001 物理排除)
- 容器镜像: `localhost/swt-m03:latest` (无则 build, U-006); match 路径用 scratch 伪镜像 (M07 形态)
- 环境依赖缺失 (podman/git/nft) → 失败并打印缺失项, 不静默 skip

## 关键接口契约 (U 系列补钉汇总, 实现前必读)

CLI 骨架:

```text
swt birth     --repo <主仓> --branch <母体分支名原文> [--base <源 ref>] [--name <容器名>]
              [--mode whitelist --allow <CIDR>]... | [--mode blacklist [--deny <CIDR>]...]
              [--image <ref>] [--requirements <file>] [--new-mother | --reuse-mother]
swt resume    --repo <主仓> [--name <容器名>] [--confirm]
swt status    --repo <主仓>
swt terminate --repo <主仓> [--name <容器名>] [--force]
swt switch    --repo <主仓> --to <目标分支名原文> [--force]
# 全子命令共用: [--records-root <dir>]  (缺省 ~/.agents/sandbox-worktree)
```

- `--repo` 缺省从 cwd 推导主仓 (`git rev-parse --git-common-dir` 取主仓 .git 的父目录, D025); 推导失败 exit 2.
- slug: `uv run workflow/use-worktree/scripts/slug.py <project> main <分支名原文>` 取 `dir=` 值 (M03 契约); 母体分支名 = 母体目录名 = 该值; 容器缺省名 `swt-<dir值>`, `--name` 覆盖 (D031).
- exit code: 0 成功 / 1 DECIDE / 2 前置 (未动任何资源) / 3 中途可重入 (PARTIAL 文案列唯一人工恢复路径, D037) / 4 环境错误. stderr 首行 `FAIL|PARTIAL|ENV <人话>`; 原生报错原文透传后续行.
- stdout 末行 `STATE {...}` 单行 json, `schema:1`, 字段: repo, mother{branch,dir,exists,worktree-dirty}, config{swt-form}, daemon{addr,port,orphan}|null, containers[]{name,podman-id,state,ssh-port,image-digest,retired,dirty{uncommitted,unpushed,relation,reachable}}, image{ref,digest,verdict,newer-available}|null, network{mode,table-present,auto-allow}|null. 只加字段不改名.
- DECIDE 行: `DECIDE <id> <kind> <问题人话> 选项: <flag 形态>`, 首次改任何资源前一次列全 (D026); 收据机制见 U-002; runtime/锁/审计见 U-003; whitelist 自动 allow 见 U-004; switch 目标不存在见 U-005.
- 脏检查口径 (D029): 未提交含未跟踪; 未 push = 容器 HEAD vs 主仓 `refs/heads/<母体分支>`, `merge-base --is-ancestor` 分 ahead/behind/diverged, 纯 behind 不算脏; ssh 不可达/容器已停 → unknown 视同脏.
- birth 顺序: 前置 (环境 exit 4 含 git `!` 行为级重验 U-007; 单活动母体不变量 D010) → DECIDE 列全 → 母体建/复用 (脏母体复用 exit 2) → config 写入语义 (沿用 e2e-smoke: 快照+写前校验, 错值中止不覆盖) → config 校验 → daemon 拉起 (监听兜底顺序沿用 e2e-smoke) → 镜像判定 (D035) → 容器 create+start → **立即 nft apply (fail-closed, F-M04-02)** → ssh key 注入+BatchMode 断言 → 容器内 clone -b 母体分支 + 读面断言 → runtime `stage=born`.
- resume 序列 (D030/F-M04-02): DECIDE gate → 收 stale daemon → start 容器 → daemon 重拉 → nft 重注入 (--merge 语义, 禁 clear+apply) → probe/ssh 校验. retired 容器 resume exit 2 (D033); runtime 母体分支 ≠ 当前授权 (config 例外) → exit 2.
- terminate: 按容器粒度 (D029), 脏 → DECIDE + `--force`; --force 先写 audit.jsonl 再删; nft `remove --container-ip`; 母体保留 config 不动; 最后一个容器终结后母体级资源仅闲置不删.
- switch (D010 原子序): 旧母体全部容器逐个脏检查 → 脏 exit 1 需 --force → 停全部容器+daemon → nft remove → 校验目标 (U-005) → 改 hideRefs 例外 → get-all 断言 → 旧容器 runtime 标 retired (D033). 不删旧母体, 不建新容器.

## 任务图

- ISSUE-05: `issues/ISSUE-05-swt-skeleton-status.md`; 骨架+协议底座+status; 依赖: 无.
- ISSUE-06: `issues/ISSUE-06-net-firewall-remove.md`; D032 扩展; 依赖: 无.
- ISSUE-07: `issues/ISSUE-07-swt-birth.md`; birth 全链; 依赖: ISSUE-05, ISSUE-06.
- ISSUE-08: `issues/ISSUE-08-swt-terminate.md`; terminate+脏检查+审计; 依赖: ISSUE-07.
- ISSUE-09: `issues/ISSUE-09-swt-switch.md`; switch+retired 标记; 依赖: ISSUE-08 (脏检查实现).
- ISSUE-10: `issues/ISSUE-10-swt-resume.md`; resume+retired 拒绝; 依赖: ISSUE-09 (retired 写入方).
- ISSUE-11: `issues/ISSUE-11-equivalence-retire.md`; D036 等价矩阵+e2e-smoke 退役+TECHNICAL 字面修补; 依赖: ISSUE-05..10.

## 覆盖矩阵 (D036 等价条目 → 落点)

- 拒绝矩阵 (新分支/tag/non-ff/删除) → ISSUE-07 birth 后容器内推送断言 (沿用 e2e-smoke smoke 段下沉)
- 母体脏树拒收 → ISSUE-07
- daemon 不带 --export-all → ISSUE-07 (命令行审计断言, 下沉 NB-003)
- config 校验先于 daemon 启动 → ISSUE-07 (故障注入, 下沉 TC-002)
- clone 检出母体分支 → ISSUE-07
- push 回流落地 → ISSUE-07
- D008 多值 config 既有值/错值/幂等重跑 → ISSUE-07
- ssh 不可达与已停容器视同脏 → ISSUE-08
- 强拆审计登记 → ISSUE-08
- 中途清理与重复 birth → ISSUE-07/08 (重入状态机)
- 多容器共享母体互不影响的 resume/terminate/nft → ISSUE-08/10
- switch 中途失败与旧容器 retired → ISSUE-09
- 收据指纹比对/一次性/状态漂移重问 (D026) → ISSUE-07 首落地, 08/09/10 各自 DECIDE 路径沿用
- 上述全部断言独立外部状态 (D036 明文)

## 全局风险和停止条件

- spec/U 系列与 D 账本字面冲突 → 停止上报.
- 需要扩大允许范围 (触碰真实仓/其他 skills/新增依赖) → 停止上报.
- 镜像真构建 (image-prep build) 不是本变更内容; 测试只用现成/伪镜像.
- daemon 监听地址探测不可行时沿用 e2e-smoke 兜底顺序, 不停止.
