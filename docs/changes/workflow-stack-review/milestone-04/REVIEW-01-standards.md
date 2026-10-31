# milestone-04 Standards 轴评审 (REVIEW-01)

- 审核者: std01, 未参与本轮实现与修复的独立审核者. 只审 Standards 轴 (是否遵循仓库已记录规范 + Fowler 坏味道基线), 不做 Spec 轴判断, 不修代码.
- 目标: `git diff 962e299...HEAD`, HEAD `2e0d393`.

## 1. 基准点与 diff 命令

- diff 命令: `git diff 962e2996593eeedc1d2da335baa813763dd47d30...HEAD` (三点语法, 与 EXECUTION.md 评审起点一致).
- commit 列表: `git log 962e299..HEAD --oneline`

```
2e0d393 doc: milestone-04 旧行为影响复查                       (影响复查簿记, drive-execution 强制产物)
75d0175 Merge branch 'issue/06' into refactor-skill-around-verification
fcd4e1b doc: 更新路线图 milestone-06, 新增 milestone-10 执行哲学转向   (非本轮, 航行簿记)
49d512b feat: ISSUE-06: 全套回归与审计纯核验通过...
b795a8f Merge branch 'issue/04' ...
b090da6 Merge branch 'issue/03' ...
bd7b020 doc: milestone-06 修订决策与验收标准                    (非本轮, milestone-06 决策账)
69f278d feat: ISSUE-04: 地图页 demo/poc 各自可辨的星球外观与图例...
d2fc4d4 feat: ISSUE-03: navigate 类型语汇按 demo/poc 新口径重写
181b3cd Merge branch 'issue/05' ...
8d4a0b8 Merge branch 'issue/02' ...
6b67650 Merge branch 'issue/01' ...
38476f7 feat: ISSUE-02: prototype skill 改名 demo...
9e11311 feat: ISSUE-01: 里程碑 type 枚举落地 demo/poc...
e5b0cf6 feat: ISSUE-05: 新增 ADR 0024...
27b05c0 doc: 更新路线图 milestone-09                           (非本轮, 航行簿记)
336d378 doc: milestone-09 记录评审起点                         (非本轮, 本目录簿记)
```

非本轮提交 (27b05c0/336d378/bd7b020/fcd4e1b) 的体例也已过目, 未发现违反规范处 (见第 6 节).

## 2. 规范来源清单

1. `AGENTS.md` — 只能改本仓库, 禁止修改真实安装的 skills.
2. `README.md` — 技能表体例, 调用关系口径.
3. `pytest.ini` — testpaths 顺序: 各树 conftest 同名, tests/ 必须最后; 其他树禁止显式 `from conftest import`.
4. `docs/changes/workflow-stack-review/milestone-04/TECHNICAL.md` — 模块划分/模块接口/非功能要求.
5. `docs/changes/workflow-stack-review/milestone-04/EXECUTION.md` — 允许/禁止范围, 完成定义.
6. `docs/changes/workflow-stack-review/milestone-04/PRODUCT.md` — BR-003 (残留审计), BR-005 (单点维护) 等已记录规则.
7. `docs/adr/` 既有体例 (0023/0022/0004/0003 作样板).
8. `general/writing-for-llm/SKILL.md` — 单一真相源/重复/冗余枚举/相关性 (check_skill.py 只机检 frontmatter, 正文规则靠评审).
9. `workflow/drive-execution/SKILL.md` — IMPACT-REVIEW.md 落位与提交信息格式 (`feat: ISSUE-<NN>: <描述>`).
10. `workflow/decision-ledger/SKILL.md` — 决策账条目与 已替代 (→ D00X) 格式.
11. Fowler 坏味道基线全文 (`~/.agents/skills/code-review/references/fowler-baseline.md`, 已读).

## 3. 工具链已覆盖项 (不重复报)

- `general/writing-for-llm/check_skill.py`: SKILL.md frontmatter 硬约束 (name kebab-case/目录一致, description 单行, 冒号禁令). 两份改动 SKILL.md 已过机检.
- pytest 套件 (含新用例的运行结果): 工具强制, 只审写法不审绿红.
- `visual/render_checks.py` 的运行结果: 巡检脚本本体不属 pytest 收集, 但其运行绿红不属 Standards 轴.

## 4. 规范来源冲突与优先级判定 (可解, 未触发停止条件)

