# milestone-04 旧行为影响复查 (IMPACT-REVIEW)

- 审核者: imp01, 未参与本轮任何实现与修复的独立审核者. 本报告是调查记录, 不新增产品判据, 不做产品验收结论.
- 目标提交: `75d017564d9c08552eb4077a719c03f5506ff6c6` (集成提交, Merge branch 'issue/06').
- 评审起点: `962e2996593eeedc1d2da335baa813763dd47d30` (EXECUTION.md 评审起点 节所记 milestone-04 编码起点).
- 调查方法: 按 blast-radius skill 的框架做共享接口深查, 先定关键安全事实, 再给证据分级 (1 直接断言 / 2 指到代码行 / 3 走查路径 / 4 实跑 / 5 应用内复现), 检索空结果写明命令与边界.

## 1. 差异范围核对

### 1.1 范围内改动逐文件核对

`git diff 962e299..HEAD --stat` 共 22 个文件 (含改名 2 个), 其中 10 个非 merge 提交 (`git log --no-merges | wc -l` = 10). 逐文件对照 EXECUTION.md 全局允许范围:

| 文件 | 允许条款 | 实际改动 | 核对 |
| --- | --- | --- | --- |
| `workflow/prototype/` → `workflow/demo/` | demo 目录由 prototype 改名, 可改三文件 | git 识别为改名 (LOGIC.md 相似度 80%, UI.md 67%), SKILL.md 新写 (name: demo, disable-model-invocation: true) | 落在范围 |
| `workflow/navigate/SKILL.md` | 类型语汇 | 种类/完成标准/收口产物三节按 demo/poc 重写 | 落在范围 |
| `workflow/navigate/TEMPLATES.md` | 枚举行 | 仅 `type` 枚举行 1 行 | 落在范围 |
| `workflow/navigate/scripts/roadmap.py` | 只改 TYPE_VALUES 一行 | 仅 `roadmap.py:35` 一行, 命令集 (query/save/delete) 与写入路径语义未动 | 落在范围 |
| `workflow/navigate/web/index.html` | 类型元数据/图例/星球外观分派/配色表 | 图例, TYPE_META, PLANET_PALETTES, PLANET_FEATURES, drawStar 分派, 无其他 | 落在范围 |
| `workflow/navigate/tests/test_roadmap_validation.py` | 只新增枚举用例 | 纯新增 40 行: 夹具 + TC-002/003/005 三用例 | 落在范围 |
| `workflow/navigate/tests/visual/render_checks.py` | 类型清单/夹具/新增巡检项 | TYPES 清单, small_roadmap 夹具, TC-006, `import re` (TC-006 所需) | 落在范围 |
| `README.md` | 工作流技能表 demo 一行 | 仅 1 行 | 落在范围 |
| `docs/adr/0024-demo-poc-milestone-types.md` | 新增 ADR | 新增 3 行 | 落在范围 |
| 本目录 `EXECUTION.md` 与 `issues/` | 本目录簿记与交付证据 | EXECUTION.md 仅 评审起点 行填号 (336d378); issues/ 六文件为交付证据追加 | 落在范围 |

6 个 merge 提交 (6b67650, 8d4a0b8, 181b3cd, b090da6, b795a8f, 75d0175) 无内容改动.

### 1.2 范围之外的改动与非本轮改动归类

差异中落在允许范围之外的文件共 3 个, 全部归类为 非本轮改动 (milestone-04 实施之外的流程簿记与并行会话文档), 依据如下:

1. `docs/changes/workflow-stack-review/ACCEPTANCE.md` (+7/-7) 与 `docs/changes/workflow-stack-review/milestone-06/DECISIONS.md` (+28), 来自提交 `bd7b020` (doc: milestone-06 修订决策与验收标准, 2026-10-31 03:49:46).
   归类依据: 内容全部是 milestone-06 的验收标准修订 (AC-06-02/03 修订版, 新增 AC-06-09) 与决策账 (D002/D003 标 已替代, 新增 D007/D008, 事实 F011/F012); 提交信息自述为 milestone-06; 时间点落在 ISSUE-03 与 ISSUE-04 提交之间, 是并行会话的文档提交; 与 m04 允许范围的任何条款无交集.
