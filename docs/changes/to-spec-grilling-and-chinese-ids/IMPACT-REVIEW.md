# IMPACT-REVIEW (旧行为影响方向)

- 本文件是首轮 (轮次 1). 产物根目录此前无 IMPACT-REVIEW.md, 本轮新建, 不覆盖旧轮次.
- 评审方向: 旧行为影响 (变更是否破坏可能受影响的既有入口, 调用方与旧行为). 不评审规范符合度与 spec 实现完整性, 不新增产品判据, 不作为 `verify-change` 的输入判据.
- 评审起点: `9e8dd1dfe92b3b446c88c2cb8fce33cb0c67a77a` (该点上的 ac-draft.py 含 review_id/--review 契约, to-spec 旧流程, verify-change 旧条文).
- 目标提交: `1e3c9844c6f2aea8df7135214c5225fcc2d3d766` (`git rev-parse HEAD` 实取).
- diff 命令: `git diff 9e8dd1df...HEAD` (三点); commit 列表: `git log 9e8dd1df..HEAD --oneline` (12 条).
- 审核者: 独立会话, 未参与本变更实现与修复.
- 过程原件: `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/integration/review1/` (`IMPACT-NOTES.md`, `probe3.py`, `marker_probe.py`, `recipe.py`, `logs/`).
- 范围说明: 1227 个改动文件中 1212 个是 `docs/changes/to-spec-grilling-and-chinese-ids/evidence/` 的证据归档, 按约定不计产品改动. 产品改动 15 个文件, 见下"实际产品差异".
- 证据级别 (按 blast-radius): 1 = 只断言; 2 = 指到 file:line; 3 = 走查路径证明; 4 = 实跑脚本/测试; 5 = 真实应用里复现. 下文每条标注级别.

## 0. 实际产品差异 (非证据归档)

```
workflow/to-spec/ac-draft.py             | 41 +-   删 review_id/--review, promote 签名改 3 参数, preview JSON 少字段
workflow/to-spec/check-ac.py             |  8 +-   标记文案, with_draft 前置标记检查
workflow/to-spec/SKILL.md                | 120 +--  流程重写 (盘问/反方/机械落正式/独立检查/预览交付)
workflow/to-spec/GHERKIN.md              |  6 +-   编号依据, 标记固定 v1, 预览定位
workflow/to-spec/TEMPLATES.md            |  4 +-   盘问后落笔, 审计证据路径归属
workflow/to-spec/tests/test_ac_draft.py  | 140 +--  迁移到公开 CLI, 删 4 个 mock 内部协作者用例, 删 stale 版本用例
workflow/to-spec/tests/test_ac_reading.py|  60 +--  同上
workflow/verify-change/SKILL.md          |  57 +--  设计方式改为盘问确认 + 反方 + 独立核对, 新增"方案修订"
workflow/verify-change/REVERIFY.md       |   6 +-   复验按方案内容而非编号/状态核对
workflow/navigate/SKILL.md               |  12 +-   spec/verification-plan 的完成标准与衔接条文
workflow/navigate/ACCEPTANCE-GUIDE.md    |  10 +-  验收标准来源, 新增"验证方案确认"节
README.md                                | 条目与阶段说明
```

`workflow/to-spec/check-tech.py` 在三点 diff 中无差异 (见已排除项 E5).

## 1. 关键安全事实

事实 S1: 转正脚本原有的"审阅版本绑定"是唯一的机械防串版手段, 删除后没有任何替代机械检查; 保留下来的是另外四道与"用户确认"无关的保护 (输出符号链接拒绝, 输出等于输入拒绝, 转正期间输入/正式文件变化中止, 转正后正式机检).
- 证据: `git show 9e8dd1df:workflow/to-spec/ac-draft.py` 第 38-41 行 `review_id()`, 第 293-307 行 promote 的版本比对与 `--review` 必填 (第 322 行); HEAD `workflow/to-spec/ac-draft.py` 第 285-303 行 promote 已无版本参数, 第 265-281 行 `_atomic_write` 与第 296-297 行输入变化检查仍在.
- 级别 4: `logs/probe3.log` C 段实跑, 旧版对"预览后改草稿"返回 2 且不写正式文件; 新版同一操作返回 0 并写入.
- 安全作用: 其余四道保护只防止"写入过程本身出错", 不防止"内容不是用户确认过的那一版".

事实 S2: 产物格式与标记向后兼容, 旧产物与新工具, 新产物与旧工具双向可读.
- 证据: HEAD `check-ac.py:41` `CONFIRMATION_MARKER = "<!-- confirmed-flow: v1 -->"` 与旧版同值; 仓库现存 `docs/changes` 下 513 处 `<!-- confirmed-flow: v1 -->` 全部为 v1.
- 级别 4: `logs/probe3.log` E 段, 新版产物过旧 check-ac (E3), 旧版产物过新 check-ac (E6), 均 exit 0.
- 安全作用: 已交付的历史规格不需要迁移, 不会被新机检判废.

## 2. 逐项发现

### R1 [高] promote 去掉审阅版本绑定, 机械防串版消失, 仅剩 chat 记录靠自觉核对

- 位置: `workflow/to-spec/ac-draft.py:285-303` (promote 已无 review 参数与比对); 旧版对照 `9e8dd1df:workflow/to-spec/ac-draft.py:299-300` (审阅版本不匹配即拒绝).
- 影响面: 仓库内脚本调用方只有 to-spec 流程自身 (`workflow/to-spec/SKILL.md:42`), 以及测试; 仓外无已知自动化调用方 (见 R3). 受影响的是"用户确认的是什么内容"这一链: 用户闭环后由 LLM 改写暂存稿或草稿, 新版照旧转正.
- 依据: `docs/changes/to-spec-grilling-and-chinese-ids/DECISIONS.md:77-82` 决策10 明写删除该机制, 理由为用户不看草稿; `TECHNICAL.md:51`; `issues/ISSUE-01-tospec-flow-and-cli.md:25` "不保留 review_id 或 --review 兼容". 属已裁定的设计变更, 不是实现偏差.
- 概率与代价: 触发条件是"闭环后仍改动正文". 新条文要求 `workflow/to-spec/SKILL.md:37` 用盘问范围核实 chat 闭环, 但这是文本要求, 无机检兜底; 一旦静默发生, 正式 PRODUCT.md 与用户确认内容不一致, 下游 verify-change 与验收全链基于未确认内容, 且事后无法只靠文件判断. 代价高, 不可自动恢复.
- 检查方法: 重跑 `logs/probe3.log` C 段. 手动: preview 一次, 改草稿, 直接 promote, 观察返回 0.

### R2 [中] 已安装技能库未同步, 且比评审起点更旧, 交付面与仓库不一致

