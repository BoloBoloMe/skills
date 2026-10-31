## 父级
- `../EXECUTION.md`
## 执行
- [x] 已完成
## 要核验什么
五个实施 issue 拼起来后, 本变更对外的承诺是否成立, 且没有越界:
- 全套回归与文档机检: AC-015, AC-017, TECHNICAL 非功能要求的回归检查与文档机检.
- 三条审计: BR-003 (活跃内容不残留 prototype 类型名, 路径约定, 分支约定), BR-004 (没改已安装 skills 与全局配置, 没运行同步, 没宣称安装效果), BR-006 (演示材料与变体分支没被主动清理).
- 抽查两条容易被后续改动破坏的既有不变量: `roadmap.py` 的命令集与写入路径语义未变, 展示页未知类型仍回退 task, 以及 BR-001 的枚举字面量.
- 逐个复核 AC-001 到 AC-014 与 AC-016 的可观察结论, 只记录事实与差距, 不修代码.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-015, AC-017, BR-003, BR-004, BR-006; 复核 AC-001 到 AC-014 与 AC-016.
- Technical: `../TECHNICAL.md`, 非功能要求 (回归检查, 文档机检, 不宣称安装效果), 模块接口 (roadmap.py 命令行不变量, 展示页未知类型回退).
## 相关决策
- `../../milestone-03/DECISIONS.md`: D001 (不留别名, 历史文件原样), D013 (ADR 边界), D019 (不主动清理演示材料与分支).
- `../../milestone-01/DECISIONS.md`: D006 (演示活动不新增产品交付承诺, 不改已安装 skills 的定位).
## 代码定位提示
- 回归入口: `workflow/navigate/tests/`, `workflow/navigate/tests/visual/render_checks.py`.
- 审计对象: `workflow/` (skill 正文, 模板, 脚本, 网页, 测试), `README.md`, `general/`, `docs/changes/`, `docs/adr/0024-*`, `~/.agents/skills/` (只读核对).
- 复核入口: `workflow/navigate/scripts/roadmap.py`, `workflow/navigate/web/index.html`, `workflow/navigate/TEMPLATES.md`, `workflow/demo/`, `workflow/navigate/SKILL.md`.
## 验证入口
```bash
# 0 前置: 展示服务占着默认端口会让三个 lifecycle 用例假红
uv run python workflow/navigate/scripts/web_server.py stop
uv run python workflow/navigate/scripts/web_server.py status        # 期望 alive:false

# 1 AC-015 与 TECHNICAL 回归检查
uv run python -m pytest workflow/navigate/tests
#    通过标准: 退出码 0, 末行显示全部通过, 无 failed

# 2 视觉巡检回归 (环境缺口时降级并写明)
uv run --project general/access-web/browse python workflow/navigate/tests/visual/render_checks.py
#    通过标准: 退出 0, 0 项失败
#    若 playwright/chromium 缺失: 改为人工起页面加截图, 证据里写明缺口, 不写成已跑

# 3 AC-017 与文档机检
uv run python general/writing-for-llm/check_skill.py workflow/demo/SKILL.md
uv run python general/writing-for-llm/check_skill.py workflow/navigate/SKILL.md
#    通过标准: 两次都输出 OK 且退出 0

# 4 BR-003 审计 (活跃内容)
grep -rn 'prototype' workflow/ README.md general/ --include=*.md --include=*.py --include=*.html
#    通过标准: 零命中
grep -rln 'prototype' docs/
#    通过标准: 命中项逐条分类为允许例外后写入证据: docs/changes/ 下的历史一手材料与决策记录,
#    以及 docs/adr/0024-demo-poc-milestone-types.md (记录旧名由来); 活跃内容里不得出现

# 5 BR-004 审计
git status --short
git diff --stat
#    通过标准: 改动文件全部落在 EXECUTION.md 的全局允许范围内; 未改 PRODUCT/TECHNICAL/DECISIONS,
#    未改 docs/changes 历史材料, 未改已安装 skills
ls ~/.agents/skills | grep -x -E 'demo|prototype'
#    通过标准: 只列 prototype (证明没安装/没同步), 没有 demo
#    另核对: 本次会话没有任何 sync-to-pi.py 调用记录; 完成证据不含安装效果或模型行为结论

# 6 BR-006 审计
git diff --stat docs/changes
git status --short docs/changes
ls docs/changes/less-is-more-palette/prototypes/
git branch --list 'prototype/*'
#    通过标准: docs/changes 无删除项, 历史 prototypes 目录内容仍在, 旧分支列表与改动前一致

# 7 BR-001 与两条不变量抽查
grep -n 'TYPE_VALUES' workflow/navigate/scripts/roadmap.py
mkdir -p /tmp/m9-04-06
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-06/r.json milestones.milestone-01 '{"title":"夹具","type":"task","question":"q"}'
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-06/r.json milestones.milestone-01.type prototype
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-06/r.json milestones.milestone-01.type poc
uv run python workflow/navigate/scripts/roadmap.py query docs/changes/workflow-stack-review/roadmap/ROADMAP.json milestones.milestone-04.type
#    通过标准: 常量为六值; prototype 退出 1 且报完整合法值; poc 退出 0; 现网 ROADMAP.json 仍可读
grep -c 'TYPE_META.task' workflow/navigate/web/index.html    # 通过标准: 回退点仍在 (2 处)

# 8 逐条复核 AC-001 到 AC-014 与 AC-016
#    对每条 AC 的断言读文件或跑命令, 记录结论与差距; 参考 EXECUTION.md 覆盖矩阵里的验证入口
```
## 完成证据
执行者: ex06, 纯核验, 未改任何源码/文档正文 (除本节与勾选); 原始输出与截图在 `/tmp/m9-04-06/`.