- (a) TECHNICAL.md 模块边界写 "其余文件不动", EXECUTION.md 允许范围只列 "本目录的 EXECUTION.md 与 issues/", 而本轮新增了 `milestone-04/IMPACT-REVIEW.md`. 判定: `workflow/drive-execution/SKILL.md:36` 明文要求把影响复查报告 "写入产物根目录的 IMPACT-REVIEW.md 并提交", 属更高层已记录流程规范, 且 IMPACT-REVIEW.md 由指定审核者在实施提交之后独立产出. 按流程规范优先, 该文件不算越界; TECHNICAL 边界句按实现模块口径读. 记录在此, 供总指挥知悉 (EXECUTION 允许范围清单未预列该产物, 属输入侧遗漏).
- (b) writing-for-llm "单一真相源/重复" 禁令 vs ISSUE-03 AC-007/AC-010/AC-011 强制在 navigate/SKILL.md 的多处与 demo 三文件重复同一约定. 判定: 已确认的具体 spec 优先于一般写作规范, 相关发现降级为判断性 (S-03), 不作硬性.

## 5. 逐条发现

硬性违规 0 条, 判断性发现 13 条 (S-01..S-13). 每条均已读取 hunk 所在完整函数/章节及必要调用方.

### S-01 TEMPLATES.md 残留旧类型中文标签 "原型" — 判断性 (偏硬, 建议优先处理)

- 位置: `workflow/navigate/TEMPLATES.md:88` (本 diff 未触碰该行).
- Hunk: 本轮 TEMPLATES.md 只改了枚举行 (`@@ -28,7 +28,7 @@`), 第 88 行 "里程碑产物 (findings/原型/决策文档等) 仍是独立文件" 原样保留.
- 规范: PRODUCT.md:35 BR-003 — "活跃内容 (skill 正文, 模板, 脚本, 网页, 测试, README) 里不残留 `prototype` 的类型名, 路径约定或分支约定". "原型" 正是旧类型在 `TYPE_META` 里的中文显示名 (prototype: label '原型'), 且新口径下 demo 类产物走 `demos/` 目录, "原型" 作为活的产物种类已失效.
- 判为判断性的原因: BR-003 字面 (反引号限定) 只禁英文 token `prototype`; 但 TECHNICAL.md 模块划分节明文写 TEMPLATES.md "本次只改枚举行与原型一词", 说明规格自身把 TEMPLATES 的 "原型" 一词划入了应改范围, 而实际未改. 字面不 coverage, 意图 coverage, 两读法并存.
- 上下文依据: 已读 TEMPLATES.md 全文与基线版 (`git show 962e299:...`), 确认第 88 行为全文件唯一 "原型" 残留且改动前就存在; 已读 m04 的 BR-003 审计证据 (ISSUE-06): 其 grep 只查英文 token, ISSUE-03 的中文 grep 只覆盖 navigate/SKILL.md, 该残留落在两轮审计的盲区.
- 交叉提示: TECHNICAL 声称的 "改原型一词" 与实际 diff 不符, 属 Spec 轴核对事项, 此处只记录事实不作 spec 判定.

### S-02 navigate/SKILL.md 两个并列清单的类型顺序不一致 — 判断性

- 位置: `workflow/navigate/SKILL.md:35-40` (种类清单) 对 `:44-49` (完成标准清单).
- Hunk: `@@ -32,17 +32,19 @@`.
- 问题: 种类清单顺序为 research, demo, poc, deliberate, task, acceptance; 而完成标准清单, TEMPLATES.md:31 枚举行与 roadmap.py `TYPE_VALUES` 均为 research, deliberate, demo, poc, task, acceptance. 同一节内两份按类型展开的清单顺序分叉, 后续维护按枚举顺序对表时会错位.
- 规范: 无成文规则, 属一致性判断 (Fowler 视角可读作轻度的 Duplicated Code 维护代价). 注: 旧文种类清单本就不按 TYPE_VALUES 顺序 (prototype 在 deliberate 前), 本轮沿用并加深了分叉.
- 上下文依据: 已读 SKILL.md 种类/完成标准两节全文并核对 TEMPLATES.md:31 与 roadmap.py:35.

### S-03 poc 的完成标准/收口产物同一意义在文内出现四处 — 判断性 (spec 强制形态, 抑制为判断性)

