# 交接: swt-cross-host-access 沙盒工作树 birth 进行中 (2026-09-13)

## 任务

为 swt-cross-host-access 需求 (M1 已关闭, 剩余 M2-M9) 创建沙盒工作树, 后续里程碑在容器内完成. 当前卡在 birth 第一步 (网络模式盘点), 等用户拍板.

## 已完成的动作与现状

1. **仓库布局迁移** (非标准 → 标准, 用户拍板选项 b):
   - 主仓从 `/home/bolo/Workspace/skills` 整体搬到 `/home/bolo/Workspace/skills/skills-v2` (主 worktree, 分支 v2, 干净).
   - `/home/bolo/Workspace/skills/` 现在是项目目录, 不是 git 根; 旧会话 cwd 路径已失效.
   - 本地执行过 `git remote set-head origin v2` (只改本地符号引用): origin/HEAD 原指向 main, 但本仓实际主线是 v2, status.py 按 origin/HEAD 推主分支名, 不改则布局恒判 nonstandard.
   - 已跑 `git fetch --all --prune`.
2. **母体 worktree 已建好** (use-worktree 流程): `/home/bolo/Workspace/skills/skills-v2-swt-cross-host-access`, 分支 `swt-cross-host-access`, 基于 v2 @ 7303c9d, 干净.
3. **swt status 快照** (birth 前): `stage=idle`; 镜像 `localhost/sandbox-worktree/skills:2026.09.13-2` verdict=REUSE (`newer-available` 只是提示, 不阻塞); 上次运行网络模式为 blacklist.

## 卡点: 等用户拍网络模式

已向用户摆出选项, 尚未答复:
- **whitelist** (推荐): 默认拒, 需用户提供容器工作所需站点 (尤其容器内 pi 要调的 LLM API 域名), 由 agent 解析成 IP/CIDR 传 `--allow`. git 走 unix socket 桥, 不占白名单.
- **blacklist**: 默认放, 只断 `--deny` 条目.

## 环境事实

- swt 脚本: `uv run python ~/.agents/skills/use-sandbox-worktree/scripts/swt.py`.
- 记录根: `~/.agents/sandbox-worktree/`; 需求清单已有 `~/.agents/sandbox-worktree/skills/requirements.md` (镜像 REUSE 即靠它匹配).
- env.conf: 全局只有 `CHANG_ZHI_AI_WORK` 一条; 无项目级 env.conf.
- birth 命令形态: `uv run python scripts/swt.py birth --repo /home/bolo/Workspace/skills/skills-v2 --branch swt-cross-host-access ...`; 出 DECIDE 行须逐字转述用户, 带 flag 重跑同一命令.
- 镜像无需重建 (REUSE), birth 内部会自动跑 match.
- herdr 注意: 本机 pi 提交键 `alt+\`; send-text 后须单独 send-keys 提交; 详见 `~/.pi/agent/herdr-pi.md`.

## 必读推荐

- `~/.agents/skills/use-sandbox-worktree/SKILL.md` — birth 后续步骤 (第二~四步) 与交付包规格的唯一权威来源; 新会话未必自动加载该 skill, 需手动读.
- `/home/bolo/Workspace/skills/skills-v2/docs/changes/swt-cross-host-access/roadmap/ROADMAP.md` — 需求全貌, 里程碑依赖图, 已关闭决策; 判断后续容器内工作内容的依据.

## 路线图

1. 用户在 v2 分支推进 swt-cross-host-access 需求, M1 (信箱盘问) 关闭, 路线图定稿.
2. 用户决定剩余里程碑 (M2-M9) 在沙盒工作树中完成 → 发起本 birth 流程.
3. 已完成: status 盘点 (idle) → 布局迁移 → 母体 worktree 建立.
4. 当前: 网络模式盘点待拍板 → birth 执行 (预计出 DECIDE: 母体复用/网络模式确认) → 交付包齐发 → 用户 ssh/herdr 进容器驱动 pi 干 M2/M4/M6 (三者互不阻塞).
5. 目的地: 三类场景 × 两个访问位置真机跑通, SKILL.md 固化实证现实 (详见 ROADMAP.md 目的地节).