- 位置: `~/.agents/skills/to-spec/` (ac-draft.py mtime 2025-11-14, check-ac.py mtime 2025-10-27; 仍含 `review_id` 第 38/254/261/299/309/322 行, SKILL.md 仍要求 `--review`).
- 依据: `logs/installed-copy.log`; 实跑旧 check-ac 对当前 `docs/changes/to-spec-grilling-and-chinese-ids/PRODUCT.md` 报 40+ 条 `@G-002 在 ## 目标 节不存在`, exit 1 (`logs/installed-old-check-on-new-product.log`). 原因是被安装副本还停留在中文编号改造之前 (要求 `- G-NNN:` 拉丁条目), 早于本评审起点.
- 影响面: agent 实际加载的是安装库副本, 不是仓库文件. 本变更在宿主执行 `uv run python sync-to-pi.py` 之前对使用者零生效; 同步前仓库文档 (README.md:65-67, to-spec/verify-change 条文) 已描述新行为, 形成"文档说新, 手上跑旧"的窗口.
- 概率与代价: 交付即发生 (必然窗口), 直到宿主同步. 代价为按旧契约产出规格 (要求用户采纳 review_id) 或旧机检直接判废当前产物, 返工一轮.
- 检查方法: 比对 `~/.agents/skills/to-spec/{ac-draft.py,SKILL.md,check-ac.py}` 与 `workflow/to-spec/` 同名文件; 或直接对任一现行 PRODUCT.md 跑安装库 check-ac.
- 备注: 中文编号分歧是 milestone-01 遗留, 不由本 diff 引入; 但说明"仓库改完"不等于"已生效", 需在交付前同步.

### R3 [中] 15 个历史变更文档/脚本仍按旧契约, 重跑即失败 (历史例外, 分类如下)

- 清单 (命令见 `logs/grep-contract-residue.log`; `grep -rln` 计数 15 文件):
  - 可执行脚本 8 个, 都从 `ac-draft.py preview` 的 stdout 取 `review_id` 再 `promote --review`:
    `docs/changes/verification-skills/evidence/ISSUE-01/setup-drills.sh:20-21`, `ISSUE-02/setup-drills.sh:23-24`, `ISSUE-03/setup-drills.sh:26`, `ISSUE-03/setup-heavy-drills.sh:17`, `ISSUE-03/setup-micro-drill.sh:17`, `ISSUE-04/setup-drills.sh:34`, `ISSUE-05/setup-drills.sh:380`, `ISSUE-10/setup-drills.sh:619`.
  - 说明文档 7 处: `docs/changes/verification-skills/evidence/ISSUE-01/README.md:18`, `ISSUE-02/README.md:17`, `docs/changes/verification-skills/DECISIONS.md:395`, `docs/changes/workflow-stack-review/milestone-22/CHECKS.md:16`, `milestone-25/CHECKS.md:19`, `milestone-25/EXECUTION.md:17`, `workflow-stack-review/roadmap/ROADMAP.json` (2 处 close_summary).
- 依据与判定: 这些是本变更之外的历史产物, 属"历史快照例外", 不要求迁移, 也不要求通过新机检 (与 `VERIFICATION-PLAN.md:135` 规则12 的口径一致). 但它们的重跑路径确实断了: 新 `preview` 的 JSON 键为 `command/draft/preview/success` (无 `review_id`, 实跑 `logs/probe3.log` A 段), 取键即 KeyError; `promote --review` 退出 2 (`unrecognized arguments`, 同日志 D 段).
- 概率与代价: 只在"复验旧变更时重跑历史 drill 脚本"时触发; 后果是脚本早期失败而非静默通过, 可诊断. 概率低, 代价低.
- 检查方法: `grep -rn "review_id\|--review" docs/changes | grep -v to-spec-grilling-and-chinese-ids`; 未实跑这些脚本 (会写入历史目录, 越权), 记为缺口 G4.

### R4 [中] 三条转正过程保护不再有仓库自动化测试覆盖, 只留一次性证据

- 位置: `workflow/to-spec/ac-draft.py:278` (正式文件在转正过程中已变化), `:297` (输入在转正过程中已变化), `:294` `checker.validate_product(candidate)` (正式复检失败).
- 依据: 被删除的 4 个用例 (旧 `tests/test_ac_draft.py`, `9e8dd1df` 版) 中的 `test_change_during_validation_aborts_publication`, `test_changed_output_is_not_overwritten_during_atomic_write`, `test_formal_recheck_failure_preserves_old_output` 恰好覆盖这三条路径; 新版测试文件里这三个断言串全部 0 命中 (`logs/probe3.log` H 段 FAIL 即此). 现存覆盖只有一次性证据 `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-01/run5/logs/trace-{base,draft,output}.*` (ptrace 指定窗口暂停, 外部 cp 改动后才恢复, exit 2 且旧稿保留) 与 `trace-atomic-formal-check.*`.
- 概率与代价: 现在不坏 (代码路径未删, 且有 2026-11-27 的实跑证据). 风险在未来: 该路径无回归网, 重构 `promote`/`_atomic_write` 时无声破坏, 而它正是替代 review_id 后剩下的主要保护.
- 检查方法: `grep -n "输入在转正过程中\|正式文件在转正过程中\|validate_product" workflow/to-spec/tests/*.py` (0 命中); 修复建议方向是把 trace 场景落成仓库内真实进程用例 (不改产品代码即可测).
- 级别 4.

### R5 [中] 下游门禁仍按"已确认的 VERIFICATION-PLAN"措辞, 确认语义已换

- 位置 (均未被本 diff 修改): `workflow/to-execution/SKILL.md:16` "须先有产物根目录下状态为已确认的 `VERIFICATION-PLAN.md`", `:35` "已确认的 `VERIFICATION-PLAN.md`"; `workflow/drive-execution/SKILL.md:26` "已有状态为已确认的 `VERIFICATION-PLAN.md`"; `workflow/navigate/reference/VERIFICATION.md:5` "已确认的 `VERIFICATION-PLAN.md` 路径与修订号".
- 变化点: 旧 `verify-change` 第 4 步要求用户明确确认修订号后才置"已确认"; 新 `workflow/verify-change/SKILL.md:36-41` 改为"盘问闭环 + 独立核对无阻塞"即以已确认状态交付, 并明说 `:47` "版本号, 确认状态或通知不证明内容已获确认".
- 判定: 字段仍在, 门禁不会失效, 属兼容; 但四处下游条文仍把"已确认"当"用户逐条看过"的同义词, 读者可能据此跳过 `verify-change` 执行方式第 1 步要求的内容级核实. 属措辞未同步, 不是功能破坏.
- 检查方法: 读上述四行 + `workflow/verify-change/SKILL.md:36-47`; `git diff 9e8dd1df...HEAD -- workflow/to-execution workflow/drive-execution` 为空 (`logs/capability-diff.log`).
- 级别 2.

### R6 [低] check-ac 报错文案与 with_draft 检查顺序变化 (退出码不变)

- 位置: `workflow/to-spec/check-ac.py:12` 与 `:171` 文案 "验收标准确认流程写入" -> "转正流程写入"; `:325-330` 把"草稿不得带标记"提到围栏检查之前.
- 实跑: 缺标记时退出码同为 2, stderr 文案不同 (`logs/probe3.log` F 段); 草稿同时"带标记"且"围栏外有多余内容"时, 旧版报 "草稿只能包含一个完整的 gherkin 代码块", 新版报 "草稿不携带确认标记", 退出码同为 2 (G 段).
- 影响面: `with_draft` 只被 ac-draft.py 调用 (`ac-draft.py:33` 按文件名加载 check-ac.py), CLI `check-ac.py --draft` 走 `validate_draft` 不经过该顺序; 仓库内无解析报错文本的消费者 (grep 0). 概率低, 代价低 (仅报错措辞不同).
- 级别 4.

