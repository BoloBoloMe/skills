# HANDOFF: ISSUE-21 create / maintain 视角与重复批准规则

## 交付了什么

两份技能正文的写作面修订, 不改批准语义, 不改运行时行为:

1. `workflow/create-verification-skill/SKILL.md`
   - 写入授权的 "交用户批准" 改 "交我批准"; 派工单句 "你转给用户决定" 改 "你转给我决定".
   - 原三段共用规则收拢到 `**共用批准规则.**` 一处, 改为三条列表项, 并写明 "生成与维护配方共用, 只在这里维护, 维护配方按 `maintain-verification-skill` 的指针读回这里".
   - "生成配方的批准不覆盖运行期临时数据" 改为 "生成或修配方的批准都不覆盖运行期临时数据", 一句话覆盖两个技能, 约束强度不变.
2. `workflow/maintain-verification-skill/SKILL.md`
   - "交用户批准" 改 "交我批准"; "你转给用户决定" 改 "你转给我决定".
   - 删掉与 create 逐字重复的两段规则和重复的第三段, 只留自己的资源清单四项, 加一句写入前必读指针: 相对链接指向 `../create-verification-skill/SKILL.md` 的 "共用批准规则", 点名该节管的四件事, 并声明不重复原文.
   - 两份文件各自的 `完成标准` 句都保留.

新增证据目录 `docs/changes/verification-skills/evidence/ISSUE-21/`: 审计脚本 1 个, 红绿日志 2 份, diff 1 份, 机械检查 1 份, 全量快层 1 份, 切片记录 1 份, 说明 1 份, 本 HANDOFF.

## 每个验收标准对应的证据

| 验收标准 | 证据文件 | 要点 |
| --- | --- | --- |
| 视角统一, 有扫描证据 | `red-voice-dedupe.log`, `green-voice-dedupe.log`, `TS-001-voice-dedupe.md` (红轮 / 绿轮节) | 红轮 4 条视角命中 (create:22, create:33, maintain:35, maintain:46), 绿轮 0 命中; 扫描排除固定术语 "用户入口" 与 "用户调用" |
| 重复规则合并为一处, 有 diff 证据 | `diff-skills.log`, `TS-001-voice-dedupe.md` (改法 / 语义保持核对节), `red-voice-dedupe.log` | 红轮 2 条逐字重复 (116 字符与 81 字符整段) 加 4 条结构性命中; 绿轮 0; diff 显示 maintain 侧只删不加规则原文, create 侧三条规则保留并标为共用 |
| 不改批准语义 | `TS-001-voice-dedupe.md` 语义保持核对节, `diff-skills.log` | 批准绑定四样, 同范围复跑, 换范围再批准, 已信任/免审批不等于写入权限, 运行期临时数据单独批准, 派工单随范围下发并记录写入清理: 原文都还在, 只在 create 处集中; maintain 用指针加四件事摘要承接 |

覆盖依据是评审 `../code-review/STANDARDS-2.md` 的 N1 与 N3, 不新增也不重验任何 AC 行为. 与本 ISSUE 相关的 PRODUCT AC-016 至 AC-020 的行为层结论未变, 沿用既有演练证据, 本轮不另作断言.

## 跑过的命令与退出码

| 命令 | 结果 |
| --- | --- |
| `uv run python docs/changes/verification-skills/evidence/ISSUE-21/check-issue21.py <两份 SKILL.md>` (修订前, `711b463`) | `hits=10`, 退出码 1, 见 `red-voice-dedupe.log` |
| 同上 (修订后) | `hits=0`, 退出码 0, 见 `green-voice-dedupe.log` |
| `uv run python general/writing-for-llm/check_skill.py workflow/create-verification-skill/SKILL.md` | `OK`, 退出码 0 |
| `uv run python general/writing-for-llm/check_skill.py workflow/maintain-verification-skill/SKILL.md` | `OK`, 退出码 0 |
| 全角标点扫描 (`rg`, 覆盖两份 SKILL.md 与本证据目录全部文件, 含 U+2014 与全角引号) | 无命中, `rg` 退出码 1, 见 `machine-checks.log` |
| 英文残留扫描 (`rg`, 两份 SKILL.md) | `rg` 退出码 0, 逐条人工复核: 全部是技能名, 文件名, 路径, 既有固定术语 (`PRODUCT.md`, `disable-model-invocation`, `/skill:`, `use-herdr` 等), 无需要翻译的正文英文; 本次新增英文只有 `maintain-verification-skill` 与 `../create-verification-skill/SKILL.md` 两处引用, 是文件与技能标识 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | `7 passed, 18 subtests passed` |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed in 275.24s`, 退出码 1; 6 条失败与 `../BASELINE.md` 逐条相同 (全是环境/超时类), 未见新增失败, 见 `full-suite.log` |

## 会话与临时项目

本轮不适用: 纯写作面修订, 不改加载行为也不改批准语义, 按任务书 "通常不需要真会话演练" 处理. 未开 herdr 会话, 未建临时项目, 未改 `~/.agents` 或 `~/.pi`, 未运行 `sync-to-pi.py`; 没有需要清理的运行期资源. 临时目录只用了 `/tmp/orchestra-21/red.log`, 内容已抄成 `red-voice-dedupe.log` 并删除, `/tmp/orchestra-21` 已移除.

## 提交

- 实现提交: `20afd79b0027349484ea0f56d43d3cb983e96941` (`feat: ISSUE-21: 统一 create/maintain 的视角并把重复批准规则并入一处`), 分支 `issue/21`, 父提交 `711b463`.
- 本 HANDOFF 单独一个提交, 见 `git log --oneline -2`; HANDOFF 不写自身哈希, 避免自指.

## 缺口 / 风险 / 未验证项

- 指针跨技能目录: maintain 的相对链接指向同级 `create-verification-skill`. 两技能在本仓库同级且一起同步部署, 链接成立; 若只部署 maintain 而不带 create, 指针会悬空. 这是 N3 消除重复指令的代价, 落在任务书 "共用规则只保留一处并用指针承接" 之内.
- 扫描口径的局限: 视角命中靠固定术语白名单 (`用户入口`, `用户调用`), 重复命中只比逐字相同的整行 (阈值 20 字符). 近义改写造成的重复与新的第三人称说法查不到, 仍要靠人读.
- 未验证项: 没有真会话演练. 本轮不改行为, 行为层证据沿用 `../ISSUE-17/` 与 `../ISSUE-12/`; 若后续要求重验批准流程行为, 需要另开演练, 本轮不声明行为已重验.
- 未做: 未勾选 EXECUTION.md 与 ISSUE 文件里的复选框 (按要求留到合并节点), 未推送, 未合并, 未动其他 ISSUE 与其他技能.
