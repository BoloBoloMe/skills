## 父级
- `../EXECUTION.md`

## 执行
- [x] 已完成

## 要交付什么
完成 to-spec 从盘问到正式规格的完整候选流程, 包括用户亲答和可查事实入账,按需跨会话续问,反方与写后独立检查,按影响修文或补问,产品正文暂存稿/独立验收场景草稿/技术草稿三份临时材料,可选预览及产品机械转正/技术稿复制. 更新公开 CLI 与必要测试, 使新说明能从真实入口运行. 复用 milestone-01 已完成的正文编号汉化, 不生成重复汉化任务.

## 覆盖依据
- Product: `PRODUCT.md`, 验收1-24(@AC-001至@AC-024), 验收26-30(@AC-026至@AC-030), 规则1-15.
- Technical: `TECHNICAL.md`, 模块划分, 模块接口中的盘问与确认/独立会话与修正/脚本与文件/分段续问, 接缝与依赖, 安全策略, 关键流程1-4.
- 验证依据: `VERIFICATION-PLAN.md` 中对应的全部产品行,规则9/10/11/12/15审计行,to-spec测试工程行和技术格式机检子项.

## 相关决策
- `DECISIONS.md`: 决策40, 决策41, 决策42.

## 允许范围
- `workflow/to-spec/SKILL.md`, `workflow/to-spec/TEMPLATES.md`, `workflow/to-spec/GHERKIN.md`, `workflow/to-spec/ac-draft.py`, `workflow/to-spec/check-ac.py`, `workflow/to-spec/check-tech.py`, `workflow/to-spec/tests/`.
- 只在本 issue 的 to-spec 范围及其对应既有行为内修改. 若发现范围外规则可能有缺口, 记录到父级集成检查; 不在本 issue 执行全仓编号/历史审计或据此扩大修改. 优先复用现状, 不重做 milestone-01.

## 禁止范围
- 不改 `PRODUCT.md`, `TECHNICAL.md`, `VERIFICATION-PLAN.md`, `DECISIONS.md`, `roadmap/ROADMAP.json`, `REVIEW-milestone-01.md` 或历史快照.
- 不改已安装 skill, 不整体调用或改写 deliberate, 不新增盘问记录文件/章节/格式,服务或依赖.
- 不把 preview 变成确认入口, 不保留 `review_id` 或 `--review` 兼容, 不改正式标记为可变版本.
- 不用私有函数,mock 解析器或假文件替代真实公开 CLI 与文件系统验证.

## 代码定位提示
- 流程入口: `workflow/to-spec/SKILL.md`; 核对引用的模板和 Gherkin 条文时看 `workflow/to-spec/TEMPLATES.md` 与 `workflow/to-spec/GHERKIN.md`.
- 脚本公开入口: `workflow/to-spec/ac-draft.py` 的 argparse `main`, `workspace`, `preview`, `promote`; 当前 `review_id` 定义在文件开头, promote 参数在 `main` 中. 当前原子写入及输入/正式目标复核逻辑位于 promote 写入路径.
- 格式 CLI: `workflow/to-spec/check-ac.py`, `workflow/to-spec/check-tech.py`.
- 现有回归位置: `workflow/to-spec/tests/test_ac_draft.py`, `workflow/to-spec/tests/test_ac_reading.py`. 先读现有测试和公开 CLI 帮助, 不从私有入口推断外部契约.

## 验证契约
- 变更类型: 行为变更.
- 对应范围: to-spec 操作条文与账本/交接调用行为; preview/promote 的公开参数,JSON,退出码,原文和原子替换; 输入变化及正式目标变化保护; check-ac/check-tech 的格式及编号行为.
- 验证要求/证据: 使用真实 gherkin 解析器,公开 CLI 和真实隔离文件. 保存合成输入,完整命令,stdout/stderr,退出码,生成文件及其摘要. 技能条文以逐条语义对照证据验证. 原子替换和并发保护另留可复查系统事件及时序, 不以单测通过替代. 不适用性能或结构变更验证.