### R7 [低] 文档写"固定 v1", 代码仍接受任意 vN

- 位置: 文档 `workflow/to-spec/GHERKIN.md` 第 7 条 "必须含固定标记 `<!-- confirmed-flow: v1 -->`", `workflow/to-spec/SKILL.md:48` "加固定 `<!-- confirmed-flow: v1 -->`", `check-ac.py:12`; 实现 `check-ac.py:43` `MARKER_RE = r"<!--\s*confirmed-flow:\s*v\d+\s*-->"`.
- 实跑: 把转正产物标记改为 v2 / v9, `check-ac.py` 均 exit 0 "通过" (`logs/marker-probe.log`).
- 判定: 不破坏兼容 (513 个 v1 历史文件照常通过), 但"固定 v1"目前只是约定, 机检没拦住 vN. 若后续有人手工改成 v2, 不会被拒. 概率低, 代价低.
- 级别 4.

### R8 [低] 预览文件名格式变化 (去掉 12 位哈希段)

- 位置: `workflow/to-spec/ac-draft.py:248`: 旧 `{日期}-acceptance-{review[:12]}-{uuid4().hex[:8]}.html`, 新 `{日期}-acceptance-{uuid4().hex}.html`.
- 影响面: 仓库内没有按该模式匹配文件的脚本 (grep `acceptance-` 仅命中 ac-draft.py 自身与本变更文档的记录). 历史文档里记录的旧文件名指向 /tmp 工作区, 早已不同名也不影响读取. 概率低, 代价无.
- 级别 4 (grep 全仓 + diff 对照).

### R9 [低] 新命令清单引入 POSIX 专有 `cp --` / `cmp --`, 仓库自称跨平台

- 位置: `workflow/to-spec/SKILL.md:43-44`; 旧版对应位置 (`9e8dd1df:workflow/to-spec/SKILL.md` 第 4 步) 只用散文描述"复制技术稿", 无 `cp`/`cmp`; 旧命令块只有两条 `uv run`.
- 依据: `sync-to-pi.py` 文档头写明 "跨平台: Windows / Linux / macOS, 纯 Python 标准库", 仓库整体按跨平台维护. 本机 (Linux) 实跑通过 (`logs/recipe.log` RECIPE OK), Windows 上 `cp`/`cmp --` 不可用, 技术稿机械复制这一步会中断, 而该步正是"两份正式稿整组交付"的前置.
- 概率与代价: 只在 Windows 宿主上执行该流程时触发, 概率中低; 代价是流程卡在复制步, 需改用 `python -c shutil.copyfile` 或 `Copy-Item`.
- 级别 3 (跨平台属实但未在 Windows 实跑, 记缺口 G2).

### R10 [低] to-spec 新流程对被组合技能提出的细节要求, 未写进那些技能的契约

- 位置与依据: `workflow/to-spec/SKILL.md:21` 要求交接写"已否决分支及理由, 逐题和逐节覆盖进度, 盲区扫描进度"; `general/handoff/SKILL.md` 只规定 必读推荐/路线图/落盘位置, 没有这几类字段 (`grep "盲区\|进行时\|逐题" general/handoff/` 0 命中). `SKILL.md:23` 用"`grilling` 盲区扫描", `general/grilling/SKILL.md:26` 确有该概念 (对齐). `SKILL.md:23` 的"事实条目标明 `随决策N确认`"在 `workflow/decision-ledger/SKILL.md:33-39` 的事实模板里没有对应字段, 只能塞进"来源"或"内容" (靠约定, 无机检). 本 diff 未改这些技能 (`logs/capability-diff.log` 为空).
- 判定: 不构成破坏 (被调用技能不禁止额外信息), 但跨技能路径的正确性只靠 to-spec 单方面措辞, 被调用技能的机检/检查清单不会兜底. 概率中 (执行者按被调用技能的最小要求交付时会漏项), 代价低 (交接或账本信息不全, 续问时重问).
- 级别 2.

## 3. 已排除项 (查过并确认没事)

| 编号 | 查了什么 | 排除依据 | 级别 |
| --- | --- | --- | --- |
| E1 | 仓库内是否有脚本/产品代码调用 `ac-draft.py promote --review` 或读 `review_id` | `grep -rn "review_id\|--review" workflow general tests README.md pi agent-prompts` 只命中 2 处测试断言 (`test_ac_draft.py:217` 断言不存在, `:267-270` 断言参数被拒). 无其他调用方. `logs/grep-contract-residue.log` | 4 |
| E2 | 旧产物能否通过新机检 | `docs/changes` 下 513 处 `confirmed-flow: v1` 与 `check-ac.py:41` 同值; 实跑旧版产物过新 check-ac exit 0 (`logs/probe3.log` E6) | 4 |
| E3 | 新产物能否被旧工具读 | 新版产物过旧 check-ac exit 0 (E3 段) | 4 |
| E4 | 跨文件 markdown 锚点是否悬空 | `deliberate/SKILL.md:9` 与 `drive-execution/reference/orchestration.md:20` 指向 `to-spec/SKILL.md#规格约束与停止条件`, 新文件第 11 行仍是该标题; `TEMPLATES.md:3/48` 与 `GHERKIN.md:3/95` 指向 `#达标标准与检查边界` / `#规格约束与停止条件`, 第 65 行与第 11 行都在; `navigate/ACCEPTANCE-GUIDE.md:14` 新增的 `SKILL.md#milestone` 对应 `navigate/SKILL.md:31` `## Milestone` | 3 |
| E5 | check-tech.py 是否有契约变化 | `git diff 9e8dd1df...HEAD -- workflow/to-spec/check-tech.py` 空输出; 任务点所述 check-tech 退出码/输出变化为无变化 | 4 |
| E6 | 被删章节是否仍被引用 | 全仓 `grep "验收标准确认"` 在 workflow/general/README 0 命中 (旧章节名已无人引用) | 4 |
| E7 | 新版 SKILL 第 3 节命令清单能否照做 | 逐条实跑: check-ac 草稿 0, check-tech 0, promote 0 且 success, cp/cmp 0, 正式 check-ac/check-tech 0 (`logs/recipe.log` RECIPE OK) | 4 |
| E8 | 既有检查是否仍绿 | to-spec 测试 39 passed + 39 subtests exit 0; `check_skill.py` 对 to-spec/verify-change/navigate 三个 SKILL.md 均 OK; 产品路径 `git diff --check` exit 0 | 4 |
| E9 | 预览页是否还含确认入口 | 页面无"审阅版本", 含"页面仅供选看, 不用于确认.", JSON 无 `review_id` (`logs/probe3.log` A2/A4) | 4 |
| E10 | 被组合技能是否被本 diff 改动 | `git diff --stat` 对 general/{grilling,handoff,opposing-viewpoint,present} 与 workflow/{deliberate,decision-ledger,domain-modeling,domain-awareness,codebase-design,verification-contract,to-execution,drive-execution} 为空 | 4 |
| E11 | 新旧工具混用的日常路径 | 安装库与仓库各自成套 (`ac-draft.py:33` 按同目录文件名加载 check-ac.py), 不存在只换一个文件的官方路径; 混用只发生在人工单文件拷贝, 未做实跑 | 3 |
| E12 | 仓内是否有旧流程写的 VERIFICATION-PLAN 需迁移 | `grep -rln "方案版本" docs/changes --include=VERIFICATION-PLAN.md` 只有本变更一份 (新流程产物); 旧流程计划数 0 | 4 |

