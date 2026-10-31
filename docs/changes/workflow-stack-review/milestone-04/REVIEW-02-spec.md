# milestone-04 Spec 轴评审 (REVIEW-02)

- 审核者: spec01, 未参与本轮实现与修复的独立审核者. 本报告只看 Spec 轴: 实现是否完整落实规格, 有无范围蔓延, 实现方式有无偏差, 交付证据是否覆盖验证契约. 不做代码风格/坏味道判断, 不修代码, 不做验收结论.
- 工作树: `/home/bolo/Workspace/refactor-skill-around-verification.worktrees/review-spec`, 分支 `review/m04-spec`, HEAD `2e0d393`.

## 基准点与 diff

- 基准点: `962e2996593eeedc1d2da335baa813763dd47d30` (EXECUTION.md 评审起点节所记编码前最后状态; 已核实 `git merge-base 962e299 HEAD` 即该提交).
- diff 命令: `git diff 962e299...HEAD` (23 个文件, +498/-117, 含 2 个改名).
- commit 列表 (`git log 962e299..HEAD --oneline`):

```
2e0d393 doc: milestone-04 旧行为影响复查
75d0175 Merge branch 'issue/06' into refactor-skill-around-verification
fcd4e1b doc: 更新路线图 milestone-06, 新增 milestone-10 执行哲学转向
49d512b feat: ISSUE-06: 全套回归与审计纯核验通过, 15 条 AC 复核无差距, TYPE_META.task 计数笔误已复核不涉不变量
b795a8f Merge branch 'issue/04' into refactor-skill-around-verification
b090da6 Merge branch 'issue/03' into refactor-skill-around-verification
bd7b020 doc: milestone-06 修订决策与验收标准
69f278d feat: ISSUE-04: 地图页 demo/poc 各自可辨的星球外观与图例, 巡检脚本类型覆盖更新并新增 TC-006
d2fc4d4 feat: ISSUE-03: navigate 类型语汇按 demo/poc 新口径重写
181b3cd Merge branch 'issue/05' into refactor-skill-around-verification
8d4a0b8 Merge branch 'issue/02' into refactor-skill-around-verification
6b67650 Merge branch 'issue/01' into refactor-skill-around-verification
38476f7 feat: ISSUE-02: prototype skill 改名 demo 并按演示语义重写三文件与 README 条目
9e11311 feat: ISSUE-01: 里程碑类型落地 demo/poc, prototype 被拒
e5b0cf6 feat: ISSUE-05: 新增 ADR 0024 记录 demo 改名与 poc 新增类型及旧名处置边界
27b05c0 doc: 更新路线图 milestone-09
336d378 doc: milestone-09 记录评审起点
```

- 簿记提交核对 (按评审说明单列): `bd7b020` 只改 ACCEPTANCE.md 与 milestone-06/DECISIONS.md; `fcd4e1b` 只改路线图 ROADMAP.json. 两者均未触碰 milestone-04 的 PRODUCT/TECHNICAL/EXECUTION/issues 文本. 说明中提到的 `822cbbd`/`a6670e3` 不在本 diff 范围内 (它们是主分支 `refactor-skill-around-verification` 上 75d0175 之后的簿记, 分别改 milestone-06 反方材料与 ROADMAP.json), 同样未触碰 m04 规格文本, 故本报告无与之相关的单列项.

## spec 来源清单

- `docs/changes/workflow-stack-review/milestone-04/PRODUCT.md` (G-001..G-012, BR-001..BR-006, NG-001..NG-004, AC-001..AC-022)
- `docs/changes/workflow-stack-review/milestone-04/TECHNICAL.md` (模块划分/模块接口/接缝与依赖/安全策略/非功能要求)
- `docs/changes/workflow-stack-review/milestone-04/EXECUTION.md` (评审起点, 全局允许/禁止范围, 完成定义, 验证策略, 覆盖矩阵)
- `docs/changes/workflow-stack-review/milestone-04/issues/ISSUE-01..ISSUE-06` (各份 验证契约/验证入口/交付证据)
- 决策只读参考: `../milestone-01/DECISIONS.md` D004/D005/D006/D007/D013; `../milestone-03/DECISIONS.md` D001/D002/D004/D005/D011..D019
- 契约核对依据: `/home/bolo/.agents/skills/verification-contract/SKILL.md`