2. `docs/changes/workflow-stack-review/roadmap/ROADMAP.json` 中 milestone-09 关闭部分 (status 已关闭, artifacts 12 项, close_summary), 来自提交 `27b05c0` (doc: 更新路线图 milestone-09, 2026-10-30 17:39:53).
   归类依据: 纯 drive-execution 里程碑状态流转簿记; EXECUTION.md 禁止范围明文 "不改 ROADMAP.json 的内容, 里程碑状态流转归 drive-execution"; 该提交发生在评审起点后 14 秒, 早于全部 issue 实施, 是准备节点收尾, 不是本轮实施.
3. `docs/changes/workflow-stack-review/roadmap/ROADMAP.json` 其余部分 (milestone-06 状态流转, milestone-07 问句与 blocked_by 挂 milestone-10, 新增 milestone-10 节), 来自提交 `fcd4e1b` (doc: 更新路线图 milestone-06, 新增 milestone-10 执行哲学转向, 2026-10-31 04:02:07).
   归类依据: 同为 drive-execution 簿记, 内容全部属 milestone-06/10, 提交信息自述清楚.

另: `336d378` (doc: milestone-09 记录评审起点) 只改本目录 EXECUTION.md 的 评审起点 一行, 属本轮簿记, 在允许范围内, 不算越界.

范围核对结论: 本轮六个 issue 的实施改动零越界; 差异中的范围外文件共 3 处, 均已归入 非本轮改动, 不构成对 milestone-04 的越界判定. PRODUCT.md, TECHNICAL.md, `workflow/software-engineering-consensus/`, `web_server.py` 未被任何本轮 issue 提交触碰 (不在 diff 清单).

### 1.3 禁止范围核对

- NG-001 (不留 prototype 别名): `roadmap.py:35` 的 TYPE_VALUES 无 prototype; TC-003 (test_roadmap_validation.py:189) 断言错误文案的合法值部分不含 prototype. 未发现任何别名机制.
- NG-002 (历史一手材料不动): docs/changes 下既有文件零删除 (git diff 无 D 标记); `docs/changes/less-is-more-palette/prototypes/` 目录在场 (内容 palette); 历史 `prototype/<slug>` 分支见 F10.
- NG-003 (不建 poc skill 目录): `ls workflow/` 无 poc 目录.
- NG-004 (不运行同步): 本轮未发现同步调用痕迹; 复核只读确认安装目录状态 (见 F9).
- 不用 off_course 记 PoC 终止 / 不加状态枚举: STATUS_VALUES 未动 (roadmap.py:34), diff 无状态相关行.

## 2. 关键安全事实 (blast-radius 框架)

- KF1: 仓库内全部 ROADMAP.json 都不含 prototype 类型, 且 roadmap.py 对 type 的校验只有 TYPE_VALUES 一个来源 (定义 roadmap.py:35, save 路径校验与报错 220-224, 全文校验与报错 270-273, 报错文案由 `', '.join(TYPE_VALUES)` 动态拼装). 所以枚举改名对既有数据的读取/校验/写入零影响, 报错文案自动跟随新枚举, 无硬编码旧值残留. 证据级别 4 (CLI 实跑, 见 F1/F2).
- KF2: 展示页消费 TYPE_META 的位置全仓只有 3 处 (index.html:954 面板, 1555 星球绘制, 1927 画布标注). 星球绘制处的未知类型回退 `TYPE_META[node.m.type] || TYPE_META.task` 逐字保留 (改前 1544 行 → 改后 1555 行); 面板与标注两处对未知类型的三元空值保护逐字未动 (改前 945/1903 → 改后 954/1927). 未知类型的页面行为与改前逐字等同; 既有 5 类型的渲染分支除 prototype 改绑 demo 外未动. 证据级别 4 (render_checks 实跑 10/10) + 2 (新旧行比对).
- KF3: skill 改名的爆炸半径收在仓库文本内. 仓库无按名字硬编码的 skill 清单 (sync-to-pi.py 按目录扫描, sync-to-pi.py:199 `src.iterdir()`), 全仓旧路径活引用为零 (见 F6/F7), 新路径与链接目标全部在场. 证据级别 4 (grep 全量清点 + 文件存在性 + check_skill).