## 4. 缺口 (未证实或未覆盖)

- G1 宿主同步链未验证: `sync-to-pi.py` 在容器内只读 (`~/.agents` 属 root), 未跑"同步 -> agent 重新加载 -> 用新条文产出一份规格"的链路. R2 只能证明"当前未生效", 不能证明"同步后一定生效". 需宿主侧执行并按 R2 检查方法复核.
- G2 未在 Windows 实跑. R9 的跨平台结论是条文 + 仓库自述推断, 无 Windows 观察.
- G3 新 to-spec / verify-change 流程本身没有端到端试跑 (盘问 -> 账本 -> 反方 -> 落笔 -> 独立检查 -> 转正). 本轮只验条文与 CLI, 因此"确认语义从逐版采纳改为闭环确认"带来的行为影响只能按文本判断, 未在真实长会话里观察. 该流程本身的试跑属成品验证, 不在本方向.
- G4 历史 drill 脚本未实跑 (会写入历史证据目录, 超出只读授权); R3 的"重跑即失败"由字段实跑 + 静态用法推定, 未逐脚本执行.
- G5 仓外消费者无法枚举: 其他项目若复制过旧版 to-spec 脚本, 或宿主有自建脚本调 `--review`, 本轮无入口发现. E1 的"无调用方"只覆盖本仓库.
- G6 R1 的替代保障 (chat 闭环核实) 无机械锚点, 也无法由外部验证; 这是决策10 的知情接受风险 (见 `DECISIONS.md:77-82` 与 `OPPOSING-milestone-03.md:73` OPP-07), 本轮不重复裁决, 只记录其影响面.
- G7 根 `pytest.ini` 的 `testpaths` 不含 `workflow/to-spec/tests`, 默认 `uv run pytest` 不会跑被改契约的测试 (既有缺口, 非本次引入). 本轮结论依赖显式指定路径的实跑.

## 5. 既有检查与本轮运行结果

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| to-spec 测试 | `uv run --with gherkin-official pytest -p no:cacheprovider -q workflow/to-spec/tests` | 39 passed + 39 subtests, exit 0 |
| 技能文档检查 | `uv run python general/writing-for-llm/check_skill.py <3 个改动 SKILL.md>` | 均 OK, exit 0 |
| 产品路径空白 | `git diff --check 9e8dd1df...HEAD -- workflow general README.md pi agent-prompts` | 空, exit 0 (证据目录内有既有空白告警, 不计产品) |
| 契约差异探测 | `probe3.py` (本轮) | A/B/C/D/E/F/G 全 PASS; H 段 3 项 FAIL 即 R4 |
| 标记版本探测 | `marker_probe.py` (本轮) | v1/v2/v9 均 exit 0 |
| 命令清单实跑 | `recipe.py` (本轮) | RECIPE OK |
| 旧安装版对现行产物 | 安装库 check-ac 对 `docs/changes/.../PRODUCT.md` | exit 1, 40+ 条编号对账错误 |
| 仓库默认测试收集 | `pytest.ini` testpaths | 不含 to-spec 测试 (G7) |

## 6. 本轮记录

- 做了什么: 读产品差异 15 文件与旧版对照; 全仓搜索旧契约调用方与文档引用 (workflow/general/tests/pi/agent-prompts/README/docs/changes); 从基准点抽出旧版工具对做新旧实跑对比 (契约差异, 兼容性, 文案, 顺序, 覆盖); 按新版条文实跑命令清单; 跑既有测试与文档检查; 对比已安装技能库; 读证据根 (issue-01/INDEX.md, run5 trace-*, integration/run1/audit-renumbering.md) 核对并发与编号审计材料.
- 关键事实与级别: S1 级别 4, S2 级别 4 (见第 1 节).
- 最便宜的复现: `uv run --with gherkin-official python /home/bolo/evidence/to-spec-grilling-and-chinese-ids/integration/review1/probe3.py` (需先把 `probe3.py` 内 OLD 指向旧版快照目录, 见 IMPACT-NOTES 第 4 节). 其中 C1/C2 一对输出直接显示防串版保护的去留.
- 合并前建议: R2 (同步再宣称生效) 与 R4 (补回过程保护的仓库内用例) 值得在交付前处理; R5/R9/R10 属措辞与跨平台事项, 可按优先级另行安排; R1/G6 已由决策10 接受, 本条只记录影响面.
- 未覆盖范围: 宿主同步链, Windows 环境, 新流程端到端试跑, 历史 drill 脚本实跑, 仓外调用方 (G1-G5).
- 不声称本报告找到全部影响: 以上基于三点 diff, 全仓文本检索与可运行入口的实跑; 语义层面的跨技能执行偏差 (G3) 未观察.
- 提交状态: 按派工口径 "不提交 (你的报告文件除外, 也不自行提交)", 本文件只写入工作区, 未 commit, 未 push; 是否提交由调用方/集成会话决定.
- 清理: /tmp 下运行产物已删, 探针脚本与日志已归档到证据目录; 未改产品文件.

---

# IMPACT-REVIEW 第二轮 (返工轮复核, 目标提交 a13085a)

- 轮次: 第二轮 (重跑), 追加于首轮之后, 不覆盖上轮内容.
- 评审起点不变: `9e8dd1df`; 目标提交: `a13085ab9e10eacbc726b90e0d8ccfb731447c0d` (`git rev-parse HEAD` 实取, 工作区干净).
- 返工轮新差异: `783a528..a13085a` 中产品文件 4 个 (`workflow/to-spec/SKILL.md` 五步各补一行完成标准, `workflow/to-spec/check-ac.py` docstring 与一条报错文案 vN->v1, `workflow/to-spec/tests/test_ac_draft.py` 新增 11 例坏输入回归, `workflow/verify-change/SKILL.md` 三处 设计方式->设计验证方案), 其余为工单/执行记录文档, 不计产品.
- 授权: 除追加本文件外只读. 过程命令与输出见各条引用, 本轮未新建证据目录外文件.
- 方法: 按 blast-radius skill 第 2-6 节核对返工轮差异的调用方与旧行为; 返工轮无共享接口/数据格式/跨模块路径的行为变更 (见 S3), 不触发其第 7 节多模型同题调查; 上轮 R4 涉及 promote 保护路径属共享行为面, 本轮深查其自动化覆盖.

## 7. 返工轮关键安全事实