- 位置: `workflow/navigate/SKILL.md:37` (条目内 **完成标准** 与 **收口产物** 两段近重复), `:47` (完成标准节 poc 行), `:110` (航行 step 4 收口产物).
- Hunk: `@@ -32,17 +32,19 @@` 与 `@@ -105,7 +107,7 @@`.
- 规范: writing-for-llm 剪枝节 "让每个意义住在单一真相源... 重复, 即同一个意义出现在多处"; 条目内 37 行 "结论与依据已写进本里程碑自己的产物" 与 "poc 的产物是它自己里程碑里的结论与依据" 两句同义相邻.
- 抑制说明: ISSUE-03 AC-011 强制 poc 条目恰含四部分 (含完成标准/收口产物), AC-007 强制完成标准节有 poc 行且收口产物节提及 poc. spec 强制的多处成文覆盖一般写作规范 (见第 4 节 (b)), 故不作硬性. 条目内部两段的同义重复不在 AC 字面强制内, 仍是可收敛点.
- 上下文依据: 已读 SKILL.md 全文, ISSUE-03 的 AC-007/AC-011 原文, EXECUTION.md 覆盖矩阵对应行.

### S-04 poc 条目引用变更 scoped 规则号 "(BR-005)" 无解析路径 — 判断性

- 位置: `workflow/navigate/SKILL.md:37` 句末 "(BR-005)".
- Hunk: `@@ -32,17 +32,19 @@`.
- 问题: BR-005 定义在 `docs/changes/workflow-stack-review/milestone-04/PRODUCT.md:37`, 是本轮变更的 scoped 规则号. navigate/SKILL.md 是长期存活的 skill 正文, 引用一个不随文件走的变更内编号, 变更归档后读者无从解析; 同一句里另一个指针 (software-engineering-consensus 的 PoC 词条) 给了完整路径, 同句双标, 参照系不一.
- 规范: writing-for-llm 上下文指针 (指针须让材料可抵达) 与相关性/沉积 (过期引用层沉降); 判断性, 非硬性 (无成文禁令).
- 上下文依据: 已读 SKILL.md poc 条目全文, PRODUCT.md:37, 及同类先例 (`workflow/use-sandbox-worktree/scripts/swt.py` 内的 BR 引用均带本变更语境).

### S-05 README 技能表的字母序被改名打破 — 判断性

- 位置: `README.md:54`.
- Hunk: `@@ -51,7 +51,7 @@` (原 prototype 行原位改写为 demo).
- 问题: 工作流技能表在基线是严格按 skill 名字母序排列的 (已逐行核对基线 962e299 与现行 通用技能表), `prototype` 恰好落在 navigate 与 software-engineering-consensus 之间维持了有序; 改名 `demo` 后原位保留, 破坏有序 (demo 应位于 deliberate 之后). 表无成文排序规则, 故判断性; 但两表其余 36 行均有序, 单行破序可读性损失真实存在.
- 上下文依据: 已读 README.md 全表, 基线版对照.

### S-06 图例 poc 项副标注 "PoC" 偏离 "小字 = 类型键" 既有模式 — 判断性

- 位置: `workflow/navigate/web/index.html:199` (`<span>实验 <small>PoC</small></span>`).
- Hunk: `@@ -188,7 +188,15 @@`.
- 问题: 其余五类图例的 `<small>` 均为原样类型键 (research/demo/task/acceptance 及基线 prototype), poc 写作 "PoC" (大小写修饰), 模式破缺; 连带 render_checks TC-006 只能硬编码字符串 "实验 PoC" (render_checks.py:211), 两处耦合同一非常规拼写.
- 规范: 无成文规则, 一致性判断; 类型键是 `poc` (TYPE_META 键与 TEMPLATES 枚举均小写).
- 上下文依据: 已读图例整块 (index.html:172-214), TYPE_META (:265), TC-006 断言 (:211).

### S-07 测试文件 TC 编号碰撞且模块 docstring 未更新 — 判断性

- 位置: `workflow/navigate/tests/test_roadmap_validation.py:1` (模块 docstring), `:61`/`:74` (既有 TC-002/TC-003 docstring) 对 `:181`/`:190`/`:203` (新增 TC-002/TC-003/TC-005 docstring).
- Hunk: `@@ -166,3 +166,43 @@`.
- 问题: 文件头 docstring 仍只列旧变更 ISSUE-02 的 TC-002/003/004/104/105, 未把本轮 m04 的三条用例纳入; 且新用例复用 TC-002/TC-003 编号但含义不同 (旧 TC-002=非法枚举被拒, 新 TC-002=demo 可写入), 同文件同名编号两义. 新 docstring 加了 "(m04 AC-xxx)" 消歧是好的, 但裸编号与文件头清单均已失真, m04 文档 (EXECUTION.md 验证策略) 里 "TC-002" 指新义, 读旧 docstring 会拿错对象.
- 坏味道: Mysterious Name + 文档沉积. 判断性 (无成文测试命名规范).
- 上下文依据: 已读测试文件全文, 追溯其来源提交 692bdc4 (旧 ISSUE-01/02), 核对 m04 EXECUTION.md 验证策略与 ISSUE-01 的 TC 定义.

