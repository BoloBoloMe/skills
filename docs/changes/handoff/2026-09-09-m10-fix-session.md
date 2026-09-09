# Handoff 2026-09-09 (二) — M10 命名缺陷已修, 测试基线回绿, 待继续全链实测

## 使命与现状

probe 遍历收尾 `docs/changes/use-sandbox-worktree/roadmap/`, 前沿 = MILESTONE-10 (最后一个). 本会话原计划全链重新演练, 建环节第零步首次实测即暴露命名缺陷, 用户拍板转为修复会话. 修复已提交 (3e3815e), 下个会话从 birth 继续.

验收链 (不变): 建 (第零步已完成 → birth) → 干 (用户 ssh/herdr 进容器改 `workflow/deliberate/SKILL.md`) → 推 → 展示链 → 登录墙 → 拆.

## 环境现状 (比上一份 handoff 有推进)

- 母体已建 (第零步完成): worktree `/home/bolo/Workspace/skills-v2-skill-optimization`, 分支 `skill-optimization` @ 修复提交, 干净.
- base 镜像已重建: `localhost/sandbox-worktree/base:2026.09.09-3` (含 codex-config 烘配, 旧账已清).
- skills 项目层镜像: 无, 下次 birth 走 BUILD-NEW → DECIDE 出示 `~/.agents/sandbox-worktree/skills/requirements.md` (codex+kimi+codex-config, 用户早已确认).
- 测试镜像 `localhost/swt-m03:latest` 已重建为 bolo 用户版.
- 浏览器项目层镜像未建 (登录墙环节才需要, requirements-browser.md 的 bolo 路径仍未实测).
- swt 状态: 无容器/无 daemon/无防火墙规则; 主仓 config 未动.
- 网络模式已拍板: **blacklist, 无 --deny 条目**.

## 本会话发现与修复 (3e3815e)

1. **命名缺陷 (第零步首次实测暴露)**: swt `resolve_branch_slug` 硬编码来源 "main" 且把母体分支名前綟化, 与 use-worktree 产出 (分支=目标名原文, 目录=slug) 对不上, birth 找不到已建母体. 修为: `resolve_mother_branch` 原样返回目标分支名; `mother_dir_name` 用真实来源分支 (`default_branch`) 算 slug; 新增 `container_default_name` 净化分支名 (podman 名不允许 /). SKILL.md 第零步/第三步措辞同步修正.
2. **m12 测试基线红是既有问题** (7e94c0f 改 bolo 用户后 m12 未跑过; 8f80960 加 refs/remotes 后断言未跟): 61 红. 修复: swt-m03 测试镜像 agent→bolo + PermitUserEnvironment; m12/m09 陈旧断言 (clone 路径 58 处 /home/agent/workspace → /home/bolo/Workspace/feature/m12, hideRefs 四条目, fixture srv 路径). 结果: m07 30 + m09 26 + m12 84 全绿.
3. 遗留: m04 `NetworkModeTestCase::test_01_whitelist_default_deny` 环境性失败 (改动前即失败, nft 敏感, 未追查).

## 下会话从哪继续

```text
cd /home/bolo/Workspace/skills
uv run python workflow/use-sandbox-worktree/scripts/swt.py birth \
  --repo /home/bolo/Workspace/skills --branch skill-optimization --mode blacklist
```

预期: 找到已有母体 → DECIDE `mother-reuse` (答 `--reuse-mother`) + DECIDE `image-build` (BUILD-NEW, 先 `image-prep.py build` 再带 `--image` 重跑). 之后按 SKILL.md 走交付汇报 (ssh 双入口 + 双凭证 + herdr remote 双命令), 再交用户进容器干活.

注意: `--branch` 传 `skill-optimization` (修复后 = 分支名原文; 旧的"二次前缀化"教训已失效).

## 关闭 M10 前欠的簿记 (更新)

- DECISIONS.md 补记: (a) 上批: 母体同级位置/bolo home 字面复刻/herdr 进 base/固定密码/env.conf/双入口; (b) 中批: herdr 双命令必发/codex env_key 零秘密/base 烘配置/use-worktree 第零步; (c) 本批: **母体分支名=目标名原文 + 目录名=真实来源 slug 的命名对齐决策** (新增).
- 镜像: ~~base 待重建~~ (已建 2026.09.09-3); skills 项目层下次 birth 建; 浏览器项目层登录墙环节建.
- ~~测试陈旧引用~~ (已修); m04 环境性失败仍挂.
- 展示链: swt create 只映射 22 端口, present 8800 仅容器 IP 可达 — 用户要局域网访问即是新发现.
- 关闭动作: MILESTONE-10 头改已关闭 → ROADMAP.md 更新 → 评估未决迷雾 (运行期新站点需求/D037 救场回访) → 提交.
- 本地 v2 领先 origin 9 个提交未 push.
- skill 改动生效需 `uv run python sync-to-pi.py` (仍未同步; 演练用仓库内脚本不受影响).

## 必读推荐

1. `docs/changes/use-sandbox-worktree/roadmap/ROADMAP.md` + `MILESTONE-10.md` — 验收链与 probe 纪律.
2. `workflow/use-sandbox-worktree/SKILL.md` — 最新操作手册 (命名节已按修复改).
3. 本目录 `2026-09-09-m10-fresh-rehearsal.md` — 上一份交接 (演练背景与 codex 方案细节).
4. `~/.agents/sandbox-worktree/skills/requirements.md` — skills 项目层清单原文.