## 验证入口
1. 对照 `PRODUCT.md` 的验收1-18及26-30, 逐条检查候选 to-spec 条文和实际调用关系. 同一 `@AC` 下的每个 normal/failure/edge 场景分别对应到条文位置和预期, 不只按 AC 标题合并判断. 核对一句话问法,严格直译免问边界,拿不准即问,同判定只问一次,已定不重问,闭环清单与明确确认,逐节覆盖和盲区,按需 handoff,反方与正式检查使用不同会话,检查依据不自证,误报/有据修文/缺判定补问分流,用户验收权限,审计证据归账本,脱敏最小材料及专用预览目录.
2. 对照现行 `general/grilling/SKILL.md`, `general/handoff/SKILL.md`, `general/opposing-viewpoint/SKILL.md` 与领域维护入口, 确保 to-spec 组合现有能力, 不整体调用 deliberate, 不改其他调用者的四步语义, 不新增盘问专用持久记录或免问清单. 搜索结果逐项分类, 不以关键词命中作语义结论.
3. 公开 CLI 实跑合成材料:
   - preview: `uv run python workflow/to-spec/ac-draft.py preview <产品暂存稿> <验收草稿>`. 核对 JSON `success` 与预览/原文件路径, 页面有展开卡片和原文, 两个输入字节未变, 页面仅供选看且没有确认入口.
   - promote: `uv run python workflow/to-spec/ac-draft.py promote <产品暂存稿> <验收草稿> <隔离正式稿>`. 不提供 review 参数时成功; stdout 不暴露 review_id; 验收内容逐字节嵌入, 其余产品正文保留, 代码块前固定 `<!-- confirmed-flow: v1 -->`. 用原始文件比较和系统文件事件核实原子替换.
   - 用例19保护 preview 的路径,卡片/原文和输入不变; 用例20保护无 review 参数转正,固定 v1,原文嵌入和其他节保留; 用例21保护 `--review` 不再属于公开参数且无兼容分支. 所有命令从进程入口运行.
   - 用例22先用坏格式/编号输入证明命令非零退出且已有隔离正式稿字节不变. 再由真实外部进程分别在 promote 已读入产品暂存稿,已读入验收草稿后改变相应输入, 以外部事件证明改动处于输入复核窗口; 改动必须被发现, 不得转正旧内容. 另以真实外部进程在正式目标已核验,尚未替换时修改目标, 恢复 CLI 后证明停止替换并保留并发修改. 三种变化分别留时序和前后原件, 不能互相代替.
