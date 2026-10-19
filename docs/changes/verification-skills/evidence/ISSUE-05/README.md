# ISSUE-05 演练记录: 旧证据适用性与项目配方选择

本目录是 `docs/changes/verification-skills/issues/ISSUE-05-verify-change-applicability-recipes.md` 的行为证据. 全部结论来自真实 pi 会话在临时 Git 项目上的实际运行, 不是源码关键词断言.

## 待测对象

- 源文件: 本工作树 `workflow/verify-change/SKILL.md` (分支 `issue/05`), 三个版本都留了原件在 `logs/skill-versions/`:
  - `SKILL-v1-red.md` md5 `82cb7913d710dfaf3b898c56d17c618c`: 本 ISSUE 改动前的版本, 红演练用它.
  - `SKILL-v2-entry-recipe.md` md5 `cd7eabce6835454746fcfe6e8ff5e604`: 加了入口/配方选择与旧证据适用性规则, AC-010 的绿演练用它.
  - `SKILL-v3-final.md` md5 `45af75c2a10ff902286391bb4ad0160f`: 在 v2 上加了派工时定材料来源与报告行内引用要求, AC-009 的绿演练用它. v2 到 v3 的差异只有第 4 步一句加第 8 步一句, 见 `logs/skill-diff-v2-v3.txt`; 第 5, 6 步 (入口与配方规则) 在 v2, v3 中逐字相同, 所以 AC-010 的 v2 证据对最终版仍然成立.
  - `SKILL-v4-final.md` md5 `f66877da91ddc2ab7df7990aa17bb392`: 提交版. 只把第 7 步里那两段适用性说明从四条材料类型中间移到它们之后, 文字一字未改 (`logs/skill-diff-v3-v4.txt`, 两个版本排序后的行集合完全相同). 因此 v3 上跑出的 AC-009 行为结论对提交版仍成立.
- 覆盖范围: 只覆盖上述源文件与下面的加载方式, 不表示任何全局部署副本已更新; 未运行 `sync-to-pi.py`.

## 宿主与加载方式