### S-08 新增两条 "类型可写入" 用例结构重复, 未用文件既有 parametrize 先例 — 判断性

- 位置: `workflow/navigate/tests/test_roadmap_validation.py:180-188` 与 `:202-207` (test_demo_type_accepted / test_poc_type_accepted).
- Hunk: `@@ -166,3 +166,43 @@`.
- 坏味道: Duplicated Code — 两用例除字面值 demo/poc 外逐行相同; 同文件既有 `@pytest.mark.parametrize` 先例 (test_invalid_enum_rejected, :56-69) 正是同类枚举驱动的参数化写法.
- 抑制说明: EXECUTION.md 验证策略要求 "三条 pytest 用例 (TC-002/TC-003/TC-005)" 一一对应, 参数化为一条会改用例数; 用 parametrize 加 ids 仍可保三条命名, 故报判断性不报违规.
- 上下文依据: 已读测试文件全文及既有参数化用例.

### S-09 `_task_fixture` 下划线前缀与文件既有 helper 命名不一致 — 判断性 (轻微)

- 位置: `workflow/navigate/tests/test_roadmap_validation.py:171`.
- Hunk: `@@ -166,3 +166,43 @@`.
- 问题: 既有模块级 helper (run_cli/legal_doc/write_doc) 均无下划线前缀, 新增私有 helper 取 `_task_fixture`, 同文件两套命名惯例. Python 惯例本身认可前缀, 故仅作一致性判断.
- 上下文依据: 已读测试文件全文.

### S-10 render_checks 的 fillText 打桩样板第三处复制 — 判断性

- 位置: `workflow/navigate/tests/visual/render_checks.py:195-201` (TC-006 桩) 对 `:174-180` (验收类型展示桩) 与 `:255-258` (光照记录桩).
- Hunk: `@@ -188,6 +190,35 @@`.
- 坏味道: Duplicated Code — "劫持 `CanvasRenderingContext2D.prototype.fillText` 收集标注" 的样板第三次出现, 三处仅回调体不同, 可提一个共享打桩 helper (入参: 判定函数或收集器). 注意桩本身写在页面里是既有模式, 本条只针对样板重复度.
- 上下文依据: 已读 render_checks.py 的 run() 全函数, 三处桩均在其内.

### S-11 tests/visual/README.md 覆盖表未随脚本与夹具更新 — 判断性

- 位置: `workflow/navigate/tests/visual/README.md:27-34` (覆盖表) 与 `:29` ("7 个里程碑").
- 对应 hunk: render_checks.py `@@ -27,7 +28,7 @@` (TYPES 六类) 与 `@@ -53,15 +54,16 @@` (small_roadmap 7→8 个里程碑, 新增 TC-006 检查项 `@@ -188,6 +190,35 @@`).
- 问题: README 覆盖表逐项列举 render_checks 的检查, 本轮新增 "demo/poc 类型展示" 一项未入表; 常规视图夹具从 7 个里程碑增至 8 个, 表内 "7 个里程碑的常规视图" 描述同时失真. 注: 表在基线就已缺 "验收类型展示/无 JS 报错" 两行 (沉积非本轮始), 本轮在其上叠加. ISSUE-04 允许范围只含 render_checks.py, 修表需要动范围, 故只报不改.
- 规范: 仓库文档与代码同步的一般一致性要求 (ISSUE-02 风险提示亦载 "改名要连带 README"), 判断性.
- 上下文依据: 已读 README 覆盖表基线与现行, small_roadmap 全函数.

### S-12 新增一个里程碑类型要在 7 处联动, 类型知识分散 — 判断性 (轻度, 既有结构)

- 位置: `workflow/navigate/web/index.html` 五处: TYPE_META `:265` (`@@ -257,7 +265,8 @@`), 图例 `:193-205` (`@@ -188,7 +188,15 @@`), PLANET_PALETTES `:1207` (`@@ -1198,7 +1207,8 @@`), PLANET_FEATURES `:1220` (`@@ -1210,7 +1220,8 @@`), drawStar 分派 `:1650/:1664` (`@@ -1636,7 +1647,7 @@`, `@@ -1650,6 +1661,19 @@`); 另及 roadmap.py:35, TEMPLATES.md:31, render_checks.py:31, 测试夹具.
- 坏味道: Shotgun Surgery — "加一个类型" 这一逻辑变更迫使多文件多处锁定改动; index.html 内 TYPE_META/配色表/地貌表是三张按类型键平行的表, 加图例 SVG 与 drawStar 分支共 5 处, 单一 "类型注册表" 可把元数据/配色/地貌收拢.
- 抑制说明: 平行表是基线既有的仓库结构, 本轮严格沿用且各表相邻 (1207-1230), 校验单点 (TYPE_VALUES) 反而是本轮做对的样板; 故仅作判断性记录, 不建议本轮返工.
- 上下文依据: 已读 index.html 相关区块与 planetStyle (:1272-1273 回退), drawStar 全函数, render_checks TYPES 的全部消费点 (random_roadmap/small_roadmap).