4. 按目标版本公开帮助确定 check-ac 参数, 用 `uv run python workflow/to-spec/check-ac.py ...` 从 CLI 执行用例23和用例24. 用例23证明 `目标1`/`规则2` 与 `@G-001`/`@BR-002` 对账通过. 用例24的七个违规各用独立合成输入运行, 每例只改一个条件: 引用不存在的 `@G-099` -> 退出码1并报目标不存在; 将 `@BR-009` 挂到审计规则9 -> 退出码1并报审计条目不可进 Gherkin; 重复 `目标1` -> 退出码2并报编号不唯一; 使用 `假如` -> 退出码1并报关键字不在白名单; 同一场景挂 `@AC-001` 和 `@AC-002` -> 退出码1并报 AC 数量错误; 使用 `@smoke` -> 退出码1并报自由标签; 草稿自带确认标记 -> 退出码2并报草稿不得带标记. 逐项对照 `VERIFICATION-PLAN.md` 留输入,输出和退出码.
5. 按 `VERIFICATION-PLAN.md` 的规则12子项, 用 `uv run python workflow/to-spec/check-tech.py <合成技术文件>` 经公开 CLI 核对合法必备节输入成功,合法条件节输入成功,四个必备节逐个缺失,固定节名逐个写错,固定节序错误. 每个失败输入只构造一个错误并保留原件. 记录基线和目标在相同输入/环境下的输出及退出码; 不从候选实现倒推预期. 若规格模板与基线观察冲突, 报缺口而不擅改标准.
6. 技术草稿按候选流程经机检后机械复制到隔离正式文件, 用字节比较核实完全一致; 不由模型复制重写. 整组任一文件失败时检查条文是否要求保留现场,补齐失败步骤并复查两份后才交付, 不误写为双文件同时替换事务.
7. 复用 milestone-01 编号汉化. 对本 issue 实际修改的编号规则和对应既有行为, 对照 `REVIEW-milestone-01.md` 核对没有回退; 已完成的9文件汉化不得再开重复改造. 不在本 issue 提前作全仓编号/历史范围结论. 基线 `182ff1846d0ed310b7f4ed308366d36f6e74b412` 到最终目标的全范围搜索,命中分类和历史例外核对由父级全切片集成检查完成.
8. 执行 `uv run pytest workflow/to-spec/tests`. 现有测试中依赖 `review_id`/`--review` 的断言改为新契约. 仅保留或补充能从公开 CLI 持久保护复杂行为的最少测试; 自动化测试仍用真实解析器与隔离文件, 不 mock 内部协作者. 逐个记录收集项和退出码, 不能因全绿略过上列 CLI 实跑.
9. 对本分支改动的 `SKILL.md` 逐个执行 `uv run python general/writing-for-llm/check_skill.py <路径>`. 全仓最终技能清单及全量 `uv run pytest` 留给父级在全部切片集成后统一核对, 不作为本 issue 的局部结果或合并前置.
10. 命令前核实仓库外专用证据根的绝对路径, 避免覆盖旧材料. 不使用真实需求,生产数据或无关用户数据. 运行中无法证明输入或目标并发窗口时, 相关结果记未验证.

## 交付证据
- 执行后填写本分支实际改动路径与提交号,候选条文逐条映射,合成文件清单,CLI 命令/输出/退出码,输入和生成文件的可复查位置及摘要,原子替换/并发时序原件,本分支测试清单及结果,本分支 skill 格式检查结果. 对全仓审计只记录父级待办引用,不提前填全范围结论.
- 原始材料脱敏后仍须足以核对. 通过方案指定的证据根把原件和索引持久化到正式产物根并推送, 从持久位置重新读取核对; 推送未成功不得报告证据已交付.

### 填写结果 (2026-11-27)

**提交**. 分支 `issue/01`, 评审起点 `775b5a2`.
- `fd26618` `feat: ISSUE-01: 实施盘问确认与机械转正` — 7 文件 (下列全部).
- `8ce78be` `feat: ISSUE-01: 补回 GHERKIN 机检项的固定标记原文` — GHERKIN.md 1 行.
- `3229525` `docs: ISSUE-01: 填写交付证据与验收标准` — 只改本工单文件, 不改产品代码.
- 证据与结论绑定: 代码状态 `8ce78be`; 测试与格式检查在 `3229525` 上重跑 (`run5/logs/final-pytest.*` 39 passed + 39 subtests exit 0, `final-check-skill.*` OK exit 0), 因此结论对 `8ce78be` 与 `3229525` 均成立 (`run5/final-commit.txt` 记录 `git diff 8ce78be 3229525` 仅本工单). 本行之后若还有纯文档提交, 代码与证据结论同样不变; 分支顶端 SHA 见该证据文件. 按派工不推送, 不合并, 不 rebase.

**改动路径**.
`workflow/to-spec/SKILL.md` (流程重写: 盘问确认/写前反方/机械落正式/写后独立检查/预览交付), `TEMPLATES.md` (盘问后落笔说明, 审计证据路径归属), `GHERKIN.md` (编号依据改为盘问确认, AC 不擅自拆分, 确认标记与预览定位), `ac-draft.py` (删 `review_id`/`--review`, preview 页面去掉确认入口与审阅版本), `check-ac.py` (标记文案, 草稿标记检查前置), `tests/test_ac_draft.py`, `tests/test_ac_reading.py` (迁移到公开 CLI, 删 mock 内部协作者用例). 未改 `workflow/grilling` 等既有能力 (仓库内无该目录), 未改 deliberate/decision-ledger/domain-modeling 及 `general/` 下被组合技能 (差异检查见下).