- 宿主: Ubuntu 26.04 LTS (x86_64); herdr 0.9.4; pi 1.3.0; 字面 `python3` 实际由 `uv run python` 执行 (Python 3.14.7), `/usr/bin/python3` 为 3.14.4.
- 模型与深度: 指挥会话 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`; 子验收者由指挥会话按 `llm-select` 另选 (实测 `cli/glm-5.3-flash`, thinking `xhigh`).
- 启动形态: `herdr agent start <会话名> --kind pi --pane <窗格ID> -- --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`; `-a` 只给该次会话做一次性项目信任, 未改全局配置.
- 加载方式: 待测目录复制到临时项目的 `.agents/skills/verify-change/`, 在项目 cwd 开新 pi 会话, 用同一行 `/skill:verify-change <任务>` 点名加载. 全部任务文本见 `logs/dispatch-prompts.txt`.
- 实际加载来源核对: `logs/loaded-locations.txt` 从每个指挥会话的 jsonl 首条 `<skill name=... location=...>` 抽出实际展开的文件路径并算 md5, 与要测的版本逐一对上. 没有 `[Skill conflicts]` 段.

## 夹具

`setup-drills.sh` 在 `/tmp/orchestra-05/` 生成夹具, 全部是临时 Git 项目. 产品标准用 `workflow/to-spec/ac-draft.py preview/promote` 真实转正, 带真实确认标记, 转正后跑 `check-ac.py` 通过. 夹具里的关键文件另存到 `fixtures/`, 便于复核.

| 夹具 | 端口 | 用途 | 提交历史 |
| --- | --- | --- | --- |
| `/tmp/orchestra-05/board` | 18201 | 完整夹具母版 | `1dbbbe1` 初始 + 依赖 1.2; `86c9ae0` 旧运行记录; `d2e680c` 只改 `docs/notes.md`; `65b43e1` 依赖升到 1.3 |
| `board-r1` (clone, 分支 t1) | 18201 | AC-009 第 1 轮: 只改说明材料 | HEAD `d2e680c` |
| `board-r2` (clone, 分支 t2) | 18201 | AC-009 第 2 轮 (依赖变化) 与第 3 轮 (输入变宽) | HEAD `65b43e1`, 之后 `5f9544d` 新增 AC-004 |
| `norecipe` | 18201 | AC-010-1: 只有 PRODUCT.md + 源码 + README, 无 TECHNICAL/EXECUTION, 无配方 | `d1f656e` |
| `stalerecipe2` | 18321 | AC-010-2: 同一项目加一份过时配方 `.agents/skills/verify-board/SKILL.md` (参数 `--data-root`, 端口 18001, 期望 `version=relay-v1`) | `04a8dd6` |
| `red-board` | 18201 | 红演练 AC-009: 旧技能 + 说明材料与依赖同时变 | `70bcc79` |
| `red-board2` | 18201 | 红演练 AC-009: 旧技能 + 只改说明材料 | `d2e680c` |
| `red-stalerecipe` | 18201 | 红演练 AC-010: 旧技能 + 过时配方 | `d1f656e` |
| `stalerecipe` | 18201 | 作废的 AC-010-2 首夹具 (端口与 board 冲突), 记录见 `logs/dispatch-prompts.txt` | `d1f656e` |

旧运行记录 (`fixtures/old-evidence-dep-1.2/`) 是真跑出来的: 当时启动实例与仓库外的 relay 服务 (127.0.0.1:18290), 跑 health/status/report/sync 并保存原始输出与退出码, 记录内容为 `dep=1.2`, `sync-ok ... relay=ok`. 造完记录后删除了那份 relay 文件, 演练期间 18290 一直无监听, 所以 AC-003-1 的"依赖服务缺失"是真的缺失, 不是被验收者造出来的.

## 会话一览

| 轮次 | 会话 | 项目 | pi session id | 记录 |
| --- | --- | --- | --- | --- |
| 红 AC-009 (混合条件) | `i05-red009` + `acc-r1` | red-board | `01a154b6-4c8a-...`, `01a154b8-8f92-...` | `sessions/red-board/` |
| 红 AC-009 (只改说明材料) | `i05-red009b` + 子验收者 | red-board2 | `01a154bf-8ca9-...`, `01a154c0-88e2-...` | `sessions/red-board2/` |
| 红 AC-010 | `i05-red010` + 两轮子验收者 | red-stalerecipe | `01a154b6-5bf1-...`, `01a154b7-b950-...`, `01a154bb-cac9-...` | `sessions/red-stalerecipe/` |
| 绿 AC-009 第 1 轮 | `i05-g009r1` + `01a154d4-fe1a` | board-r1 | `01a154d3-7c5d-...` | `sessions/board-r1/` |
| 绿 AC-009 第 2, 3 轮 | `i05-g009r2` + `r2-verifier` + `r2-verifier2` | board-r2 | `01a154d8-0ad3-...`, `01a154d8-e9f1-...`, `01a154df-fc83-...` | `sessions/board-r2/` |
| 绿 AC-010-1 | `i05-green010a` + `verify-board-r1` | norecipe | `01a154bf-d2fb-...`, `01a154c0-d72b-...` | `sessions/norecipe/` |
| 绿 AC-010-2 | `i05-green010c` + `acc-stalerecipe2-r1` | stalerecipe2 | `01a154d0-656e-...`, `01a154d1-3da5-...` | `sessions/stalerecipe2/` |
| 作废: board 首轮 (目标与 HEAD 不符) | `i05-green009` + `acc-board-r1` | board | `01a154c0-128b-...`, `01a154c9-968c-...` | `sessions/board/`, 报告抄在 `drill-green-009-r1-extra-version-premise/` |
| 作废: stalerecipe 两轮 | `i05-green010b` + 两名子验收者 | stalerecipe | `01a154bf-e0ba-...`, `01a154c1-dba5-...`, `01a154c9-e9e1-...` | `sessions/stalerecipe/` |

全部演练会话已在收尾时用 `herdr tab close` 关闭; 收尾 `herdr agent list` 中没有本 ISSUE 的存活会话.

## 红演练 (先失败)

| 切片 | 目录 | 旧版实际行为 | 与预期失败的对应 |
| --- | --- | --- | --- |
| TS-001 AC-009, 混合条件 | `drill-red-009-mixed/` | 旧版没有适用性判断规则, 4 项全部重跑; 旧证据只被一句 "dep=1.2 已不适用" 带过, 没有逐项核对覆盖范围与代码/依赖/配置/环境, 也没有引用原检查时间与位置. AC-003 当时把仓库外的部署方 relay 启动起来跑通了, 因此没走到"缺依赖服务"分支. | 对应"旧证据未按条件判断即可复用". 实际失败形态是"一律重跑, 不做适用性判断", 不是预期的"无条件复用旧通过结论"; 如实记录, 没有为了贴合预期去改夹具. |
| TS-001 AC-009, 只改说明材料 | `drill-red-009-docsonly/` | 条件完全没变 (只加了 2 行交接说明, 代码/依赖/配置/环境逐项同值) 时, 旧版仍然把 AC-001, AC-002 全部重跑; 旧证据只在末尾被否掉 (relay 缺失那条), 有效旧观察既没被复用也没被引用. | 直接对上 TS-001 的失败预期: 该复用的没复用, 也没有原时间/版本/位置. |
| TS-002 AC-010 | `drill-red-010/` | 第一轮不点名配方时, 旧版发现 `.agents/skills/verify-board/` 后把它降格成"只能当运行线索", 自己按 README 重跑, 全程没有报告配方过时; 第二轮明确要求"按配方重新核对"后, 旧版按配方跑出 `--data-root` 报错, 报告了配方过时与已试路径, 也没改配方. | 对应 TS-002 的失败预期: 没有入口选择规则时, 项目配方不会被当成首选入口, 配方过时也就没人报告. 补做的第二轮说明旧版在"被明确点名"时能正确处理, 因此本 ISSUE 新增的是默认采信与操作缺口分类, 不是从未有过的能力. |

## 验收标准对应证据

| 验收标准 | 证据 |
| --- | --- |
| AC-009-1 条件仍适用的旧证据带原时间/版本/位置复用, 并说明改动不影响适用范围 | `drill-green-009-r1/REPORT.md` 第 2 节: 引用旧观察 `board-dep-1.2-run` 的原检查时间 `2026-10-19T15:19:48Z`, 提交 `1dbbbe1`, 文件位置, 适用条件 (逐个 blob 比对 `app.py`/`deps.txt`/`vendor/relaylib.py`/`README.md` 同值), 并写明"1dbbbe1..HEAD 只新增旧证据文件与 2 行交接说明". 逐项表 BR-001 行同时给出本轮观察与旧观察引用. 另见 `drill-green-009-r3/REPORT.md` 的 AC-003 行: 引用上一轮 `06-ac003-sync.txt` 的原检查时间与版本, 并注明适用条件. |
| AC-009-2 条件变化时只重跑受影响场景, 旧结论不作本次通过依据 | `drill-green-009-r2/REPORT.md` "旧观察的适用性 (未引用为通过依据)" 一节逐条列出每一项的条件变化 (依赖 1.2 到 1.3, relay 服务消失, 实例已停), 全量重跑并把旧结论排除在通过依据外; AC-002 实测 `dep=1.3` 与 `deps.txt` 一致. |
| AC-009-3 条件失效且不可运行时如实受阻, 不通过也不沿用失效证据 | `drill-green-009-r2/REPORT.md` 与 `drill-green-009-r3/REPORT.md` 的 AC-003-1 行: 先核 18290 无监听, 实跑 sync 得 `HTTP Error 503` 与退出码 1, 记"未验证 (缺部署方 relay 服务)", 明确不是产品缺陷, 未起桩或替身; 旧 `sync-ok` 记录只作引用材料. 对应原件 `drill-green-009-r2/06-ac003-sync.txt`, `drill-green-009-r3/07-ac003-relay-precondition.txt`. |
| AC-009-4 输入变化后旧报告只覆盖旧输入, 新场景对新目标重新派发; 目标未重新指定时不悄悄验收 | 负半: `sessions/board-r2/2026-10-19T15-46-47-123Z_01a154d8-0ad3-775e-...jsonl` 里 PRODUCT.md 未提交新增 AC-004 时, 指挥者答"本轮结论不变, AC-004 不追认", 在 `drill-green-009-r2/REPORT.md` 新增"验收后输入变更(不追认)"节, 指出工作区已与 65b43e1 不一致, 要求提交成新目标或撤回. 正半: `drill-green-009-r3/REPORT.md`: 新目标 `5f9544d`, 新证据目录, 新开非作者验收者, AC-004 本轮实跑, 上一轮报告继续只覆盖 `65b43e1` 与旧 PRODUCT.md. |
| AC-010-1 无配方时按 PRODUCT.md 与项目已有可靠入口继续, 不因缺技术/执行文档阻塞, 不自动生成配方 | `drill-green-010-norecipe/90-report.md`: 项目无 TECHNICAL.md / EXECUTION.md / 配方, 验收者按 README 启动实例并跑 3 项, 全部有原始输出; 报告写明"没有自动化测试与项目级验证配方, 本轮按 README 命令操作". 项目 `.agents/skills/` 里只有复制进去的 `verify-change`, 没有新生成的配方 (`git status` 只有证据目录). |
| AC-010-2 配方过时按操作缺口报告, 写明已尝试路径, 不记产品缺陷, 不私自修改 | `drill-green-010-stale/VERIFICATION-REPORT.md` "操作缺口 (不产生判据)" 一节: 配方用 `--data-root` 与 18001, 实跑报 `the following arguments are required: --instance, --data-dir`, 随后 health/status/report 连接被拒; 报告写明这是操作材料缺口, 不是产品行为不满足标准, 验收者改用 README 继续, 未改配方, 未自建 relay 替身. 原件 `drill-green-010-stale/recipe-attempt-18001.txt`; 配方 md5 演练前后同为 `d7bb9590b4358f9695f87a39ac9ba50e` (`fixtures/stalerecipe2/stale-recipe-SKILL.md`). |

## 环境干扰与作废轮次

1. **端口冲突**: 前四个夹具都用产品标准里钉死的 18201, 并发演练时互相占端口. `drill-green-009-r1-extra-version-premise/` 与 `sessions/stalerecipe/` 的两轮受此影响: 前者是按第 2 步正确停下 (目标与 HEAD 不符), 后者第一次因派工单要求空工作区而停在入口, 第二次因 18201 被同轮 board 实例占用而全部记未验证. 这两批不作 AC 证据, 复跑了 stalerecipe2 (18321) 与 board-r1/board-r2.
2. **git 工具钩子**: 操作者执行 `git reset --hard` 时被 git-operation-gate 拦下, 之后改用新建临时项目目录的方式准备目标提交 (board-r1/board-r2 各自 clone 到目标提交), 没有再用 reset.
3. **子会话信任页**: stalerecipe 轮的子验收者首次启动时报项目信任确认, 由操作者选 "Trust (this session only)"; stalerecipe2 轮的验收者没授项目信任, 配方按路径读取而不是按名加载, 报告里如实写了.

## 清理与残留

- 临时项目: `/tmp/orchestra-05/` 保留到证据抄完, 之后整体删除.
- 实例与外部服务: 每轮结束由验收者停实例; 收尾 `ss -ltn` 中 18201, 18290, 18321 均无监听, 无 `app.py serve` 进程, 部署方 relay 文件已在造完旧证据后删除.
- 未运行 `sync-to-pi.py`, 未写 `~/.agents`, `~/.pi` 或任何全局部署副本; 被验项目除证据目录与 gitignore 内的 `runtime/`, `__pycache__/` 外无改动.
