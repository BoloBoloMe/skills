# Handoff 2026-09-09 — use-sandbox-worktree M10 环境已归零, 待全链重新演练

## 使命与现状

probe 遍历模式收尾 `docs/changes/use-sandbox-worktree/roadmap/`, 前沿 = MILESTONE-10 (最后一个, 关闭即达目的地). 用户在上一演练中途拍板: SKILL.md 已迭代到与建旧容器时的行为差距较大, **上个沙盒已彻底拆除, 环境归零, 新会话从头重新体验全流程**.

验收链 (全部待跑): 建 (含新增的第零步) → 干 (用户 ssh/herdr 进容器改 `workflow/deliberate/SKILL.md`, 想法仍模糊, 可用容器内 pi+deliberate 推进) → 推 (ff-push 回流母体) → 展示链 (present 容器分支) → 登录墙 → 拆.

## 环境现状 (已归零, 可直接 birth)

- `swt status` 输出 "什么都没有", `swt-form: false`; 容器/镜像/母体/守护进程/防火墙规则/hideRefs/运行时档案全清.
- 保留项 (有意保留, 勿删):
  - 全局 `~/.agents/sandbox-worktree/env.conf`: 含 `CHANG_ZHI_AI_WORK` (llm 中转站密钥的变量名, 值在 host `~/.bashrc`, 文件不存秘密). 所有新项目容器自动继承.
  - `~/.agents/sandbox-worktree/skills/requirements.md`: skills 项目层清单 (codex + kimi + codex-config 条目), 已经用户确认; 下次 birth 走 BUILD-NEW → DECIDE 出示该清单.
  - `~/.agents/sandbox-worktree/{base,skills}/builds/`: 历史构建记录 (镜像已删, 记录仅作历史).

## 本次会话改动 (均已提交到本地 v2)

1. `bb4732c` SKILL.md: herdr remote 交付强化 — birth 收尾必须同时打印本机 (`ssh://bolo@127.0.0.1:<端口>`) + 局域网 (`ssh://bolo@<host-LAN-IP>:<端口>`) 两条完整命令, 用户会在本机/远程机间切换.
2. `02b9d2b` codex 中转站零秘密方案:
   - codex 配置文件用 `env_key = "CHANG_ZHI_AI_WORK"` 从环境变量取密钥, 文件零秘密 — 不需要"创建时填值"机制.
   - SKILL.md 镜像管理节加推导规则: 项目层清单含 codex 时必须附 `codex-config` 条目 (base64 写法防引号问题; probe 必须输出版本号, 用 `grep -c .`, `test -s` 无输出会导致构建校验 FAIL).
   - base 层 Containerfile + DEFAULT_BASE_REQUIREMENTS 已加 codex-config — **尚未重建 base, 未生效**; base 重建须用户明说, 且因 base-digest 硬谓词会连带所有项目层镜像过期.
   - 顺手修 m07 两处 /home/agent 陈旧断言 (30 用例全绿).
3. `4e16059` SKILL.md 诞生节加**第零步**: 必须先用 `use-worktree` skill 为项目建工作树分支 (slug 命名来自它), 再走 birth; 已建好的母体 birth 会走 DECIDE `--reuse-mother` 路径 (实测兼容).
4. 环境清理: terminate → 拆母体 (无独有提交) → 删 7 个镜像 → 清 hideRefs → 清运行时档案.

## 新会话演练要体验到的新行为 (验收重点)

- 第零步 use-worktree 先建树 → birth 识别已有母体走 reuse 决策.
- birth 交付两条 herdr remote 命令 + ssh 双入口 + 双凭证 (密码见 SKILL.md 风险明示节, 密钥在运行时目录).
- 容器内 codex 经中转站可用: env.conf 继承变量 + config.toml env_key. base 未重建前, config.toml 来自 skills 项目层清单的 codex-config 条目 (BUILD-NEW 时烘入), 效果等同.
- 上个会话已验证: `codex exec` 经中转站真跑通 (2,717 tokens).

## 关闭 M10 前欠的簿记 (累积)

- DECISIONS.md 补记两批拍板: (a) 上批: 母体同级位置/bolo 用户 home 字面复刻/herdr 进 base/固定密码/env.conf 机制/双入口交付; (b) 本批: herdr 双命令必发/codex env_key 零秘密 + 推导规则/base 烘配置/use-worktree 第零步.
- 镜像待重建: base (codex config 生效) + skills 项目层 (codex-config 条目) + 浏览器项目层 (requirements-browser.md 已改 bolo 路径未实测, 登录墙环节暴露). base 一重建全部连带, 可攒一次做.
- 测试陈旧引用待修: `tests/test_swt_m09.py:418`, `test_swt_m12.py:631,685` (还是 /home/agent); `test_swt_m04.py::NetworkModeTestCase::test_01_whitelist_default_deny` 环境性失败 (改动前即失败, 疑似 nft 环境敏感, 未追查).
- 展示链注意: swt create 只映射 22 端口, present 8800 仅容器 IP 可达 (host 直连行, 局域网不行) — 用户要局域网访问即是新发现.
- 关闭动作: MILESTONE-10 头改已关闭 → ROADMAP.md 已关闭决策+前沿+连线图 → 评估未决迷雾 (运行期新站点需求/D037 救场回访) → 提交.
- 本地 v2 领先 origin 11 个提交未 push.
- 仓库规则: skill 改动只改 `workflow/` 侧, 生效需 `uv run python sync-to-pi.py` 同步 (当前未同步, 演练直接用仓库内脚本).
- 操作教训: `swt birth --branch` 传原始名 (如 `m10-rehearsal`), 传完整 slug 会被二次前缀化成 `skills-main-skills-main-...`.

## 必读推荐

1. `docs/changes/use-sandbox-worktree/roadmap/ROADMAP.md` + `MILESTONE-10.md` — 目的地/验收链定义, probe 遍历纪律 (DECIDE 逐字转述, HITL 不代答, 每轮停).
2. `workflow/use-sandbox-worktree/SKILL.md` — 最新操作手册 (含第零步/herdr 双命令/codex 推导规则/env.conf/风险明示), 演练照它走.
3. `docs/changes/use-sandbox-worktree/DECISIONS.md` — 补记格式参照 (D018/D023 等历史脉络).
4. `docs/changes/handoff/2026-09-09-m10-rehearsal.md` — 上一份交接: 8 个已修缺陷清单与上批设计变更原文.
5. `~/.agents/sandbox-worktree/skills/requirements.md` — skills 项目层清单原文 (codex-config 条目的 base64 写法参照).

## 路线图 (意图脉络)

1. 产品线 M01-M12 全关: 四脚本 + 契约落地.
2. M10 写 SKILL.md → 用户五轮审改 → 首次全链演练开机 (标的 skills 仓, blacklist, codex+kimi).
3. 首轮演练抓 8 缺陷 (全修), 用户顺势拍板 6 项设计变更; 干环节前因 env 变量缺失重建过一次容器 (验证 env.conf 机制与 reuse 路径).
4. 本轮: codex 零秘密方案落地 (env_key + 清单条目 + base 烘配), herdr 双命令与 use-worktree 第零步固化进 SKILL.md; 用户判定新旧行为差距大, 环境归零.
5. 当前: 新会话从头全链演练, 跑通 建→干→推→展示→登录墙→拆 即关闭 M10 达目的地. 剩约一半路程.