**证据根与索引**. `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-01/`; 总索引 `INDEX.md`; 摘要清单 `manifest.sha256` (1109 行). 轮次: run1 (首次摸底, 发现 AC-024 例7 报错被前置检查抢先), run2 (修复后 CLI 矩阵), run3 (并发取证失败: 解释器路径取错, 子进程 125), run4 (fd26618 全项), **run5 (8ce78be 最终绑定轮, 全部结论依据)**. 旧轮全部保留.

**候选条文逐条映射**. `run5/text-mapping.md`: 产品表 42 行 (AC-001..AC-024, AC-026..AC-030 每个 normal/failure/edge 各一行, 含 AC-024 七例) 逐行给 SKILL.md 行号与原句要点, 结论全部通过; 另含规则 1-15 承接表, 与 grilling/handoff/opposing-viewpoint/decision-ledger/domain-modeling/deliberate 的组合关系核对表, milestone-01 编号复用核对. 缺口与处理见该文件末节: 实施中发现 1 处真缺陷 (草稿标记检查被"只能含一个代码块"抢先, 已前置, run2 起 AC-024 例7 得到预期报错), 1 处随流程必须改的预览文案 (原"待确认/请在 chat 确认/审阅版本"会成为确认入口), 无遗留语义缺口.

**合成文件清单** (`run5/files/`).
- `ac/`: `valid`, `missing-goal`, `audit-rule`, `duplicate-goal`, `keyword`, `multiple-ac`, `free-tag`, `marker` 八个用例目录, 各含 `PRODUCT.base.md` 与 `review/acceptance.md`; `ac/valid/review/2026-11-27-acceptance-*.html` 与实际使用的 `page-nodes.json`.
- `promote/`: `removed-option`, `bad-input` 各含 `before.md` (改动前后原件) 与 `PRODUCT.md`.
- `tech/`: `required.md`, `conditional.md`, 四个 `missing-N.md`, 七个 `typo-N.md`, `order.md`, 复制结果 `TECHNICAL.md`.
- `trace/`: `atomic`, `base`, `draft`, `output` 各含 `PRODUCT.base.md`, `acceptance.md`, `original-output.md`, `PRODUCT.md`; 三例并发改动另存 `input-before.bin`, `external-intended.bin`, `external-after.bin`.
- 全部为合成内容 ("合成清单/合成记录"), 不含真实需求, 生产数据或用户数据.

**CLI 命令/输出/退出码** (原件 `run5/logs/<name>.{cmd,stdout,stderr,exit}`).
- 入口: 全部经 `uv run --with gherkin-official python <脚本>` 或 `uv run python` 的进程入口, 参数先以 `target-help-*` 的 `--help` 核实.
- check-ac: `valid` 0; 七例 `missing-goal` 1 (@G-099 不存在), `audit-rule` 1 (审计条目禁止进 Gherkin), `duplicate-goal` 2 (目标1 重复), `keyword` 1 (关键字不在白名单), `multiple-ac` 1 (每场景恰好一个 AC), `free-tag` 1 (非法标签 @smoke), `marker` 2 (草稿不携带确认标记). 复核见 `target-cli-matrix.stdout`.
- preview: 0, JSON `success=true` 且含 `preview`/`draft`, 无 `review_id`; 页面 2 张展开卡片, 卡片步骤与草稿原文逐字一致, 有原文件链接, 无确认控件/`on*` 属性, 正文含"页面仅供选看, 不用于确认."; 两输入字节未变.
- promote: 无 `--review` 时 0 成功; 带 `--review` 时 2 (`unrecognized arguments: --review`); 坏输入 1 且原正式稿字节不变.
- check-tech: 必备节齐全 0; 条件节全保留 0; 四个必备节逐个缺失 1; 固定节名逐个写错 1; 节序颠倒 1; 与基线 (主仓库 `/home/bolo/Workspace/improve`, 同 775b5a2) 的相同输入 stdout/stderr/exit **逐字节一致** (`base-*` 与 `target-*` 对比在 `probe.py` 内断言, 见 `base-tech-matrix.*`).
- 技术稿: `cp` / `cmp` / 正式 check-tech 均 0 (`target-tech-{copy,compare,formal}`).

