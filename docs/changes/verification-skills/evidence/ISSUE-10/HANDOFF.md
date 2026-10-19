# ISSUE-10 交接报告

## 交付了什么

在既有 `workflow/verify-change/SKILL.md` 上增量补齐三个切片, 没有推翻 ISSUE-01..05 已实现部分, 没有新建或修改任何项目级配方, 没有实现两项复刻本身:

- AC-011 写入授权与清理:
  - 新增第 5 步 "先定写入授权与清理": 默认只读; 开跑前把测试资源, 对象, 操作, 清理方式与清理验证交用户批准; 同范围再次写入或复跑不重复要批准, 换资源/对象/操作/清理范围先停下要新批准; 未批准的写入不发生; 派工单原样交批准范围并要求记录每次写入与清理; 清理失败或残留单列, 该项不算整项通过, 不擅自扩大清理范围, 产品观察保留, 残留不写成产品功能失败.
  - 第 9 步报告新增 "写入与清理记录" 节与残留对象要求.
  - 边界一节增加 "写测试资源前先按第 5 步取得批准并记录清理".
- AC-012 实现问题与缺口分类:
  - 第 7 步新增三类去向: 已证实的实现问题交回实现流程 (指挥者不修复, 不改代码); 尚缺产品规则只停受影响项并交回决策流程, 其他项继续但整体不报全部通过; 权限或环境缺口单独列出并写清影响场景, 不写成产品实现失败; 方法跑完仍无法证实的安全事实归入未验证.
  - 第 9 步报告新增三类去向小节, 汇总不用全部通过一类总标签.
- AC-013 条件调用两项方法:
  - 第 4 步分组时按标准需要安排方法: 性能结论由承接组用 benchmark-checklist, 依赖未实证关键安全假设由承接组用 blast-radius; 其他组不强制, 派工单不写无关方法; 两项方法是实际验收者的工具, 指挥者不亲自调用.
  - 第 6 步派工单要求写明由该组实际验收者自己点名加载方法, 方法结论仍按 PRODUCT.md 判定.
  - 第 9 步派工记录要求写明哪名验收者, 哪个场景组, 什么入口调用; 指挥者没有亲自调用代替.
  - 边界增加 "不替实际验收者调用 benchmark-checklist 或 blast-radius".