## 3. 逐项发现

判定分类: 需返工 (明确实现破坏) / 待裁决 (需产品取舍) / 已排除 (已证实无影响).

### F1 既有 ROADMAP.json 在新枚举下的读取与校验 — 已排除
- 现象: TYPE_VALUES 把 prototype 换成 demo/poc, 需确认既有 ROADMAP.json 不被校验拒绝.
- 代码依据: 仓库内 ROADMAP.json 仅 2 份 (`find . -name ROADMAP.json -not -path ./.git/*`): `docs/changes/workflow-stack-review/roadmap/ROADMAP.json` 类型集合 {acceptance x1, deliberate x4, task x5}, `docs/changes/review-session-skill/roadmap/ROADMAP.json` 类型集合 {deliberate x1, research x2, task x2}. 无 prototype, 全部落在新枚举 6 值内.
- 证据: `roadmap.py query <两份文件> milestones.<id>.type` 均成功 (得 task 与 research), 前后 md5sum 一致 (query 不写文件); `/tmp` 副本上 `save milestones.milestone-01.type prototype` 退出 1, 文件 md5 逐字节不变; `save ... poc` 与 `save ... task` 往返成功, query 读回 task.
- 判定: 已排除. 校验与既有数据兼容, 这也是 NG-001 不留别名成立的数据前提.

### F2 非法 type 的报错文案变化 — 已排除
- 现象: 写入 prototype 现在报 `非法 type 值 "prototype"; 合法值: research, deliberate, demo, poc, task, acceptance` (旧行为合法值列表不同).
- 代码依据: 文案在 `roadmap.py:224` 与 `roadmap.py:273` 由 TYPE_VALUES 动态拼装, 无第二处硬编码.
- 证据: 同 F1 的实际退出码与报错 JSON; `grep -n "TYPE_VALUES\|合法值" roadmap.py` 仅 35/220/224/270/273 五处.
- 判定: 已排除. 只影响写错值时的提示文案, 属本轮预期行为变更, 不影响任何既有合法数据与命令集.

### F3 展示页对未知类型的渲染 — 已排除
- 现象: 若某图含未知 type, 页面是否还按 task 外观回退 (模块接口不变量).
- 代码依据: KF2 三处消费点, 回退表达式与空值保护逐字未动 (index.html:954, 1555, 1927; 改前 945, 1544, 1903).
- 证据: 新旧行文本比对 (git show 962e299:workflow/navigate/web/index.html); render_checks 实跑含 无 JS 报错 pageerror 0 条.
- 判定: 已排除. 行为与改前逐字等同. 注: 未知类型的实机页面观察未做 (EXECUTION 允许人工读代码代替), 见 缺口 2.