### S-13 drawStar 内 poc 双环描边与 deliberate 双环描边结构相似 — 判断性 (低置信)

- 位置: `workflow/navigate/web/index.html:1664-1674` (poc 新分支) 对 `:1639-1649` (deliberate 既有分支).
- Hunk: `@@ -1650,6 +1661,19 @@`.
- 坏味道: 可能是 Duplicated Code — 两分支同为 "两道同心描边, 外层 alpha 更低" 的环带样板 (ellipse 对 arc, 静对动). 画布绘图里这类样板接近惯用法, 且视觉语义不同 (土星环对脉冲环), 置信低, 仅备案不主张修改.
- 上下文依据: 已读 drawStar 全函数两个分支及调用方 (drawStars 循环).

## 6. 已检查范围声明 (查过且无发现)

- AGENTS.md 硬约束: diff 全部落在仓库内, 无 `~/.agents` 真实 skills 改动, 无 sync 调用痕迹.
- pytest.ini testpaths/conftest 规则: 无新增测试树/conftest, 新用例无 `from conftest import`, tests/ 顺序未动.
- roadmap.py 常量单点化: TYPE_VALUES (:35) 是唯一枚举来源, save 路径 (:220-224) 与整文档校验 (:270-273) 的报错合法值清单均由该常量拼装, 全文件无第二处硬编码枚举 (grep 证); 校验分支未新增 (TECHNICAL "不新增分支" 符合).
- index.html 一致性: TYPE_META 六键与 TEMPLATES/TYPE_VALUES 集合一致; 图例顺序与 TYPE_META 一致; poc 的 TYPE_META 色 #63c9a3 与图例 SVG fill 一致; demo 继承原 prototype 色板/地貌/分派逐字平移; 未知类型回退表达式与空值保护未动.
- demo 三文件与 navigate 用词: "拿已交付的成品或线上系统演示时不调用本 skill, 直接跑成品" 两处口径一致; "可保留回看, 代理不主动删除, 仓库主人点名删除" 三文件口径一致; frontmatter (name: demo, disable-model-invocation) 正确; LOGIC/UI 对 SKILL.md 规则 5 的指称成立; `workflow/` 与 README 下中文 "原型" 仅 TEMPLATES.md:88 一处 (见 S-01), 英文 prototype 残留为零 (BR-003 审计已覆盖, 不重复报).
- ADR 0024 体例: 编号 0024 连续, 标题一行加正文三句, 与 0023/0022/0004/0003 对照, 短正文先例成立 (0004 亦短), 内容覆盖 ISSUE-05 要求的三条.
- 非本轮文档提交: 27b05c0/336d378 (ROADMAP 簿记, 字段合法, 提交信息符合 navigate step 7 规定), bd7b020 (DECISIONS D002/D003 标 已替代 (→ D008) 符合 decision-ledger:23/:51 格式, D007/D008/F011/F012 与邻条同构; ACCEPTANCE 追加段与既有条目同构), fcd4e1b (ROADMAP milestone-10 节字段合法, blocked_by 引用存在). 均无体例违规.
- 提交信息: 五个实施提交均为 `feat: ISSUE-<NN>: <描述>`, 符合 drive-execution:34; 2e0d393 符合 navigate step 4 的 `doc: <milestone-id> <产物简述>` 兜底式.
- IMPACT-REVIEW.md 内容与 drive-execution:36 要求项 (目标提交/逐项发现/已排除项/证据/缺口) 一一对应; 其 "22 个文件/10 个非 merge 提交" 数字经独立复算 (962e299..75d0175) 准确.
- ISSUE 六文件体例: 各节齐全, 勾选与交付证据回填格式一致, 偏差 (规格偏差 2 条, 计数笔误) 均如实留痕.

## 7. 发现总数

- 硬性违规: 0 条.
- 判断性发现: 13 条 (S-01..S-13).
- 最严重: S-01 (TEMPLATES.md:88 "原型" 残留, BR-003 意图覆盖而字面未覆盖, 且落在本轮两轮审计的 grep 盲区; TECHNICAL 明言要改而未改, 已交叉提示 Spec 轴).