## 逐条发现

### A-1 (类别 a, 实现缺失): TEMPLATES.md 第 88 行残留 "原型" 一词, TECHNICAL 点名要改的这处未改

- spec 原文: TECHNICAL.md 模块划分 "`workflow/navigate/TEMPLATES.md`: ROADMAP.json 的字段说明, 含 `type` 的合法值一行. 本次只改枚举行**与原型一词**." 以及 PRODUCT.md BR-003 "活跃内容 (skill 正文, 模板, 脚本, 网页, 测试, README) 里不残留 `prototype` 的类型名, 路径约定或分支约定; 已关闭变更的一手材料与记录旧名由来的 ADR 除外. (审计)".
- 位置: `workflow/navigate/TEMPLATES.md:88` "- 里程碑产物 (findings/**原型**/决策文档等) 仍是独立文件, 放 `docs/changes/<feature-slug>/<milestone-NN>/`, 链接记入该里程碑 `artifacts`." 基线 `962e299` 同位置就有这句; 本轮该文件唯一提交 `9e11311` 只改了第 31 行 type 枚举行, 第 88 行未动 (diff 只含 1 行).
- 判定: 这里的 "原型" 是旧 prototype 类型对应的产物类别词 (findings 对 research, 原型 对 prototype, 决策文档 对 deliberate), 类型改名 demo 后它是活跃模板里残留的旧类型语汇. TECHNICAL 把 "原型一词" 与枚举行并列为 TEMPLATES.md 的两处改动, 只落地了一处. 无 AC 直接断言这句 (AC-016 只查枚举行), 但 TECHNICAL 与 BR-003 依据充分.
- 审计链缺口: 该残留未被任何一轮检查发现, 原因是审计词面只有 ASCII. ISSUE-06 BR-003 审计命令是 `grep -rn 'prototype' workflow/ README.md general/ --include=*.md --include=*.py --include=*.html`, 只扫英文; ISSUE-03 证据里的中文反向检查 (`grep -n '原型' workflow/navigate/SKILL.md`) 只查了 navigate/SKILL.md, 未查 TEMPLATES.md. 我复跑 `grep -rn '原型' workflow/ README.md --include=*.md --include=*.py --include=*.html` 确认活跃内容里仅此一处中文残留 (general/present/SKILL.md:45 的 "应用级原型" 是交互设计通用词, 与里程碑类型无关, 不算).

### B-1 (类别 b, 范围蔓延): IMPACT-REVIEW.md 在 diff 内但不在本变更全局允许范围清单里

- 位置: `docs/changes/workflow-stack-review/milestone-04/IMPACT-REVIEW.md` (+149 行), 提交 `2e0d393` (HEAD). 注意它不在说明所列三个簿记提交之列, 属本 diff 评审对象.
- spec 原文: EXECUTION.md 全局允许范围列举 "本目录的 `EXECUTION.md` 与 `issues/`", 未列 IMPACT-REVIEW.md; 全局禁止范围也未点名它.
- 上下文: (1) EXECUTION.md 评审起点节自己写了 "影响复查与双轴评审的自起点都取它", 即规格 anticipating 影响复查产物; (2) 其产出授权来自并行修订的 milestone-06 AC-06-02 修订版 (bd7b020: "IMPACT-REVIEW.md 只在实做轮产出", m04 是实做轮), 属 drive-execution 流程产物, 不是产品行为; (3) ISSUE-06 的 BR-004 审计 ("改动文件全部落在全局允许范围内") 记录于 `49d512b`, 早于 `2e0d393`, 故该审计未覆盖此文件.
- 判定: 有流程授权与规格预热, 定性为流程簿记而非产品行为蔓延, 无需返工; 但按 m04 允许范围的字面枚举它是范围外文件, 且现有 BR-004 证据链没有覆盖它, 记录在案.

### C-1 (类别 c, 实现方式与 issue 文本不符, 实现本身无误): 未知类型回退点的 "两处/期望 2" 是 issue 文本对基线代码的失实描述