事实 S3: 返工轮对公开 CLI 行为零改动. `check-ac.py` 只动 docstring (第 11-15 行) 与一条报错文案字面量 (第 177 行, `vN` 占位改为 `CONFIRMATION_MARKER` 即 v1 字面量), `MARKER_RE` (第 45 行) 仍按 `v数字` 匹配, 检查顺序与退出码不变; `ac-draft.py` 与 `check-tech.py` 在 `783a528..a13085a` 无差异, `git diff 9e8dd1df...HEAD -- check-tech.py` 仍为 0 行. 两个 SKILL.md 的改动是纯条文 (新增完成标准行 / 三行术语逐字替换).
- 依据: `git diff 783a528..a13085a -- workflow/to-spec/check-ac.py workflow/to-spec/ac-draft.py workflow/to-spec/check-tech.py` 逐行读过; issue-04 证据 `marker-*` 四种输入基线/目标退出码逐例一致; 本轮复跑测试与文档检查全绿 (第 10 节).
- 级别 4. 安全作用: 返工轮不可能引入新的旧行为破坏, 剩余风险只在条文措辞与测试本身.

## 8. 上轮闭环核对 (R1-R10, E1-E12, G1-G7)

| 项 | EXECUTION.md 载明处置 | 本轮核实 | 结论 |
| --- | --- | --- | --- |
| R1 | 不返工, 决策10 知情接受, 仅记录 | 返工轮未触碰 `ac-draft.py`; promote 仍无版本参数 (`ac-draft.py:285-301`), 机械防串版仍缺失 | 记录闭环成立, 风险保持 (知情接受) |
| R2 | 不返工, 部署事项交用户 | 实测 `~/.agents/skills/to-spec/{ac-draft.py,check-ac.py,SKILL.md}` 与仓库同名文件逐一 `cmp` DIFF (mtime 2025-11-14/10-27), "文档说新手上跑旧" 窗口仍在 | 记录闭环成立, 事项仍开放 |
| R3 | 未列 (历史例外) | 返工轮未触碰历史证据目录; 产品路径 `review_id`/`--review` 复查仍只有测试负断言 3 处 (`test_ac_draft.py:217,267-270`), E1 维持 | 保持历史例外, 不变 |
| R4 | 自动化部分已修 (ISSUE-04), 并发窗口保持一次性真实进程证据 | 新增 `test_promote_rejects_bad_format_and_bad_numbering_inputs_keeping_output` 11 例, 全部经真实 `promote` 进程与隔离临时目录; 其中 "重复目标" 等用例覆盖草稿机检后的候选校验失败路径 (`ac-draft.py:293-294` -> `check-ac.py:129`), 断言正式稿字节不变且输出目录无临时残留; 实跑 40 passed + 50 subtests exit 0. 两个并发窗口保护 (`ac-draft.py:278` 正式文件变化, `:297` 输入变化) 仍无自动化, tests 内三条保护文案 grep 0 命中 | 部分闭环成立: 自动化部分修对, 余项 (并发窗口) 按载明处置保留一次性证据, 非静默回退 |
| R5 | 未列 | 返工 diff 不含 to-execution/drive-execution/navigate reference; 下游 "已确认的 VERIFICATION-PLAN" 措辞与确认语义的错位仍在 | 仍开放, 未返工 (归属见 N2) |
| R6 | 未列 (文案统一顺带) | 报错文案进一步改为 v1 字面量, 退出码不变, 全仓无报错文本解析方 (E13) | 原风险面 (仅措辞) 不变, 无新破坏 |
| R7 | 未列 (docstring 顺带) | `MARKER_RE` 行为未变, issue-04 marker 证据 v1/v2 等四例基线/目标同码; docstring 现明写 "机检按 `v数字` 匹配以兼容旧文件, 现行只写 v1" | 文档-实现不一致被显式记录为兼容承诺; 机检不拦 v2 的约定性质保持, 不变 |
| R8 | 未列 | 预览文件名逻辑不在返工 diff | 保持 |
| R9 | 未列 | `cp --`/`cmp --` 仍在 (`SKILL.md:47-48`) | 保持, Windows 缺口开放 |
| R10 | 未列 | handoff/grilling/decision-ledger 均不在返工 diff | 保持 |
| E1-E12 | - | 抽查维持: E1 (grep 复跑同上), E5 (check-tech 三点 diff 0 行), E8 (复跑全绿, 第 10 节), E2/E3 (`MARKER_RE` 未变, 双向兼容维持); 其余各项涉及的文件返工轮均未触碰, 按上轮结论沿用 | 维持 |
| G1-G7 | - | 全部开放. G1 加强证据: 安装库实测仍旧 (R2 行); G7 复核: 根 `pytest.ini` testpaths 仍不含 `workflow/to-spec/tests` (实测); G2-G6 无新观察 | 维持 |

## 9. 返工轮逐项发现

### N1 [低] 术语残留: verify-change 改用 "设计验证方案" 后, 同一调用语义的引用处仍写 "设计方式"

- 位置: `workflow/navigate/SKILL.md:71` 与根 `README.md:65` (两行均为本里程碑 diff 引入或改写, `git diff 9e8dd1df...HEAD` 逐行确认), 另 `workflow/verification-contract/SKILL.md:15` (基线已有, 非本 diff 引入). 同文件 `navigate/SKILL.md:42` 已用新词 "设计验证方案方式", 文件内不一致.
- 依据: ISSUE-05 工单 "未覆盖" 节已如实列出这三处且说明范围外未擅扩; 但 `EXECUTION.md` 的未处理清单未点名, 归属未记.
- 概率与代价: 纯条文, 无机检路径; 读者/执行者按旧词 "设计方式" 检索或理解时对不上 verify-change 现行方式名, 代价为误读或后续修文时漏改, 不破坏机检与 CLI.
- 检查方法: `grep -rn "设计方式" workflow general README.md` (命中上述 3 行); `grep -rn "设计验证方案" ...` 对照.
- 级别 4 (grep 全仓 + diff 逐行).

### N2 [低] 记录缺口: EXECUTION.md 未逐条点名 R5/R9/R10 的处置归属

- 位置: `docs/changes/to-spec-grilling-and-chinese-ids/EXECUTION.md` "未处理发现与归属" 只列 F1/R1/R2/R4-并发部分.
- 影响: 上轮 R5/R9/R10 (措辞与跨平台类, 上轮建议 "另行安排") 的实际归属需读者跨文件推断; 不是行为破坏, 是闭环记录不完整, 与 N1 同源 (返工记录按工单粒度, 未按评审发现粒度收口).
- 级别 2.

## 10. 返工轮已排除项 (新查)