**原子替换/并发时序原件**. `run5/logs/trace-*.{cmd,events.jsonl,stdout,stderr,exit}` (环境无 strace/gdb/inotifywait, 用脚本自建的 ptrace 单步控制器, 只跟踪本命令创建的子进程, 不改脚本与内部函数; `uname -sm` 与工具清单见 `run5/environment.txt`).
- `trace-atomic`: 读入两份输入 → 临时文件 fsync → `rename` 进入 (syscall 82) → 返回 0 → 退出 0, 恰一次 rename; 最终内容断言 = 暂存稿其余节原文 + v1 标记 + 草稿全文; 正式机检 0; 两输入字节未变; 无残留 `.tmp`.
- `trace-base`: 在"已读入产品暂存稿"的 close 返回处暂停, 外部 `cp` 改写暂存稿后恢复 → 退出 2, 报"输入在转正过程中已变化", 无 rename, 原正式稿未变.
- `trace-draft`: 同法在"已读入验收草稿"后改写 → 退出 2, 同报错, 无 rename.
- `trace-output`: 等三份文件读完, 在临时文件 fsync 入口暂停, 外部 `cp` 改写正式目标后恢复 → 退出 2, 报"正式文件在转正过程中已变化, 保留当前文件并停止", 无 rename, 保留并发写入内容.
- 三窗口各自命中 (事件流里有暂停点前后纳秒时间戳, 外部 `cp` 的 argv 与退出码), 未互相代替.

**测试**. 绑定最终提交的复跑见 `run5/logs/final-pytest.{cmd,stdout,stderr,exit}` (39 passed + 39 subtests, exit 0) 与 `run5/logs/final-check-skill.*` (OK, exit 0). 全项轮 `run5/logs/pytest.*` (`uv run --with gherkin-official pytest -p no:cacheprovider -v workflow/to-spec/tests`): **39 passed + 39 subtests, exit 0**; 收集清单 `run5/logs/pytest-collect.*`; 依赖 Python 3.11.2, gherkin-official 43.0.0, pytest 9.1.1 (`run5/logs/deps.*`). 相对改动前 42 passed + 37 subtests: 删 6 个用例, 新增 3 个. 删除的是 `test_stale_review_*`, `test_promote_requires_review_*` (依赖已移除的 review_id/--review 契约) 与 4 个用 `unittest.mock.patch` 替换内部协作者 (`os.replace`/`os.fsync`/`validate_product`) 的用例; 后者的保护目标改由真实外部进程时序 (`trace-*`) 与真实 CLI 用例承担. 新增 `test_promote_rejects_removed_review_option`, `test_promote_rejects_invalid_draft_without_altering_existing_output`, `test_promote_refuses_directory_target_without_leaving_temporary_file`; 预览测试全部改为经 CLI 进程运行, 断言"页面仅供选看"与无审阅版本.

**skill 格式检查**. `run5/logs/check-skill.*`: `uv run python general/writing-for-llm/check_skill.py workflow/to-spec/SKILL.md` → `workflow/to-spec/SKILL.md: OK`, exit 0. 本分支只改这一个 SKILL.md; 全仓最终清单留给父级.

**范围与依赖核对**. `run5/logs/changed-files.*` (775b5a2→8ce78be 仅 7 文件, 均在允许范围内, 无规格/账本/路线图/历史快照改动); `run5/logs/capability-files.*` (对 deliberate/decision-ledger/domain-modeling/grilling/handoff/opposing-viewpoint/present 的 `git diff --exit-code` 无差异, exit 0); `run5/logs/scope-search.*` (规则9 问题数上限: 0 命中; 规则10: 无新增记录格式; review_id/--review 仅余测试中的"不存在"断言); `run5/logs/diff-check.*` (无空白错误).

