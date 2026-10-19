# ISSUE-02 交接报告

## 交付了什么

- 在既有 `workflow/verify-change/SKILL.md` 上增量补齐两个切片:
  - AC-002: 输入阶段先抄全必验清单 (全部验收场景 + 标 `(审计)` 的 BR, 条数等于两者之和); 审计 BR 分静态材料核对与运行过程记录两种承接; 无法执行的必验项保持未验证, 禁止用自建服务桩或本地替身改判通过; 整体结论不虚报全部通过.
  - AC-003: 新增第 5 步复核材料与证据类型, 区分当前观察, 引用的旧观察, 推断, 未运行并各带引用信息; 只有摘要无原件不算充分证据, 要求实际验收者补交原件且不自己补跑; 摘要与原生记录冲突时拒绝通过, 报告差异并交回核实; 报告末尾说明仍需用户逐项确认和正式人工验收.
- 新增 `docs/changes/verification-skills/evidence/ISSUE-02/`: 夹具生成脚本, 9 个有效演练会话的原始记录, 8 份会话产物副本, 2 份失败对照与 1 份误拦事故记录.
- 没有改 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` / 既有 Spec, 没有改其他既有技能, 没有写全局部署副本, 没有运行 `sync-to-pi.py`, 没有在 ISSUE 文件或 EXECUTION 里勾选复选框, 没有提交或推送演练项目.

## 提交

- `77b2d16b37d9d62b0891537f5c59090a7dee3e70` 实现与证据 (本报告在其后的第二个提交里).

## 每个验收标准对应证据

| 验收标准 | 证据文件 |
| --- | --- |
| 报告逐项覆盖全部场景与审计 BR, 不只列 diff 相关项 | `evidence-G1/REPORT.md` 的 "必验清单与逐项结果" (15 项 = 12 场景 + BR-002/003/004); 失败对照 `evidence-R1/` 显示旧版把依赖缺失场景判通过 |
| 静态核对与运行结果分开标注 | `evidence-G1/REPORT.md`: BR-002/BR-003 标 "静态材料核对", BR-004 标 "当前观察 (资源与清理记录)"; 逐项表含 "材料类型" 列 |
| 当前观察, 旧观察, 推断, 未运行可区分 | `evidence-G2/report.md`: AC-002-1 "引用的旧观察" 附检查时间/提交/原件位置/适用条件核对, AC-003-2 "推断", AC-004-1 "未运行"; 其余 "当前观察" |
| 仅有摘要不算充分证据; 摘要与原生记录冲突时拒绝通过并报告 | 摘要: `evidence-G3/report.md` (拒绝 12/12, 要求补交原件, 未运行任何 `tool.py`); 冲突: `evidence-G4/report-7f360da-r1.md` (判 AC-004-1 失败, 列出摘要 200 与原生记录 500 的差异, 交回实际验收者核实) |

AC 场景到会话的对应关系, 夹具提交, 会话名与加载方式见 `README.md`.

## 跑了哪些命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` | 0 | `OK` |
| `rg -n` 扫描全角标点 (U+FF0C, U+FF1B, U+FF1A, U+FF01, U+FF1F, U+3001, U+FF08, U+FF09, U+3002) 覆盖 SKILL.md, README.md, HANDOFF.md, setup-drills.sh, 事故 README | 1 | 无命中 (rg 无匹配时退出 1) |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | 7 passed, 18 subtests passed |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | 6 failed, 659 passed, 2 skipped; 与 ISSUE-01 HANDOFF 记录的既有失败集合完全一致 (present 浏览器 5 条 + mailbox pending_cap 1 条), 本次未新增 |
| `bash setup-drills.sh <工作树>` (v1 与 v3 各一次) | 0 | 生成 6 个临时 Git 项目; PRODUCT.md 经 `ac-draft.py preview/promote` 转正, `check-ac.py` 通过 (12 场景 / 4 AC) |
| `herdr tab create` / `agent start` / `pane send-text` / `agent send-keys` / `agent read` / `tab close` | 0 | 会话一览见 `README.md` |

## 会话与临时项目

- 有效会话: `v02-red1`, `v02-red2`, `v02-red3`, `v02-red4b`, `v02-red4c`, `v02-g1b`, `v02-g2d`, `v02-g3`, `v02-g4`. 全部已 `herdr tab close`.
- 作废会话: `v02-red4` (模型名打错), `v02-g2b` (宿主写入检查误拦), 见 `incidents/write-gate/README.md`.
- 临时项目: `/tmp/orchestra-02/{red-coverage,red-evidence,red-evidence2,green-coverage,green-evidence,green-evidence2,green-summary,green-conflict}`, 起始提交与目标提交见 `README.md` 夹具表. 证据抄完后已删除, 可用 `setup-drills.sh` 重建.
- 待测源路径: 本工作树 `workflow/verify-change/SKILL.md`. 失败演练用起始提交 `47ca0bf` 的 ISSUE-01 版 (md5 `6851c67d...`), 通过演练用本提交版 (md5 `5351807e...`).
- 宿主与版本: Ubuntu 26.04, herdr 0.9.4, pi 1.3.0, python3 3.14.7; 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high, 启动带 `-a` 只做一次性项目信任.

## 缺口与风险

1. **旧观察材料的形态会影响结论**: 材料只有一段带命令和输出的转写说明时, 旧版 (R4) 把它当 "无原件" 记未验证; 补上真实捕获的 `transcript.log` 后 (R4c, G2) 才被当作可引用的旧观察. 新版规则把 "摘要无原件" 与 "引用的旧观察" 分开写, 但两类材料在现实里可能长得像. 后续若需要更硬的判定, 应由 Spec 明确原件最低形态, 本 ISSUE 未自行添加.
2. **两条对照演练没有红**: 冲突检测 (R2) 与带原件的旧观察 (R4c) 在旧版下也能通过, 属该模型已有的临场能力. 新版规则把这两条行为固化, 但没有 "旧版失败" 的对照; 其余失败点 (自建桩顶替, 摘要后补跑, 转写说明当无原件) 有真实红.
3. **角色隔离未验证**: 本轮只有一名验收者, AC-003-3/4 的 "转交摘要 / 原生记录" 通过把材料放进临时项目交给同一会话来承接, 真正的非作者委派与场景组派工属 ISSUE-03/04, 本 ISSUE 不承诺.
4. **加载方式只覆盖一种**: 演练走项目 `.agents/skills/verify-change/` + `/skill:verify-change`; 其他运行时的加载方式与全局部署未验证, 未运行 `sync-to-pi.py`.
5. **宿主写入检查误拦**: `v02-g2b` 的一次批量脚本被 `filesystem-operation-gate` 误判为 cwd 外写入并拦下, 会话随后失去响应; 重开 `v02-g2d` 并把临时文件放进证据目录后通过. 这是宿主扩展行为, 不是待测技能结论; 未改全局配置.
6. **夹具版本混合**: 失败演练用 v1 夹具 (`630d190` / `bb25738`), 通过演练用 v3 夹具 (`c6c44d7` / `7f360da`); v3 修正了 BR-001 与全大写场景的字面冲突并补了旧观察原件. 各会话自己的日志与产物里记录了当时的提交, 未把两版混成一次结论.
7. **未运行**: 未做端到端 tdd-as-orchestra 接入 (ISSUE-14), 未跑复验与并行 (ISSUE-04), 未在真实产品项目上验收.
