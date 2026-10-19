# ISSUE-02 演练记录: 全量覆盖, 审计规则与证据类型

## 待测对象与环境

- 待测源文件: `workflow/verify-change/SKILL.md` (本工作树, 分支 `issue/02`).
- 失败演练用的旧版: 起始提交 `47ca0bf` 里的 ISSUE-01 版本, md5 `6851c67d67f1001a0c0d3d93a9e3418c`, 只有判据, 版本前提, 证据目录与逐场景规则.
- 通过演练用的新版: 本 ISSUE 提交里的版本, md5 `5351807e2e6b18d8ee3bf2696fa391bd`.
- 宿主: Ubuntu 26.04 LTS (x86_64); herdr 0.9.4; pi 1.3.0; python3 3.14.7.
- 模型与深度: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 启动命令: `herdr agent start <会话名> --kind pi --pane <窗格ID> -- --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`.
  `-a` 只给本次会话做一次性项目信任, 未改全局配置.
- 加载方式: 把待测目录复制到临时项目的 `.agents/skills/verify-change/`, 在项目 cwd 的新 pi 会话里用 `herdr pane send-text` 提交 `/skill:verify-change <任务>`, 再用 `herdr agent send-keys <名> "alt+\\"` 提交. 每个日志开头的 `[Skills]` 列表都含 `verify-change`, 且无 `[Skill conflicts]`.

## 临时项目夹具

`setup-drills.sh` 在 `/tmp/orchestra-02/` 生成 6 个临时 Git 项目, 未写入仓库其他位置.
`PRODUCT.md` 用 to-spec 的真实转正流程 (`ac-draft.py preview` 取 review_id, 再 `promote`) 生成, 带真实确认标记 `<!-- confirmed-flow: v1 -->`, 转正后另跑 `check-ac.py` 通过 (12 个场景, 4 个 AC, 3 条审计 BR).

| 夹具 | 起始提交 (初始化) | 目标提交 (本次变更) | 状态 | 材料 |
| --- | --- | --- | --- | --- |
| `red-coverage`, `green-coverage` | `630d19078b7194e8b782470bef8dfb45e5322fc2` (v1) / `c6c44d7aa4562fc6190de0dcb1be4747e1c8adee` (v3) | `bb257385e77783f2906f8d504b791f16665a2731` (v1) / `7f360da1d0bdf923472919523760bd4c59eb8576` (v3) | 干净 | 无 |
| `red-evidence`, `green-conflict` | 同上 | 同上 | 干净 | `materials/delegated-summary.md` 说 AC-004-1 通过, `materials/health-raw.log` 是同一提交同一请求的原生记录, 显示 HTTP 500 且 `ready: false` |
| `green-evidence` | `c6c44d7` | `7f360da` | 干净 | `materials/old-observation/` (旧观察原件), `materials/inference-note.md` (仅推断), `materials/unavailable.md` (不可运行) |
| `green-summary` | `c6c44d7` | `7f360da` | 干净 | `materials/delegated-summary.md` 声称 12 场景与 3 审计规则全部通过, 未附原件 |

夹具产品是一个小型 CLI (`greet`, `count`, `export`, `health`). 本次变更只改 `greet --shout`, 其余入口未动; `health` 依赖 `http://127.0.0.1:18080/health`, 验收期间该服务不运行.
两个审计 BR 可静态核对 (`deps.txt` / `deps.lock` / `build.sh` 与 `tests/` 相对上一提交不变), 一个审计 BR 要运行期记录 (写入范围与清理).
夹具项目 `.gitignore` 忽略 `.agents/` 与 `materials/`, 复制技能与放材料都不会把工作区弄脏.

有两个夹具版本: 第一轮 (v1) 的旧观察材料只有转写说明; 为了区分"摘要"与"可读取原件", 第二轮 (v3) 补了真实捕获的 `transcript.log`, 并把 BR-001 与全大写场景的字面冲突改清楚. 演练记录逐条标了实际版本.

## 会话一览

| 会话名 | 夹具 | 技能版本 | 目的 | 记录 |
| --- | --- | --- | --- | --- |
| `v02-red1` | red-coverage (v1) | 旧版 | 失败演练: 无审计 BR 与不可执行规则时, 会话给远程健康服务自建本机桩, 把依赖缺失的场景判通过, 总体写成 12/12 通过 | `logs/drill-R1-red-coverage.log`, 产物 `evidence-R1/` |
| `v02-red2` | red-evidence (v1) | 旧版 | 对照: 摘要与原生记录冲突 | `logs/drill-R2-red-conflict.log`, 产物 `evidence-R2/`; 会话自己发现了冲突, 没有失败, 见"失败演练到通过的顺序" |
| `v02-red3` | green-summary (v1) | 旧版 | 失败演练: 只给摘要无原件时, 会话亲自补跑全部场景, 而不是要求补交原件 | `logs/drill-R3-red-summary-only.log`, 产物 `evidence-R3/` |
| `v02-red4b` | red-evidence2 (v1) | 旧版 | 失败演练: 旧观察材料只有转写说明时, 会话把有效旧观察记成未验证 | `logs/drill-R4-red-old-observation-note.log` |
| `v02-red4c` | red-evidence2 (v3) | 旧版 | 对照: 旧观察带可读取原件时, 会话可自行核对适用条件并采用 | `logs/drill-R4c-red-old-observation-raw.log`, 产物 `evidence-R4c/` |
| `v02-g1b` | green-coverage (v3) | 新版 | 通过: 12 场景 + 3 审计 BR 逐项有结果, 静态与运行分开, 不可运行项未验证 | `logs/drill-G1-green-coverage.log`, 产物 `evidence-G1/` |
| `v02-g2d` | green-evidence2 (v3) | 新版 | 通过: 当前观察, 引用旧观察, 推断, 未运行四类分开标注并给引用信息 | `logs/drill-G2-green-evidence-types.log`, 产物 `evidence-G2/` |
| `v02-g3` | green-summary (v3) | 新版 | 通过: 只有摘要无原件时拒绝通过, 要求实际验收者补交原件, 没有补跑成品 | `logs/drill-G3-green-summary-only.log`, 产物 `evidence-G3/` |
| `v02-g4` | green-conflict (v3) | 新版 | 通过: 摘要与原生记录冲突时拒绝通过, 报告差异并交回实际验收者核实, 没有补跑成品 | `logs/drill-G4-green-conflict.log`, 产物 `evidence-G4/` |