- spec 原文: ISSUE-04 要交付第 1 条 "保留未知类型回退 (`TYPE_META[node.m.type] || TYPE_META.task`, 约 1544 与 1903 行两处) 不变"; ISSUE-04 验证入口 "`grep -c 'TYPE_META.task' ... 通过标准: 回退点仍在 (期望 2 处)`"; ISSUE-06 验证入口第 7 步同写 "期望 2 处". TECHNICAL 模块接口的对应不变量是 "未知类型仍回退到 `task` 元数据, 不抛错", 未写数量.
- 实际代码: `TYPE_META[...] || TYPE_META.task` 全页只有一处 (index.html:1555, 画布渲染分派); 另两处 TYPE_META 消费点 (954, 1927) 是 `meta ? label : 原样类型名` 的标签回退, 不含 `TYPE_META.task` 字面量. 基线即如此, 非本轮改动造成.
- 处置: 两处都按偏差如实记录而未凑数 (ISSUE-04 交付证据 "规格偏差 2 条" 第 1 条; ISSUE-06 "两条不变量" 节), 且未为凑 grep 数字去改画布逻辑 (ISSUE-04 禁止范围也禁改). 我的独立核验: `grep -n 'TYPE_META\['` 得 954/1555/1927 三行, render_checks 10/10 通过 (含未知类型无 JS 报错项), TECHNICAL 不变量成立.
- 判定: 实现正确, 是 issue 文本与代码事实不符; 落笔时无法按字面满足, 执行者选择保持行为并记录, 属正确处理, 未触发停止条件. 作为 spec 文本缺陷记录.

### D-1 (类别 d, 没有记录证据): ISSUE-03 契约要求的 "无冒烟" 反向 grep 未出现在交付证据里

- 契约原文: ISSUE-03 验证契约 "给 '无 prototype, 无无处可查, 无冒烟, 无 off_course 用于 poc' 的反向 grep 零命中" (verification-contract 行为变更类要求 "逐项验证本次承诺的全部行为", 反向断言属于承诺的一部分).
- 实际交付证据: ISSUE-03 交付证据与原始输出 `/tmp/m9-04-03/verify.log` 覆盖了 prototype (第 7 条), 无处可查 (第 2 条), off_course (第 4 条), 但四项中的 "无冒烟" 没有任何记录 (verify.log 中 `grep -c 冒烟` 为 0, 即一次都没跑过或没记).
- 复核: 我实跑 `grep -n '冒烟' workflow/navigate/SKILL.md`, 零命中, 事实本身成立. 定性: 没有记录证据, 非检查未通过.

### D-2 (类别 d, 没有记录证据/部分记录): ISSUE-04 提前跑全套节点的 pytest 原始输出未留档

- 契约原文: EXECUTION.md 完成定义 "提前跑全套的两个节点: ... ISSUE-04 完成后跑 render_checks 加完整 pytest (网页与巡检脚本同动)"; 同节 "原始输出与截图放仓库外 `/tmp/m9-04-<NN>/` 并默认保留". verification-contract 共用底线 "保留原始数据. 实跑产生原始数据时, 优先放仓库外并默认保留".
- 实际交付证据: ISSUE-04 交付证据写了 "pytest: `30 passed in 8.00s`, 退出码 0", 但材料目录 `/tmp/m9-04-04/` 只有 render_checks.txt, fixture.png, unknown.png, pixcheck/shot 脚本与 fixture/unknown json, 没有 pytest 原始输出文件; 汇总行仅写在 issue 文本里.
- 缓解: ISSUE-06 随后独立复跑完整 pytest 并留档 `/tmp/m9-04-06/pytest.log` (30 passed), 我本人也复跑得 30 passed, 该节点结论有旁证. 定性: 没有记录证据 (原始输出缺失, 汇总行在场), 低严重度.

## 已检查范围声明

实跑复核 (全部通过): `uv run python -m pytest workflow/navigate/tests` 30 passed (先按完成定义处理了占用 39271 端口的外来守护进程, cmdline 核实为主仓库路径后 kill); `check_skill.py` 对 workflow/demo/SKILL.md 与 workflow/navigate/SKILL.md 均 OK 退出 0; CLI 三例 save demo/poc 退出 0 且 query 读回, save prototype 退出 1 且报 "合法值: research, deliberate, demo, poc, task, acceptance" 顺序与 TYPE_VALUES 一致, 前后 md5 相同; `render_checks.py` 10 项检查 10 项通过 (含 TC-006: 图例两项, 画布标注, 标签色/配色/地貌互不同; (707,447) 点击项在新夹具下仍通过).