| 编号 | 查了什么 | 排除依据 | 级别 |
| --- | --- | --- | --- |
| E13 | check-ac 报错文案变化是否有既有解析方 | grep 全仓 py/sh/tests `"确认流程标记\|必须位于 gherkin 代码块之前\|confirmed-flow: vN"` 仅命中 check-ac.py 自身与测试的子串断言 (`test_ac_draft.py:135` 断言的 "确认流程标记" 在新文案中仍含, 测试通过); issue-04 证据 `marker-*`: 缺标记/位置错/v1/v2 四种输入基线与目标退出码逐例一致 | 4 |
| E14 | 新增 11 例测试是否触碰真实用户环境 | `test_ac_draft.py` setUp 用 `tempfile.TemporaryDirectory` (第 89 行), 文件头明写不操作真实 agent 目录或常驻服务; 新例全部经该隔离装置实跑通过, 不触 `~/.agents` 与真实产物 | 4 |
| E15 | 五步完成标准行是否破坏既有引用/锚点 | 纯新增 5 行 (`SKILL.md:25,37,55,71,96`), 现有标题未改 (E4 锚点维持), 无命令变化; `check_skill.py workflow/to-spec/SKILL.md` OK exit 0 | 4 |
| E16 | verify-change 三处术语替换是否改语义/断锚点 | diff 仅 3 行且逐字为 设计方式->设计验证方案 (ISSUE-05 证据 `term-normalized-diff`, 本轮复核); `[方案修订](#方案修订)` 锚点标题 (`SKILL.md:43`) 未动; `check_skill.py` OK exit 0 | 4 |

## 11. 既有检查与本轮运行结果 (实测复跑)

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| to-spec 测试 | `uv run --with gherkin-official pytest -p no:cacheprovider -q workflow/to-spec/tests` | 40 passed + 50 subtests, exit 0 (上轮 39+39 基线 + 新 11 例) |
| 技能文档检查 | `uv run python general/writing-for-llm/check_skill.py <to-spec/verify-change/navigate 三个 SKILL.md>` | 均 OK, exit 0 |
| 产品路径空白 | `git diff --check 9e8dd1df...HEAD -- workflow general README.md` | 空, exit 0 |
| 安装库一致性 | `cmp ~/.agents/skills/to-spec/<3 文件> workflow/to-spec/<同>` | 三文件均 DIFF (R2 窗口仍在) |

## 12. 本轮记录与边界

- 做了什么: 读返工轮完整 diff (产品 4 文件 + 工单/执行记录); 核对 EXECUTION.md 与 ISSUE-04/05/06 处置记载; 逐项回验上轮 R1-R10/E1-E12/G1-G7 的代码现状 (grep/diff/cmp/实跑); 深查报错文案消费者, 测试隔离性, 术语引用面与锚点; 复跑全部既有检查.
- 未覆盖范围: 上轮 G1-G7 全部保持 (宿主同步链, Windows, 新流程端到端试跑, 历史 drill 实跑, 仓外调用方, R1 机械锚点, 全量 pytest 的 podman 隔离环境); 全量 `uv run pytest` 返工轮同样未验证 (G8, EXECUTION.md 载明容器无 podman 交调用方).
- 不声称找到全部影响: 本轮结论基于 `783a528..a13085a` 与三点 diff 的逐行比对, 全仓文本检索和可运行入口实跑; 语义层面的跨技能执行偏差仍未观察.
- 合并前建议: N1 的三处旧词宜与 R5 一并按措辞事项安排; R2 同步与 R4 并发窗口自动化保持上轮建议不变.
- 提交状态: 按本轮授权, 本文件只追加到工作区, 未 commit, 未 push.
- 清理: 本轮全部命令只读或跑在仓库自带测试栈的临时目录内, 无 /tmp 残留需清理, 未改产品文件.

---

# IMPACT-REVIEW 第三轮 (收尾重跑, 目标提交 de3b589)

- 轮次: 第三轮 (收尾重跑), 追加于前两轮之后, 不覆盖旧轮次.
- 评审起点不变: `9e8dd1df`; 目标提交: `de3b589ce0df1d5a94b609e5ba99507f445103d5` (`git rev-parse HEAD` 实取).
- 本轮新差异 (相对上轮目标 a13085a): merge 5bc32d2 (issue/07, 即 8e776be) + 记录 de3b589. `git diff a13085a..de3b589 --stat` 共 6 文件, 其中产品改动仅 3 行 3 文件: `workflow/verify-change/SKILL.md:47` 段内补一句 `不新增盘问专用记录格式.`, `workflow/navigate/SKILL.md:71` 与根 `README.md:65` 术语 设计方式 -> 设计验证方案; 其余为 EXECUTION.md 记录 5 行, 本文件第二轮追加与工单 `issues/ISSUE-07-round3-n1-q1.md`, 不计产品. 证据: integration/run3/ 与 issue-07/run1/.
- 授权: 除追加本文件并提交外只读. 未新建仓库外证据文件, 过程命令与结果见各条引用.
- 方法: 本轮差异为纯条文, 无共享接口/数据格式/跨模块路径变更, 不触发 blast-radius 多模型深查; 重点为字面引用面, 补句与既有禁令的一致性, 上轮 N1/N2 闭环, 以及开放项在最终提交上的现状复测.

## 13. 第三轮关键安全事实

事实 S4: 三行新差异是纯条文, 无机检或 CLI 路径可触达. 全仓排除 docs/changes 后 `设计方式` 字面仅剩 `workflow/verification-contract/SKILL.md:15` (基线已有, 非本 diff 引入, ISSUE-07 工单明载范围外只记录); 无任何 py/sh 脚本或测试对 `设计方式`, `盘问专用` 或 verify-change 方式名做字面匹配 (`grep --include="*.py" --include="*.sh" 盘问专用` 0 命中; 方法名仅出现在 markdown 引导条文里). 两个改动 SKILL.md 的 `check_skill.py` 均 OK.
- 级别 4. 安全作用: 补句与术语替换不可能破坏任何脚本化消费方.

事实 S5: `verify-change/SKILL.md:47` 补句 `不新增盘问专用记录格式.` 与 `:28` 既有禁令 `不新增盘问专用文件, 章节或格式` 语义同向, 无冲突, 无重复执行歧义. 两处都是禁止性条文 (不做某事), 不存在被触发两次的动作; `:47` 是修订段对同一禁令的复述, 与 `workflow/to-spec/SKILL.md:22` 的同型表述 (`判定的持久记录只用现有决策/事实格式, 不增盘问专用文件/章节/格式`) 结构一致. 补句位置在 `用现有来源引用和检查产物保留变更及确认依据` 之后, 语义为沿用现有格式, 与该句正衔接.
- 级别 3 (逐行走读比对, 无可实跑路径).

## 14. 上轮 N1/N2 闭环核对

| 项 | 本轮核实 | 结论 |
| --- | --- | --- |
| N1 (设计方式残留) | `workflow/navigate/SKILL.md:71` 与 `README.md:65` 已逐字替换为 设计验证方案 (本轮 diff 逐行读过); 残留仅 `verification-contract/SKILL.md:15` 一处, ISSUE-07 工单明载 `不动其他 设计方式 残留 (在范围外, 只记录不改)`, EXECUTION.md:28 也载明 ISSUE-07 完成 N1 | 闭环成立: 范围内两处已修, 范围外一处已显式记录归属 |
| N2 (EXECUTION 未点名 R5/R9/R10 归属) | `EXECUTION.md:32` 新增: `R5/R9/R10 维持开放, 归属: 跨文件措辞一致性与可移植性类事项, 交 milestone-12 用户审改时定夺 (R5 与 F1 同涉 workflow/navigate/reference/VERIFICATION.md); F1 仍待用户授权范围` | 闭环成立: 归属行已在, 三项均有明确去处 |