**未验证项**.
1. 全量 `uv run pytest` (需 Podman 与完整依赖): 本容器 podman 缺失, 按派工不执行也不修环境 → **未验证**, 交父级集成检查.
2. 真实浏览器渲染/截图: 环境无 chromium; 以真实 HTML 的节点解析记录 (`page-nodes.json`) 与 present handler 的 loopback 读取测试代替 → 页面视觉呈现 **未验证** (方案允许 DOM 可核对记录, 不影响"卡片与原文"结论).
3. 真实 present 常驻服务挂载预览: 为避免占用共享端口未挂载 → **未验证**; 只证明页面与原文件可经 present handler 读取.
4. 真实需求试跑: 非目标, 不做.
5. 基线 `182ff18` 到最终目标的 `workflow/`+`general/` 全范围旧编号搜索与历史例外分类: 父级待办.
6. 证据推送: 按派工不推送; 原件在仓库外证据根 (与宿主同路径, 可复查), 随父级集成提交时再持久化.

**父级集成待办引用**. 全量 pytest (带 Podman); 全仓变更 SKILL.md 清单与 `check_skill.py` 全量; 基线到最终目标的编号/历史范围审计与 `REVIEW-milestone-01.md` 对照; 三个 issue 合并后的跨文件集成核对 (to-spec/verify-change/navigate/README); 安装目录实施后只读摘要.

## 风险提示
- `ac-draft.py` 现有测试含 review_id 与 `--review` 断言, 迁移时逐项确认保护仍覆盖新契约, 不因删除旧参数而丢掉目标和输入变化保护.
- 原子替换与三个并发变化窗口需要外部进程控制. 无可靠时序证据时不得把重复运行或内部函数测试算通过.
- check-tech 的既有退出码以相同基线输入/环境为准; 发现规范和基线冲突须停止对应判断.

## 停止条件
同全局; 若要改产品判据,marker 版本,CLI 输入输出以外的已确认接口,增加服务/依赖或扩大文件范围, 停止并交回确认. 运行环境或并发工具未就绪时保留可做部分并将对应项标未验证, 不降低标准.

## 验收标准
- [x] 验收1-24及验收26-30的全部来源场景和失败/边界分支均有候选条文或公开入口证据; AC-024七例逐个达到已确认预期. (`run5/text-mapping.md` 42 行 + `run5/logs/target-ac-*`)
- [x] 规则1-15中本 issue 承接的部分及本分支技术接口,错误模式,安全要求有对应检查和可复查材料. 规则11/12的全范围审计由父级集成检查完成. (`text-mapping.md` 规则表; `capability-files.*`; `scope-search.*`; trace/pytest)
- [x] review_id/--review 已从公开契约移除且无兼容; 标记固定 v1; 原文,原子替换,输入变化和目标变化保护均按真实入口验证. (`target-promote-removed-option.*`; `trace-{atomic,base,draft,output}.*`)
- [x] 本 issue 的改动复用 milestone-01 编号结果并核对对应既有行为, 没有重复汉化任务. 全仓编号/历史范围审计作为父级集成检查的待办明确交接, 本 issue 不提前宣称全范围通过. (`text-mapping.md` 第 4 节)
- [x] 本 issue 改动的既有测试与新增必要测试通过, `workflow/to-spec/tests` 和所有适用的 skill 格式检查留完整记录. (`pytest.*` 39 passed + 39 subtests exit 0; `check-skill.*` OK exit 0)
- [x] 验证方法受环境阻塞的项明确记为未验证, 不报告通过. (交付证据"未验证项" 1-3: 全量 pytest, 真实浏览器渲染, present 常驻挂载)

## 被阻塞于
- 无