- 步骤编号从 8 步改为 9 步, 原有 "第 6/7 步", "第 7 步", "第 1 到 8 步" 等交叉引用已同步改为新编号.
- 新增 `docs/changes/verification-skills/evidence/ISSUE-10/`: 夹具脚本, 两个待测技能版本, 两个临时产品, 红/绿演练原始报告与命令输出, 会话 jsonl, 加载来源核对, 任务文本, 清理记录.
- 未改 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` / 既有 Spec; 未改其他既有技能与 `general/`; 未写全局部署副本; 未运行 `sync-to-pi.py`; 未在 ISSUE 文件或 EXECUTION.md 勾选复选框; 演练目标项目没有改产品代码, 配置或测试 (只有证据目录新增与 gitignore 内 runtime).

## 每个验收标准对应证据

| 验收标准 | 证据文件 |
| --- | --- |
| AC-011-1 批准范围内写入可复查, 扩大范围先停止并请求批准 | `drill-green-011-012/report.md` "写入与清理记录"表 (init, account-ensure, 两次同一 note-put, 命令与结果), AC-001-1 行; `drill-green-011-012/plan.md` "写入授权"节; AC-002-1 行与 "权限与环境缺口" 节 (config/shared.json 未批准, 未改); `drill-green-011-012/verifier-1/state.log` 与 `premise.txt` 的 config sha256 相同 |
| AC-011-3 清理残留单列, 不冒充产品通过或失败 | `drill-green-011-012/report.md` 汇总 "另有 1 项清理未完成", "写入与清理记录"表最后一行 `account-delete` rc=2, 单独 "残留对象 (清理未完成, 单列)" 小节, 明确不当作整项通过也不写成产品失败; `drill-green-011-012/verifier-1/data-state-final-accounts.json`; 红对比 `drill-red-011-012-r2/REPORT.md` 把残留写成 "非判据事项", AC-001-1 仍记通过 |
| AC-012-1 实现问题交回实现流程 | `drill-green-011-012/report.md` "明确实现问题 (交回实现流程)" 节: AC-004-1 稳定失败, 定位到 `cmd_note_list` locked 分支, 交回实现流程, 验收不改代码; 红对比 `drill-red-011-012-r2/REPORT.md` 只有逐项表失败, 没有交回节 |
| AC-012-2 缺产品规则只停受影响项 | `drill-green-011-012/report.md` "缺产品规则 (交回决策流程, 只停受影响项)" 节: AC-005-1 因 BR-002 未给期限受阻, 其他项继续, 汇总不是全部通过; 红对比 `drill-red-011-012-r2/REPORT.md` 把它当 "缺 retention_period 与写入授权" |
| AC-012-3 权限/环境缺口不写成实现缺陷 | `drill-green-011-012/report.md` "权限与环境缺口 (未验证)" 节: AC-002-1, BR-001, AC-006-1 分开列受影响标准与缺口, 不记产品失败; 红对比 `drill-red-011-012-r2/REPORT.md` 只在 "越界风险" 段落里散记 |
| AC-013-1 按场景组由实际验收者调用两项方法 | `drill-green-013/00-plan.md` 分组表 (组 1 benchmark-checklist, 组 2 blast-radius); `drill-green-013/90-report.md` 4.4 节; `drill-green-013/V1-perf/REPORT.md` 第 2 节与 `V2-del/REPORT.md` 第 4 节; `logs/loaded-locations.txt` 的会话加载记录; 红对比 `drill-red-013/PLAN.md` 只有 benchmark-checklist, 没有 blast-radius |
| AC-013-2 安全事实仍无法证实时该项未验证 | `drill-green-013/90-report.md` AC-002-1 行 "未验证"; `drill-green-013/V2-del/REPORT.md` 第 4 节 F3 "级别 1 都不到, 未证实" 与缺权限/入口; 没有同时给通过, 没有用方法自定标准替代 PRODUCT.md; 红对比 `drill-red-013/REPORT.md` AC-002-1 也记未验证, 但没调用 blast-radius |

## 跑了哪些命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` | 0 | `workflow/verify-change/SKILL.md: OK` |
| 全角标点扫描 (U+3000-U+303F, U+FF01-U+FF5E, U+FFE0-U+FFEE), 对提交的 SKILL.md 与本次自写证据说明 (README, setup-drills.sh, logs/, fixtures/) | 0 | 19 个自写文件 0 命中 |
| 全角标点扫描, 对全部证据文件 (含验收者生成的原始报告与会话 jsonl) | 0 (扫描本身) | 53 处命中, 全部在验收者生成的原始报告/计划与会话 jsonl 中; 属原始材料, 保留原样未改写 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | `7 passed, 18 subtests passed` |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed in 274.94s`; 失败集合与 `evidence/BASELINE.md` 完全一致 (present 5 条 + mailbox pending_cap 1 条), 未新增失败 |
| `bash setup-drills.sh init` / `install-skill` / `install-methods` / `status` | 0 | 建 2 个夹具母版与 4 个克隆, 各带起始提交; 复制 verify-change, blast-radius, benchmark-checklist |
| `uv run workflow/to-spec/ac-draft.py preview/promote`, `uv run workflow/to-spec/check-ac.py` | 0 | 两个 PRODUCT.md 真实转正, 带 `<!-- confirmed-flow: v1 -->`, check-ac 通过 |
| `herdr tab create` / `agent start` / `pane send-text` / `agent send-keys` / `agent read` / `tab close` | 0 | 会话一览见 `README.md`; 收尾无本 ISSUE 存活会话与标签 |
| `git clone` / `git log` / `git status` / `git diff` (夹具与工作树) | 0 | 夹具 HEAD 与目标提交一致; 被验项目只有证据目录未跟踪; 本工作树只有 SKILL.md 修改与 ISSUE-10 证据目录新增 |

## 会话与临时项目

- 有效会话: 红 `i10-red-bnd`+`verify-acct-1`, `i10-red-bnd2`+`ver-acc1`/`ver-acc2`, `i10-red-mth`+`ver-a`/`ver-b`; 绿 `i10-green-bnd`+`verifier-1`, `i10-green-mth`+`verify-perf`/`verify-del`. 会话 id 与记录目录见 `README.md`.
- 临时项目: `/tmp/orchestra-10/{boundaries-red,boundaries-red2,boundaries-green,methods-red,methods-green}`, 起始提交 `bc435db` / `ea94082`. 证据抄完后整体删除, 记录在 `logs/cleanup.txt`; 绿色 AC-011 的故意残留快照已抄进 `drill-green-011-012/verifier-1/data-state-final-accounts.json`.
- 真实加载来源: `logs/loaded-locations.txt` 从每个指挥会话 jsonl 抽出 `<skill name=... location=...>`; 红演练对上 v1 md5 `f66877da...`, 绿演练对上 v2 md5 `bc59d779...`.
- 方法加载: 性能组验收者读取 `.agents/skills/benchmark-checklist/SKILL.md`, 安全组验收者读取 `.agents/skills/blast-radius/SKILL.md`, 都是项目当前文件; 未用旧部署副本或手抄正文.

## 缺口与风险

1. **红演练不是每个 AC 都失败**: AC-011-1/2, AC-012-3, AC-013-2 在旧版的任务文本与验收者谨慎下已经表现可接受. 决定性的红失败是 AC-011-3 (残留被写成非判据事项, 逐项仍通过), AC-012-1 (实现失败没有交回节), AC-012-2 (缺规则被当缺配置), AC-013-1 (没有 blast-radius). 绿演练证明新规则在这些点上改变了行为, 同时没有破坏其余行为.
2. **AC-011-2 的 "停止并请求批准" 是报告式请求**: 任务已写明共享配置未批准, 验收者没有先尝试再停下, 而是在报告里列出缺的授权与下一步. 未观察到交互式地问用户 "要不要批准". 未批准的写入确实没有发生.
3. **方法加载方式**: 两项方法由验收者用 read 工具读取项目 `.agents/skills/<name>/SKILL.md` 后执行, 不是用 `/skill:<name>` 点名加载. 方法内容与证据级别按当前文件执行, 但没有证明点名入口下也成立. 若验收要求必须走 `/skill:` 入口, 这一条尚未验证.
4. **init 范围解释**: 绿色 AC-011 报告把 "按 README 建立 runtime/data 测试实例" 解释为批准资源 `runtime/data` 的一部分, 并把它标为需用户复核. 若用户认为 init 不在字面批准对象内, 依赖该实例的 AC-001-1/AC-003-1/AC-004-1/AC-005-1 结论需要重跑.
5. **原始证据含全角标点**: 验收者生成的原始报告与会话记录中有 53 处全角标点. 本次没有改写原始材料; 自写的 SKILL.md, README, 脚本, 日志与夹具文件 0 命中.
6. **样本少**: 每个场景基本一次运行, 未重复抽样; 没有测其他模型或其他宿主; 性能数字只在 `/tmp` (tmpfs), 2 万行, 无 fsync 条件下成立.
7. **未验证**: 其他运行时或全局部署下的加载与行为; `tdd-as-orchestra` 的验收节点接入 (ISSUE-14); 两项复刻的其他接入点; `/skill:` 点名加载两项方法的入口行为.
8. **临时项目已删**: 夹具不能直接从 /tmp 重跑, 但 `setup-drills.sh` 与 `fixtures/` 保留, 可重建.

## 提交哈希

- 实现与证据提交: `a1648f45fad3d1285609e880d89468d84ffeb9cb` (`feat: ISSUE-10: 写入授权与清理, 问题分类与条件方法切片及演练证据`).