## 15. 开放项在最终提交 de3b589 上的现状复测

| 项 | 复测命令/依据 | 结果 |
| --- | --- | --- |
| R1 | `sed -n 285,303p workflow/to-spec/ac-draft.py` 后 grep `review\|版本` 0 命中; promote 仍无版本参数与比对 | 仍开放 (决策10 知情接受, 仅记录) |
| R2 | `cmp ~/.agents/skills/to-spec/{ac-draft.py,check-ac.py,SKILL.md} workflow/to-spec/<同>` 三文件均 DIFF | 仍开放 (部署事项, 交用户) |
| R5 | `grep -n "已确认的 \`VERIFICATION-PLAN" workflow/to-execution/SKILL.md workflow/drive-execution/SKILL.md workflow/navigate/reference/VERIFICATION.md` 仍命中 4 处 (:16/:35/:26/:5) | 仍开放, 归属已记 (N2) |
| R9 | `grep -n "cp --\|cmp --" workflow/to-spec/SKILL.md` 仍命中 `:47-48` | 仍开放, 归属已记 (N2) |
| R10 | `grep -rn "盲区\|逐题" general/handoff/SKILL.md workflow/decision-ledger/SKILL.md` 0 命中 | 仍开放, 归属已记 (N2) |
| F1 | `workflow/navigate/reference/VERIFICATION.md:9` 分流条文未变 (本轮 diff 未触碰该文件); EXECUTION.md:26 已载明与 AC-041 方向相反, 待用户授权范围 | 仍开放, 归属已记 |
| G1-G7 | G1 经 R2 cmp 加强证据 (安装库仍旧); G7 复测根 `pytest.ini` testpaths 仍不含 `workflow/to-spec/tests`; G2-G6 无新观察 | 全部维持开放 |

## 16. 第三轮已排除项 (新查)

| 编号 | 查了什么 | 排除依据 | 级别 |
| --- | --- | --- | --- |
| E17 | 三行新差异是否有字面匹配/解析消费方 | 全仓 (排除 docs/changes) grep `设计方式` 仅 verification-contract:15; py/sh 中 `盘问专用` 0 命中; 无脚本解析方式名或禁令句 | 4 |
| E18 | 补句是否与 :28 既有禁令冲突或造成重复执行歧义 | 两处均为禁止性条文, 语义同向无动作可重复触发; 与 to-spec/SKILL.md:22 同型表述结构一致 (S5) | 3 |
| E19 | 术语替换是否改语义/断锚点 | diff 逐字为 设计方式 -> 设计验证方案, 与 `verify-change/SKILL.md:11/:18` 的方式名一致; navigate `SKILL.md#milestone` 锚点与本文件标题未动; check_skill.py OK | 4 |
| E20 | merge 5bc32d2 与记录 de3b589 是否夹带范围外产品改动 | `git diff a13085a..de3b589 --stat` 仅 6 文件, 产品 3 行; `git diff 8e776be..de3b589` 仅 EXECUTION.md 5 行记录 | 4 |
| E21 | verify-change/navigate README 三处改动是否影响既有引用 | 三处均为段内单行, 周边条文与标题未变; 全仓无引用这三行原文的检查脚本 (E17 同源) | 4 |

## 17. 既有检查与本轮运行结果 (实测复跑)

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| to-spec 测试 | `uv run --with gherkin-official pytest -p no:cacheprovider -q workflow/to-spec/tests` | 40 passed + 50 subtests, exit 0 |
| 技能文档检查 | `uv run python general/writing-for-llm/check_skill.py <to-spec/verify-change/navigate 三个 SKILL.md>` | 均 OK, exit 0 |
| 产品路径空白 | `git diff --check 9e8dd1df...HEAD -- workflow general README.md` | 空, exit 0 |
| 契约负断言 | `grep -rn "review_id\|--review" workflow general tests README.md pi agent-prompts` | 仅测试负断言 3 处 (`test_ac_draft.py:217,267-270`), E1 维持 |

## 18. 第三轮结论与边界

- 本轮发现总数: 0 个新增问题. 三行新差异无旧行为破坏; 上轮 N1/N2 均闭环 (第 14 节).
- 最严重问题: 本轮无新增; 全程累计最严重仍为 R1 (机械防串版缺失), 已由决策10 知情接受, 仅记录影响面, 非本轮或返工引入.
- 最终影响面 (de3b589): 开放项 R1/R2/R5/R9/R10/G1-G7/F1 在最终提交上全部仍开放且归属已记录于 EXECUTION.md; 三行收尾差异未改变任何既有结论, 全部既有检查复跑全绿.
- 未覆盖范围: 上轮 G1-G7 全部保持 (宿主同步链, Windows, 新流程端到端试跑, 历史 drill 实跑, 仓外调用方, R1 机械锚点, 全量 pytest 的 podman 隔离环境); 全量 `uv run pytest` 本轮同样未验证 (G8).
- 不声称找到全部影响: 本轮结论基于 a13085a..de3b589 逐行 diff, 全仓文本检索与既有可运行入口的复跑; 语义层面的跨技能执行偏差仍未观察.
- 提交状态: 按本轮授权, 本文件追加后随本轮提交 (第三轮收尾), 交付以 push 为准.
- 清理: 本轮全部命令只读或跑在测试栈临时目录内, 无 /tmp 残留, 未改本文件以外的任何文件.

---

# IMPACT-REVIEW 第四轮 (终局核对, 目标提交 3e486d3)

- 轮次: 第四轮 (终局核对), 追加于前三轮之后, 不覆盖旧轮次.
- 评审起点不变: `9e8dd1df`; 目标提交: `3e486d37d5caea2b5bc937bbd2c77474b50b97fb` (`git rev-parse HEAD` 实取).
- 本轮新差异 (相对上轮目标 de3b589): merge b9cb2db (issue/08, 即 1efb0f0 + 工单 cc1ef59) + 记录 27a39f2 (第三轮追加) 与 3e486d3 (集成记录). `git diff de3b589..3e486d3 --stat` 共 4 文件, 其中产品改动仅 1 句: `workflow/navigate/reference/VERIFICATION.md:9` 第 3 步分流条文替换为补问语义 (issue-08, 对照记录 `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-08/run1/alignment.md`); 其余为 EXECUTION.md 1 行, 本文件第三轮追加与工单, 不计产品.
- 授权: 除追加本文件并提交外只读.
- 方法: 本轮差异为单句纯条文, 无共享接口/数据格式/跨模块路径变更, 不触发 blast-radius 多模型深查; 重点为该文件的既有引用面 (navigate SKILL.md 与 verify-change/REVERIFY.md), 新句与 verify-change 修订段/AC-036/AC-041 的语义一致性, F1 闭环, 以及开放项在最终提交上的现状复测.

## 19. 第四轮关键安全事实