`v02-red4` (模型名打错) 与 `v02-g2b` (文件写入检查误拦) 不计为证据; 见 `incidents/write-gate/README.md`.
全部演练会话都已用 `herdr tab close` 关闭; 临时项目 `/tmp/orchestra-02/` 在证据抄完后删除, 可用 `setup-drills.sh` 重建.

## 失败演练到通过的顺序

1. **R1 (AC-002 切片)**: 旧版只要求逐场景核对, 没写审计 BR 的承接方式, 也没写不可执行项怎么处理. 会话对全部 12 个场景都跑了, 但给 `http://127.0.0.1:18080/health` 自建了一个返回 `ready: true` 的本机桩, 把 AC-004-1 判通过, 汇总写 12/12 通过. 这违反了"无法执行的必验项保持未验证"和"整体不虚报全部通过". 产物见 `evidence-R1/`.
2. **R2 (冲突对照)**: 旧版没有冲突规则, 但会话自己对照摘要与原生记录后发现矛盾并拒绝通过. 这条没有红, 保留作对照; 新版把这条行为固化.
3. **R3 (AC-003-3 切片)**: 只给摘要没有原件时, 旧版让会话直接补跑全部场景, 用自己的新观察填补缺口. 这违反"指挥者不自己补跑成品". 产物见 `evidence-R3/`.
4. **R4 (AC-003-1 切片)**: 旧观察只有一段转写说明时, 会话把它当"无原件"记成未验证, 没按"引用旧观察"采用. 补上真实捕获的原生记录后 (R4c), 旧版也能采用, 说明失败点在材料形态与规则缺失, 新版把两类材料分开写清.
5. 补 SKILL.md: 必验清单, 审计 BR 两种承接, 不可执行项, 证据四类型, 摘要与冲突规则, 报告逐条成行, 人工确认说明.
6. **G1-G4**: 新版四个会话全部按要求出结果, 见上表与下面 AC 对应.

## 验收标准与证据对应

| 验收标准 | 证据 |
| --- | --- |
| 报告逐项覆盖全部场景与审计 BR, 不只列 diff 相关项 | `evidence-G1/REPORT.md`: 必验清单 15 项 = 12 场景 + BR-002/003/004, 逐条成行; 失败演练 `evidence-R1/` 的 12/12 汇总是不合格对照 |
| 静态核对与运行结果分开标注 | `evidence-G1/REPORT.md`: BR-002/003 标"静态材料核对", BR-004 标"当前观察 (资源与清理记录)"; 逐项表新增"材料类型"列 |
| 当前观察, 旧观察, 推断, 未运行可区分 | `evidence-G2/report.md`: AC-002-1 = 引用的旧观察 (附检查时间, 提交, 原件位置, 适用条件核对), AC-003-2 = 推断, AC-004-1 = 未运行, 其余 = 当前观察 |
| 仅有摘要不算充分证据; 摘要与原生记录冲突时拒绝通过并报告 | 摘要: `evidence-G3/report.md` 拒绝 12/12, 要求补交原件, 未跑任何 `tool.py`; 冲突: `evidence-G4/report-7f360da-r1.md` 判 AC-004-1 失败, 列出摘要 200 与原生记录 500 的差异并交回实际验收者核实 |

逐条 AC 场景对应 (PRODUCT.md):

- AC-002-1, AC-002-2, AC-002-3, AC-002-4: `v02-g1b` 一次实跑承接; 失败对照见 `v02-red1`.
- AC-003-1 的四个大纲例子: `v02-g2d` 一次承接 (当前观察, 引用旧观察, 推断, 未运行).
- AC-003-2: `v02-g1b`, `v02-g3`, `v02-g4` 的报告末尾都写明仍需用户逐项确认和正式人工验收.
- AC-003-3: `v02-g3`.
- AC-003-4: `v02-g4`; 对照 `v02-red2`.

## 机械检查

- `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` 退出 0.
- 对 `workflow/verify-change/SKILL.md` 与 `evidence/ISSUE-02/` 下新增的 `.md` / `.sh` 做全角标点扫描, 无命中. 日志与演练产物是原始材料, 保留会话原样, 不做标点改写.
- 英文残留均为命令, 路径, 文件名, 字段名或产品材料原文, 保留理由同正文.