### 回归与文档机检 (AC-015, AC-017, TECHNICAL 非功能)
- 验证入口 0: `web_server.py stop` 后 `status` 返回 `alive:false` (开跑前与收工后各确认一次).
- pytest `uv run python -m pytest workflow/navigate/tests`: 退出码 0, 末行 `30 passed in 8.00s`, 无 failed (基线 27 + ISSUE-01 三条新用例).
- render_checks `uv run --project general/access-web/browse python workflow/navigate/tests/visual/render_checks.py`: 退出码 0, `10 项检查, 10 项通过, 0 项失败`; 含 TC-006 (`PASS demo/poc 类型展示`: 图例两项, 画布标注 demo=True/poc=True, 标签色 #e8955c/#63c9a3, 配色与地貌均不同).
- check_skill.py: `workflow/demo/SKILL.md: OK` 与 `workflow/navigate/SKILL.md: OK`, 两次退出码均 0.

### 审计
- BR-003: 活跃内容 grep (`grep -rn 'prototype' workflow/ README.md general/ --include=*.md --include=*.py --include=*.html`) 命中 7 行, 真残留 0, 逐条分类: `render_checks.py` 176/196/254 三处为 JS 内建属性 `CanvasRenderingContext2D.prototype` (给 `fillText` 打桩采样), 与类型名无关, 允许例外; `test_roadmap_validation.py` 189/190/194/198 四处是 TC-003 反向用例自身 (断言 `prototype` 被拒且合法值清单不含它), 是 AC-003 要求的拒绝测试, 不是把旧名当类型/路径/分支约定使用, 允许例外. docs/ 侧 `grep -rln 'prototype' docs/` 命中 162 文件: 161 个在 `docs/changes/` (历史一手材料, 决策记录, 评审证据), 1 个 `docs/adr/0024-demo-poc-milestone-types.md` (记录旧名由来), 逐条核过无例外区外命中, 全部允许例外.
- BR-004: `git status --short` 干净; 五个实施提交 (9e11311/38476f7/d2fc4d4/69f278d/e5b0cf6) 改动全部落在 EXECUTION 全局允许范围; 另见 27b05c0 与 336d378 (drive-execution 的路线图状态流转与评审起点记录) 和 bd7b020 (milestone-06 修订), 属编排流程, 不属五个实施 issue; 未改 PRODUCT/TECHNICAL/DECISIONS 正文, 未改 docs/changes 历史材料. `ls ~/.agents/skills | grep -x -E 'demo|prototype'` 只输出 `prototype`, 无 demo. 本会话无 `sync-to-pi.py` 调用. 本证据只含仓库内观察, 无安装效果或模型行为结论.
- BR-006: `git diff --name-status 962e2996..HEAD -- docs/changes` 无 D (零删除); `docs/changes/less-is-more-palette/prototypes/palette/prototype.palette.html` 原样在; `git branch --list 'prototype/*'` 本地与 `git ls-remote origin 'refs/heads/prototype/*'` 均为空, 本次变更无任何分支删除操作记录, 分支列表与改动前一致.
- BR-001 抽查: `TYPE_VALUES` 单行六值 (roadmap.py:35); `git diff 962e2996..HEAD -- roadmap.py` 只动该常量一行; `save ... type prototype` 退出 1 且报 `合法值: research, deliberate, demo, poc, task, acceptance`; `save ... type demo` 与 `... type poc` 均退出 0, `query` 分别得 demo/poc; prototype 被拒后文件 md5 逐字节不变 (3ec09de6).

### 两条不变量
- roadmap.py 命令集与写入路径: diff 仅 TYPE_VALUES 一行, query/save/delete 三命令均在; 现网 ROADMAP.json `query milestones.milestone-04.type` 成功得 task 且前后 md5 相同 (a0fd4c7d, query 不写文件); `/tmp` 副本 `save notes.0` 往返成功; 写入路径仍只认 `milestones.<id>.<field>`.
- 展示页未知类型回退: `grep -c 'TYPE_META.task'` 实测 1, 与本 issue 验证入口写的 2 不符, 差异已复核且不影响不变量: 唯一元数据回退点是 index.html:1555 `TYPE_META[node.m.type] || TYPE_META.task` (画布渲染分派), 未知类型星球按 task 外观渲染; 另两处 (955, 1929) 是 `meta ? label : 原样类型名` 的标签回退, 不含 `TYPE_META.task` 字面量, 未知类型显示原始类型名字符串, 同样不抛错. 实测佐证: 用 type=mystery 夹具起页面, pageerror 0 条, 页面正常渲染 (截图 `/tmp/m9-04-06/unknown-type-page.png`).

### AC 复核表 (AC-001..AC-014, AC-016; AC-015 见回归节)
15 条全部通过, 0 差距, 0 无法核验. 逐条: AC-001 (ls workflow/demo/ 三文件在, frontmatter `name: demo` 且 description 写演示用途, 无 workflow/prototype/); AC-002 (save demo 退出 0, query 得 demo); AC-003 (save prototype 退出 1, 报错合法值清单恰为六值不含 prototype, 文件 md5 不变); AC-004 (LOGIC.md:7 demos/ 目录, UI.md:17/23/31 demo. 前缀与 demo/ 子目录, UI.md:58 /demo/<name> 路由, UI.md:84 demo/<feature-slug> 分支, UI.md:10/28 判定顺序 A 先, 无邻近宿主才 B, 无前端降级 C); AC-005 (save poc 退出 0, query 得 poc); AC-006 (TC-006 程序证据: 图例含演示 demo 与实验 PoC, 画布标注两者, 标签色/配色/地貌互不相同; 另存夹具截图 /tmp/m9-04-06/demopoc-page.png 供人工查看, 本核验会话无读图能力, 以 TC-006 为准); AC-007 (SKILL.md:37 poc 标 AFK 且写独立驱动, :47 完成标准节 poc 行, :110 收口产物 poc 写本里程碑结论与依据); AC-008 (SKILL.md:36 demo 何时创建含样子/如何运行/看清过程, 成品或线上系统演示归 demo 且不新增交付承诺); AC-009 (SKILL.md:46 完成标准 `我看过并能据此判断`, :110 成品演示关闭摘要记一行且产物可为空, `grep demos/` 零命中无强制留档); AC-010 (三文件各写可保留回看, 代理不主动删除, 仓库主人点名删除, SKILL.md:28/LOGIC.md:62/UI.md:82+85, 旧句 `合并主干前由人类清理|用完即删|用完即焚` 零命中, LOGIC.md 第 5 步原句已换); AC-011 (SKILL.md:37 poc 条目恰含四部分, 交付定义指针指向 software-engineering-consensus 的 PoC 词条, 无复述); AC-012 (SKILL.md:35 research 只留藏在当前工作目录之外的事实, `无处可查|须先做实验测出` 零命中); AC-013 (SKILL.md:39 task 含需要实测但结论是描述现状归 task 及压测/性能基线例); AC-014 (docs/adr/0024 写明 demo 取代 prototype, poc 新增, 旧分支与 prototypes/ 目录按历史证据原样保留不做读取兼容); AC-016 (README.md:54 demo 行指向 workflow/demo/SKILL.md 且用途写演示, TEMPLATES.md:31 枚举行六值, SKILL.md:38 deliberate 写无法靠演示提升保真度且全文件 prototype 零命中).

### 缺口
无阻塞性缺口. 两处记录与实测不符的差异均不影响验收: 验证入口 7 的 `TYPE_META.task` 计数 (2 处 -> 实为 1 处, 见不变量节, 属 issue 笔误, 判定不变量仍成立); AC-006 的 `一眼能分开` 人工判读由 TC-006 程序化断言加存档截图替代 (本会话无读图能力, 已写明).

## 风险提示
- 展示服务占用默认端口造成 lifecycle 用例假红, 必须先 stop 并 status 确认.
- 审计 grep 会命中历史材料与 ADR, 一律判失败就误报; 要按 BR-003 的范围与例外逐条分类.
- `~/.agents/skills` 是宿主只读挂载, 只做只读核对, 不改不装.
## 停止条件
需要改变任一 Spec, 决策或核验范围时停止; 发现需要修代码才能通过时不在本 issue 修, 报告并交回对应实施 issue.
## 适合 AFK 的原因
全部动作是跑命令与读文件, 判据已由 AC 与审计口径定死, 不需要新的产品/API/架构决策; 唯一判断是审计命中的分类, 分类规则本身写在 BR-003 里.
## 验收标准
- [x] pytest 全绿, render_checks 0 项失败 (或按环境缺口降级并写明).
- [x] 两份改过的 SKILL.md 通过 check_skill.py.
- [x] BR-003 活跃内容零 `prototype` 残留, 例外逐条分类留证.
- [x] BR-004 改动不越界, 已安装 skills 与全局配置未动, 无同步调用, 无安装效果结论.
- [x] BR-006 历史演示材料与旧分支未被动过.
- [x] AC-001 到 AC-014 与 AC-016 逐条有结论, 未通过与差距都写明.
## 被阻塞于
- `ISSUE-01-milestone-type-enum.md`
- `ISSUE-02-demo-skill-rename-rewrite.md`
- `ISSUE-03-navigate-type-vocabulary.md`
- `ISSUE-04-web-demo-poc-visuals.md`
- `ISSUE-05-adr-naming-record.md`