逐项读文件核对且无发现的重点: navigate 七处语汇 (research 35/demo 36/poc 37/deliberate 38/task 39 行条目, 完成标准 44-49 行, 收口产物 110 行) 与 AC-007..013/016/020..022 逐句对上, `off_course` 仅在歧路语境, `demos/` 在 navigate 零命中; demo 三文件 frontmatter/适用范围 (SKILL.md:13)/规则 1/5/6/三处清理约定 (SKILL.md:28, LOGIC.md:62, UI.md:85) 与 AC-001/004/010/018/019 对上, `grep -rni poc workflow/demo/` 零命中; LOGIC/UI 路径词面 (LOGIC.md:7, UI.md:17/22/23/31/58/84) 与 AC-004 对上; README.md:54 一行; ADR 0024 三条断言与 AC-014 对上且体例 (标题+一段正文, 无多余章节) 与 0023 一致; index.html TYPE_META 六键顺序与图例六项顺序一致 (research/deliberate/demo/poc/task/acceptance), poc 独立配色地貌与脉冲外观, demo 卫星外观; render_checks TYPES 六值, 夹具 8 枚含 poc, TC-006 覆盖元数据/配色/地貌三组差异; roadmap.py 仅 TYPE_VALUES 一行改动, 报错文案由常量拼出 (`roadmap.py:220-224, 270-273`); demo 三文件里 "用后即焚" (SKILL.md:30 规则 3) 与 issue 清理 grep 的 "用完即焚" 词面不同导致该 grep 零命中是字面巧合, 但规则 3 说的是演示内临时持久化文件而非演示材料清理, 不属 AC-010 三处约定, 判定不违规, 已读原文确认.

证据目录核对: /tmp/m9-04-01 (16 个文件, 基线/AC002/003/005/旧图不变量/停服务+pytest 与交付证据所述一致), /tmp/m9-04-02 (before/after 四件套, 9 行基线命中与所述一致), /tmp/m9-04-03 (verify.log, 缺 D-1 所述冒烟项), /tmp/m9-04-04 (缺 D-2 所述 pytest 原始输出), /tmp/m9-04-06 (pytest.log, render_checks.log, 截图与 unknown 核验脚本在场). /tmp/m9-04-05 不存在, 与六份 issue 的编号口径一致 (无 ISSUE-05 材料目录, 其验证入口也不要求). EXECUTION 完成定义的两个提前跑全套节点: 节点 1 (ISSUE-01 后完整 pytest) 有 /tmp/m9-04-01/pytest-and-stop.txt 在场; 节点 2 (ISSUE-04 后 render_checks+pytest) render_checks 有留档, pytest 原始输出缺 (见 D-2), 两节点均有执行记录而非未执行.

范围外文件核对: diff 中五个实施提交的改动逐文件对照 EXECUTION 允许范围全部落界; ROADMAP.json/ACCEPTANCE.md/milestone-06 DECISIONS.md 的改动全部来自簿记提交 (bd7b020, fcd4e1b, 27b05c0, 336d378), IMPACT-REVIEW.md 见 B-1. BR-004 相关事实复核: `git status --short` 干净, `ls ~/.agents/skills | grep -xE 'demo|prototype'` 只出 prototype, docs/changes 下无删除, `docs/changes/less-is-more-palette/prototypes/` 在场, 本地与远端均无 `prototype/*` 分支.

## 发现总数

共 5 条: (a) 缺失/不完整实现 1 条 (A-1), (b) 范围蔓延 1 条 (B-1), (c) 实现方式与 issue 文本不符 1 条 (C-1, 实现本身正确), (d) 证据类 2 条 (D-1, D-2, 均为没有记录证据, 无检查未通过). 最严重: A-1, TEMPLATES.md:88 残留旧类型语汇 "原型", 是 TECHNICAL 点名的两处 TEMPLATES 改动中未落地的一处, 也是唯一需要改产品内容才能消除的发现.