### F4 demo 星球继承旧 prototype 视觉行为, poc 为纯新增 — 已排除
- 现象: drawStar 分派里 `type === 'prototype'` 分支 (卫星缓绕) 改绑 demo, 行为体逐字未动 (index.html:1650 起); poc 分支 (脉冲外环) 为新增代码, 无旧行为对应.
- 代码依据: index.html TYPE_META/PLANET_PALETTES/PLANET_FEATURES/drawStar 四处, demo 拿到原 prototype 的色板与地貌, poc 拿全新值.
- 证据: render_checks TC-006 PASS (图例两项, 画布标注 demo/poc 均识别, 标签色 #e8955c/#63c9a3, 配色与地貌互不相同); 整页 10/10 通过含既有类型检查 (验收类型展示 PASS, 帧率/光照/贴图数 PASS).
- 判定: 已排除. 既有类型视觉行为保持 (prototype 的视觉平移给 demo), 无丢失.

### F5 仓库内是否残留 prototype 类型的里程碑数据 — 已排除
- 现象: navigate 语汇变更后, 旧类型数据会成为校验孤儿.
- 证据: F1 的全仓 ROADMAP.json 清点, 类型统计无 prototype; `git grep '"type": "prototype"'` 零命中 (grep -rIn prototype 全仓命中见 F6, 无任何 ROADMAP.json 命中).
- 判定: 已排除.

### F6 workflow/prototype 旧路径的全仓引用清点 — 已排除
- 现象: 目录改名后, 仓库内所有仍指向旧路径的活引用会变死链.
- 证据命令与边界: `grep -rIn "prototype" --exclude-dir=.git .` 全量清点, 剔除三类后命中为零: (a) docs/changes/ 下 161 个文件的历史一手材料与决策记录 (NG-002 允许例外, 本轮对这些文件零改动, 旧字样属历史陈述); (b) `docs/adr/0024` 第 1 行 (记录旧名由来的 ADR, BR-003 允许例外); (c) `general/present/vendor/mermaid.min.js` 的 JS 语言层 `Object.prototype` 等 (第三方库内部, 与本变更无关). 剩余命中仅: test_roadmap_validation.py:189-198 (本轮新增的负向用例, 故意写 prototype 验证被拒) 与 render_checks.py 的 `CanvasRenderingContext2D.prototype` (JS 语言层).
- 判定: 已排除. README, docs/ (非 changes 区), workflow/ 正文, general/, pi/, agent-prompts/, 根 tests/, sync-to-pi.py 均无旧路径活引用.

### F7 skill 名 prototype 在 general/ 与 pi/ 配置及同步入口的点名 — 已排除
- 现象: 若配置按名字点名该 skill, 改名后调用边断裂.
- 证据: F6 同一清点中 general/ 与 pi/ 的命中仅 vendor JS 语言层; `grep -n "prototype" sync-to-pi.py` 零命中, 其 skill 发现按目录扫描 (sync-to-pi.py:199), 改名对同步机制透明.
- 判定: 已排除.

### F8 README 与文档链接指向 — 已排除
- 现象: 改名后链接死链.
- 证据: README.md:54 demo 行指向 `workflow/demo/SKILL.md` (在场); navigate SKILL.md 调用 `demo` skill (workflow/demo/SKILL.md 在场, frontmatter name: demo); demo 三文件内部相对链接 (LOGIC.md/UI.md 指向 SKILL.md, SKILL.md 指向 ../verification-contract/SKILL.md) 目标全部在场; 全仓非历史区无 workflow/prototype 链接.
- 判定: 已排除.

### F9 已安装 skills 与仓库的语汇分叉 — 已排除 (NG-004 预期边界)
- 现象: `~/.agents/skills/` 仍只有 prototype 没有 demo, 安装的 navigate SKILL.md 含 4 处 prototype 字样, 安装的 roadmap.py TYPE_VALUES 仍是旧 5 值 (第 35 行). 按仓库新正文运作的会话若真去装, 装到的还是旧名.
- 代码依据: NG-004 与 BR-004 明文本轮不改已安装 skills, 不运行同步; BR-004 审计预期恰是 `ls ~/.agents/skills | grep -xE 'demo|prototype'` 仍只有 prototype.
- 证据: 本复核只读 ls 与 grep 确认上述状态, 与规格预期一致.
- 判定: 已排除. 这是规格明文划出的边界状态, 不是本轮造成的破坏; 分叉收敛归未来同步, 不在本轮判定.

### F10 历史一手材料与历史分支 — 已排除
- 现象: 改名可能误删/误改 prototypes/ 产物目录或 prototype/<slug> 分支.
- 证据: `ls docs/changes/less-is-more-palette/prototypes/` 在场; `git branch --list 'prototype/*'` 与 `git branch -a | grep -i proto` 均为空 — 分支引用是仓库全局状态不随提交变化, 本轮 10 个非 merge 提交无任何 ref 操作, 故 本地清单与改前一致 成立 (远端核实见 缺口 3); docs/changes 的 161 个含 prototype 字样文件本轮零改动.
- 判定: 已排除.

### F11 pytest 两条 lifecycle 用例失败 — 已排除 (环境成因, 非本轮破坏), 留运行环境缺口
- 现象: `uv run python -m pytest workflow/navigate/tests` 得 2 failed, 28 passed. 失败为 test_web_server_lifecycle.py::test_start_status_stop_cycle (断言 `obj["port"] == DEFAULT_PORT` 实得 50981) 与 ::test_port_conflict_falls_back (探针 bind 39271 报 Address already in use).
- 代码依据: 占用者是母仓检出的展示服务 (pid 75138, `/home/bolo/Workspace/refactor-skill-around-verification/workflow/navigate/scripts/web_server.py __serve__ 39271`, 04:06:47 起, 0.0.0.0:39271) 外加 socat 8801→39271 局域网桥 (web-ports.md 的 navigate 交付展示页标准配方), 当时有活跃连接; 该服务属并行宿主会话 (母仓在其启动后仍有新提交), 不是本轮残留. `web_server.py stop` 的跨检出保护拒绝误杀 (报 "pid 75138 command line does not contain this script; refuse to stop"), 该保护本身工作正常. web_server.py 本轮零改动, 两条失败用例测的是它, 与 m04 差异面无交集; start 的端口自动回退机制在被占情况下仍正常工作 (回退 50981 并成功服务).
- 证据: 上述 ps/ss 输出, stop/status 原始 JSON, pytest 失败断言原文; EXECUTION.md 完成定义早已预警 "展示服务占着默认端口时三个 lifecycle 用例会失败" (实测为其中 2 条, 另 1 条因测试用独立 runtime 目录而通过).
- 判定: 已排除 (非本轮改动破坏). 但 30/30 全绿复跑未取得, 已登记为 缺口 1. 我按容器纪律未杀宿主在用的展示服务.

## 4. 未证实的路径与缺口

1. 全套 pytest 30/30 全绿复跑未取得: 默认端口 39271 被宿主会话的活展示服务占用 (F11), 2 条 lifecycle 用例在该预置下必失败. 已证实失败与 m04 差异面无关, 但按完成定义的干净复跑需宿主暂停展示服务后进行, 是否补跑由总指挥定.
2. 未知类型在真实浏览器里的页面观察未做: EXECUTION 允许以人工读代码代替, 且 KF2 的逐字比对已构成行为等同证明; 实机观察这一级证据缺失, 如需可按 EXECUTION 的人工入口补做.
3. 母仓与远端的 prototype/<slug> 历史分支清单未从本工作树核实 (git branch -a 无 remote-tracking 命中); 本地成立 (F10), 远端未证.
4. 同步入口对改名 skill 的实际同步效果未跑也不跑 (NG-004 禁止), 属永久边界而非待补检查.

## 5. 本轮实际运行的检查与结果

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| 守门脚本对既有数据 query | `uv run python workflow/navigate/scripts/roadmap.py query <两份既有 ROADMAP.json> ...` | 2/2 成功, md5 前后一致 (只读) |
| 拒绝旧类型 | `/tmp` 副本 `save ... type prototype` | 退出 1, 报错列新合法值, 文件 md5 逐字节不变 |
| 新类型写入往返 | `/tmp` 副本 `save poc` → `save task` → `query` | 全部成功, 读回 task |
| pytest (端口被占预置) | `uv run python -m pytest workflow/navigate/tests` | 28 passed, 2 failed (F11, 环境成因); m04 相关的 test_roadmap_validation.py 全部通过 |
| 文档机检 | `uv run python general/writing-for-llm/check_skill.py workflow/demo/SKILL.md` 与 `workflow/navigate/SKILL.md` | 均 OK, 退出码 0 |
| 视觉巡检 | `uv run --project general/access-web/browse python workflow/navigate/tests/visual/render_checks.py` | 10 项检查 10 项通过 0 项失败, 退出码 0, 巡检自起的服务与临时目录已清理 |
| 服务状态收尾 | `web_server.py status` | 仅剩宿主会话的服务 (pid 75138, 39271) 原样运行; 我未启动也未停止任何服务 |

原始输出留存: /tmp/m9-04-imp01/ (md5 快照) 及上文各命令摘要. /tmp 在容器重置后不存续, 关键证据已摘录进本报告.

## 6. 判定汇总

- 需返工: 0 条.
- 待裁决缺口: 0 条.
- 已排除: 11 条 (F1-F11).
- 运行环境缺口: 1 条 (F11 对应 缺口 1: 39271 被宿主活展示占用, 30/30 干净复跑未取得; 失败已精确定位为端口断言, 与本轮差异面无关).

---

## 7. 增量复查 (第二次, 返工合入后)

- 审核者: imp01 (同一影响复查身份, 任务标识 m04-delta-impact).
- 目标提交: `7faa5e6` (主线顶端, Merge branch 'review/m04-spec'; 本分支 2e0d393 已先行合入主线, 本次 `git merge refactor-skill-around-verification --no-edit` 快进到 7faa5e6, 无冲突).
- 增量范围: 评审起点 962e299 之后新出现的返工提交 `5986c3e` (feat: ISSUE-07: 落实双轴评审返工六项) 与两份评审报告文件 (REVIEW-01-standards.md, REVIEW-02-spec.md, 来自 95a856b / 50dec07, 均为纯新增报告文件, 不触碰实现). 上节 F1-F11 结论不重做.
- 增量内其余提交归类: `822cbbd` (milestone-06 反方核实与关闭) 与 `a6670e3` (更新路线图 milestone-06) 为 milestone-06 材料与 drive-execution 路线图簿记, 归 非本轮改动 (与第 1.2 节同类), 不在本增量审计范围; 4 个 merge 提交 (1166c12, 19a378d, 89334ca, 7faa5e6) 无内容改动.
- 实现面核实: `git diff 2e0d393..HEAD --stat -- workflow/demo workflow/navigate/scripts workflow/navigate/web workflow/navigate/tests/visual/render_checks.py workflow/navigate/tests/test_roadmap_cli.py` 为空 — 上轮实跑覆盖的全部实现代码在增量后零变化, F1-F5/F8-F11 的证据继续有效.

### 增量逐项发现 (G1-G6, 全部对照 ISSUE-07 的允许范围与验证入口)

- G1 TEMPLATES.md 目录约定行 `原型` 改 `演示材料` (ISSUE-07 第 1 项, TEMPLATES.md:88) — 已排除.
  现象: 首轮改名漏掉的一处中文旧语汇. 代码依据: 该行是目录约定的措辞 (findings/原型/决策文档等), 路径与 artifacts 记法未动, 无功能调用方. 证据: `grep -rn '原型' workflow/ README.md --include=*.md` 零命中 (exit 1). 说明: 本报告第 3 节 F6 的清点命令只搜了英文词 prototype, 中文词 原型 在首轮清点的边界之外, 该残留由 Standards 轴评审发现并经本轮返工关闭, 现已复核为零; F6 关于路径与英文词的结论不变.
- G2 navigate/SKILL.md poc 条目指针句去掉 `(BR-005)` 规则号 (ISSUE-07 第 2 项) — 已排除.
  现象: 规则号随变更归档后不可解析, 与同句完整路径指针参照系不一. 代码依据: 该句是本轮新增文本, 无旧行为; 删除后同句指向 `workflow/software-engineering-consensus/SKILL.md` PoC 词条的完整指针仍在, 词条在场 (上轮已核). 证据: `grep -n 'BR-005' workflow/navigate/SKILL.md` 零命中; check_skill OK.
- G3 README 工作流技能表 demo 行按字母序归位 (ISSUE-07 第 3 项) — 已排除.
  现象: 行从 navigate 之后移到 deliberate 之后 (54 行 → 44 行), 补上被改名打破的表内字母序. 代码依据: 行内容逐字不变 (diff 删除行与新增行同文), 表是给人读的索引, 无按行序消费的调用方. 证据: `grep -n 'demo\|deliberate' README.md` 显示 43 deliberate, 44 demo.
- G4 tests/visual/README.md 覆盖表补 TC-006 行并把 7 个里程碑 改 8 个 (ISSUE-07 第 4 项) — 已排除.
  现象: 该文件不在首轮允许范围的逐文件清单里, 经 ISSUE-07 返工通道明确授权 (其允许范围列明 只覆盖表两处), 不构成越界. 代码依据: 纯文档, 修的是 ISSUE-04 夹具 7→8 造成的文档漂移, 与 render_checks.py 夹具实况 (8 个里程碑, 含 demo 与 poc 各一枚) 对齐. 证据: 上轮 render_checks 实跑 10/10, 覆盖表描述与实际检查项一致.
- G5 test_roadmap_validation.py 模块 docstring 补 m04 三条用例说明 (ISSUE-07 第 5 项) — 已排除.
  现象: 注释级改动. 代码依据: 只加 3 行 docstring, 既有用例与编号未动 (ISSUE-07 明令), 断言零变化; pytest 收集与运行已复跑证实 (见下). 装饰性观察: 模块 docstring 用 TC-m04-002/003/005 的前缀式写法, 函数级 docstring 仍是 TC-002 (m04 AC-002) 风格, 两种表述指向同一组用例, 不影响任何断言与追溯, 不构成返工项.
- G6 ISSUE-03/ISSUE-04 交付证据各补录 1 行 (ISSUE-07 第 6 项) — 已排除.
  现象: 证据补录. 代码依据: 两处均为带 补录 (ISSUE-07) 标记的单行追加, 旧内容零改动 (diff 只含 + 行).

### 增量实际运行的检查与结果

| 检查 | 结果 |
| --- | --- |
| `grep -rn '原型' workflow/ README.md --include=*.md` | 零命中 (exit 1), G1 关闭确认 |
| `grep -n 'BR-005' workflow/navigate/SKILL.md` | 零命中, G2 关闭确认 |
| README demo 行位置 | 43 deliberate / 44 demo, 字母序成立 |
| check_skill `workflow/navigate/SKILL.md` | OK, 退出码 0 |
| `web_server.py status` | alive:false (上轮占用 39271 的宿主展示服务已被其属主停用) |
| `uv run python -m pytest workflow/navigate/tests` | **30 passed in 7.99s, 退出码 0** — 第 4 节 缺口 1 (30/30 干净复跑) 就此关闭 |
| render_checks | 未重跑: 实现代码自上轮 10/10 实跑后零变化 (见本节 实现面核实), 证据继续有效 |

### 增量判定汇总

- 是否需要新的返工: 不需要. G1-G6 全部是措辞/文档/注释/证据级改动, 无一触碰既有入口, 调用方或行为面; 行为代码 (roadmap.py, index.html, render_checks.py, web_server.py, demo 三文件) 在增量中零改动.
- 增量发现: 6 条, 已排除 6, 需返工 0, 待裁决 0.
- 缺口变化: 缺口 1 关闭 (30/30 已由本审核者实测取得); 缺口 2 (未知类型实机观察) 与 缺口 3 (远端 prototype 分支清单) 维持原状; 无新增缺口.