事实 S6: VERIFICATION.md:9 的单句替换无脚本化消费方, 无旧语义残留依赖. 旧句独特措辞 `判据或方案依据变化` 与 `重新确认方案` 全仓 (workflow/general/README/tests) grep 0 命中, 即无任何条文或脚本仍引用被删旧语义; 该文件是 markdown 引导条文, 无 py/sh 解析其内容 (`盘问专用` 等 py/sh 字面 0 命中, E17 同源维持). 新句与 `workflow/verify-change/SKILL.md:45-47` 修订段三分支一一对应: 转述错误直接修文不重问原决定 / 验证决定变化只补问受影响决定 / 新判据交回权威输入维护, 递增版本与不恢复逐版阅读采纳整份方案逐点对齐; 与 AC-036 @normal/@edge (PRODUCT.md:366-378) 及 AC-041 (PRODUCT.md:427-431) 语义同向, alignment.md 已逐条留证.
- 级别 4 (grep 全仓 + 逐行走读).

## 20. 本轮重点 1: VERIFICATION.md 替换句对既有入口/调用方的影响 (已排除)

| 检查 | 结果 |
| --- | --- |
| navigate/SKILL.md 两处引用 (:45 何时创建, :59 完成标准) | 均为链接引用, 只指向 "独立验证与返工" 页与派工/分流职责, 不复述第 3 步旧句措辞, 无残留旧语义依赖; check_skill.py OK |
| verify-change/REVERIFY.md 第 1 步 | 其 "有依据的转述错误直接修正并独立复查, 只补问新增或改变的验证决定, 不重新阅读采纳整份方案. 判据变化先回权威输入维护" 与新句语义完全一致 (同源措辞), 无冲突 |
| 第 3 步其余内容与第 1 步 (R5 相关) | diff 仅目标句, 紧邻句未动 (alignment.md 复核), 第 1 步 "已确认的 VERIFICATION-PLAN" 措辞保持, R5 现状不变 |
| 文件其余引用方 | `grep -rn "VERIFICATION.md" workflow README.md` 仅 navigate/SKILL.md:45/:59 与 VOYAGE.md:13 三处链接, 均不复述被替换句 |

## 21. 本轮重点 2: F1 闭环

- 原发现 F1: VERIFICATION.md:9 旧句 "判据或方案依据变化须先更新权威输入并重新确认方案" 与 AC-041 及 verify-change 补问语义方向相反 (第一轮记录, EXECUTION.md:26 载明待授权).
- 本轮核实: 旧句已整体移除且全仓无残留 (第 19 节 grep 0); 新句经 alignment.md 对照 AC-041/AC-036 与 verify-change:45-47 无冲突; EXECUTION.md:33 载明 ISSUE-08 完成 F1 (用户 2026-11-27 授权该文件补进允许范围), 切片提交 1efb0f0, 集成 b9cb2db.
- 结论: F1 闭环成立, 从开放清单移除, 处置为 "ISSUE-08 返工修复, 语义对齐留证".

## 22. 终局: 最终集成提交 3e486d3 上的全部开放项清单及归属

| 项 | 本轮复测 (实测) | 归属 |
| --- | --- | --- |
| R1 机械防串版缺失 | promote (ac-draft.py:285-303) grep `review\|版本` 0 命中, 仍无版本参数与比对 | 决策10 知情接受, 仅记录影响面 |
| R2 已安装技能库未同步 | `cmp ~/.agents/skills/to-spec/ac-draft.py workflow/to-spec/ac-draft.py` DIFF | 部署事项, 交用户 (宿主 sync-to-pi.py) |
| R5 下游 "已确认的 VERIFICATION-PLAN" 措辞错位 | to-execution:16/:35, drive-execution:26, VERIFICATION.md:5 共 4 处仍命中 | 跨文件措辞一致性, 交 milestone-12 用户审改 (N2 归属行) |
| R9 POSIX `cp --`/`cmp --` | SKILL.md:47-48 仍命中 2 处 | 可移植性, 同上 |
| R10 组合技能契约缺字段 | handoff/decision-ledger grep `盲区\|逐题` 0 命中 | 同上 |
| G1 宿主同步链未验证 / G2 Windows / G3 新流程端到端 / G4 历史 drill 实跑 / G5 仓外调用方 / G6 R1 机械锚点 / G7 根 pytest.ini 不含 to-spec tests (实测 testpaths 仍 3 项) | 无新观察 | 维持开放 |
| G8 全量 `uv run pytest` 未验证 (容器无 podman 隔离环境) | 本轮同样未跑全量; to-spec 子集复跑全绿 (第 23 节) | 交调用方环境 |
| 归档快照误报 | post-impl-snapshot/COMPARE.md: manifest-diff 464 行全为路径前缀写法差异, 归一化后 231 文件 SHA256 逐一同值, 未触碰已安装技能 | 已澄清, 非缺陷, 留证 |
| F1 | 已闭环 (第 21 节) | 移出开放清单 |

终局结论: 最终集成提交上无新增破坏; 本轮 0 个新增问题. 全程累计最严重仍为 R1 (机械防串版缺失, 决策10 知情接受). 上述开放项全部有明确归属记录, 其中 F1 本轮闭环.

## 23. 既有检查与本轮运行结果 (实测复跑)

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| to-spec 测试 | `uv run --with gherkin-official pytest -p no:cacheprovider -q workflow/to-spec/tests` | 40 passed + 50 subtests, exit 0 |
| 技能文档检查 | `uv run python general/writing-for-llm/check_skill.py workflow/navigate/SKILL.md` | OK, exit 0 |
| 产品路径空白 | `git diff --check 9e8dd1df...HEAD -- workflow general README.md` | 空, exit 0 |
| 契约负断言 | `grep -rn "review_id\|--review" workflow general tests README.md pi agent-prompts` | 仅测试负断言 3 处 (`test_ac_draft.py:217,267-270`), E1 维持 |
| 旧句残留 | `grep -rn "判据或方案依据变化\|重新确认方案" workflow general README.md tests` | 0 命中 |

## 24. 第四轮结论与边界

- 本轮发现总数: 0 个新增问题. 单句替换未破坏任何既有入口/调用方, 无旧语义残留依赖 (第 20 节).
- F1 闭环成立, 移出开放清单并注明处置 (第 21 节).
- 最终影响面一句话: 3e486d3 上开放项 R1/R2/R5/R9/R10/G1-G7/G8 与归档快照误报澄清全部维持且归属已记录, F1 已闭环, 四轮累计无未归属的行为破坏.
- 未覆盖范围: G1-G8 全部保持 (宿主同步链, Windows, 新流程端到端试跑, 历史 drill 实跑, 仓外调用方, R1 机械锚点, 全量 pytest 隔离环境).
- 不声称找到全部影响: 本轮结论基于 de3b589..3e486d3 逐行 diff, 全仓文本检索与既有可运行入口复跑; 语义层面的跨技能执行偏差仍未观察.
- 提交状态: 按本轮授权, 本文件追加后随本轮提交, 交付以 push 为准.
- 清理: 本轮全部命令只读或跑在测试栈临时目录内, 无 /tmp 残留, 未改本文件以外的任何文件.