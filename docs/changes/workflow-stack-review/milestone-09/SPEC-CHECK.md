# SPEC-CHECK: milestone-04 PRODUCT/TECHNICAL 独立检查

任务标识: M9-SPEC-REVIEW-01
检查对象: docs/changes/workflow-stack-review/milestone-04/PRODUCT.md, TECHNICAL.md
权威来源 (只读): milestone-03/DECISIONS.md (D001-D019), milestone-01/DECISIONS.md (D004-D007, D013, D014), 根 ACCEPTANCE.md
可行性核对实际文件: workflow/navigate/{SKILL.md, TEMPLATES.md, scripts/roadmap.py, web/index.html, tests/visual/render_checks.py, tests/test_roadmap_validation.py}, workflow/prototype/{SKILL.md, LOGIC.md, UI.md}, README.md, docs/adr/ (编号与格式), general/writing-for-llm/check_skill.py, 仓库 AGENTS.md, workflow/software-engineering-consensus/SKILL.md (PoC 词条)
检查方式: 只读, 未修改任何仓库文件, 未运行会改仓库的命令, 未 git 提交.

结论标记: 落实 / 遗漏 / 无依据 / 矛盾 / 存疑.

---

## 一. milestone-03 决策逐条核对

### D001 [当前有效/必须遵守] - 落实
位置: PRODUCT.md G-001, NG-001, BR-001, BR-003, AC-001/AC-002/AC-003/AC-016; TECHNICAL.md 模块划分与模块接口.
依据: 改名 demo, 不保别名, 枚举替换与报错清单, 历史材料除外条款均与 D001 对应. 复核 F001/F009: 仓库现存全部 ROADMAP.json 的 type 只有 research/deliberate/task/acceptance, 无 prototype, 拒绝旧值不破坏既有数据.

### D002 [当前有效/必须遵守] - 落实
位置: PRODUCT.md AC-004; TECHNICAL.md 模块划分 workflow/demo/ 条目.
依据: AC-004 的判定顺序 (先 A, 无邻近宿主才 B, 无前端项目降级 C), demo. 前缀, /demo/<name> 路由与 demo/ 子目录, demos/<demo-name>/ 目录, demo/<feature-slug> 分支, 与现行 workflow/prototype/UI.md 的落位逐项对上, 确为词面替换, 位置规则未变.

### D003 [已替代 -> D019] - 未被误用, 但有一处残留影响 (见 P5, P6)
D003 的定位改写经 D019 "沿用部分" 承接 (可保留回看, 不进产品). 但 TECHNICAL.md 模块划分把 "验证止于能演示" 写成 demo 模块内容, 该句是 D003 规则 6 的改写, D019 的沿用清单未列规则 6; 且现行 prototype/SKILL.md 规则 1 "从诞生就注定被丢弃", 规则 5 "一次性分支", 规则 6 "验证止于冒烟" 若不重写, 将与 D019/AC-010 的口径自相矛盾, 而 PRODUCT.md 无对应目标或 AC. 另 LOGIC.md 第 5 步清理句见 P5.

### D004 [当前有效/必须遵守] - 部分落实, 有遗漏 (P3)
navigate 侧已落实: PRODUCT.md G-003/AC-008 承接 "可演示现成成品" 与 "演示活动不新增产品交付承诺".
遗漏: D004 预计影响明确含 "workflow/demo/SKILL.md 的适用范围句" (拿已交付成品演示时不调用本 skill) 及 "正文不提 PoC"; PRODUCT.md 无任何 G/AC 核对 demo skill 正文这两点, TECHNICAL.md 模块接口只写了 frontmatter (name: demo, description 重写), 未提适用范围句与 PoC 禁提.

### D005 [当前有效/必须遵守] - 落实
位置: PRODUCT.md AC-008 (G-003).
依据: "问题是什么样子, 如何运行, 或需要让人看清某个样子, 行为, 过程以便讨论" 与 D005 扩展后的创建条件原文一致.

### D006 [已替代 -> D017] - 未被误用
spec 按 D017 写 (AC-009), 未引入 D006 被替代前的旧口径, 也未与 D017 冲突.

### D007 [已替代 -> D019] - 未被误用
分支约定按 D019 沿用部分写 (AC-004: demo/<feature-slug> 分支), 无 "用完即删" 残留要求.

### D008 [已替代 -> D016] - 未被误用
交付定义改为指针 (BR-005/AC-011), 未在 navigate 复述; AFK 与不新建 skill 两项保留部分由 AC-007 与 NG-003 承接. 处理正确.

### D009 [已替代 -> D014] - 未被误用
spec 全文未出现 off_course 记终止的写法, 与 D014 "不写 off_course" 一致. 但 D014 本身未被承接, 见 P1.

### D010 [已替代 -> D015] - 未被误用
spec 未把 "一个会话做完一个 poc" 写进判据, 与 D015 的替代口径一致.

### D011 [当前有效/必须遵守] - 部分落实, 有遗漏 (P4)
删半句已落实: PRODUCT.md G-005/AC-012 (AC-012 还核对 "或等一个无处可查的结论, 须先做实验测出" 不在条目里, 与现行 SKILL.md:35 现文对得上).
遗漏: D011 同时要求在 research 条目写清 "工作目录内的事实就地查, 不单立里程碑" 及 blast-radius/domain-awareness 指派与 "里程碑划错了" 提示; PRODUCT.md 无 G/AC 核对这段.

### D012 [当前有效/可调整] - 落实
位置: PRODUCT.md G-002, BR-002, AC-006; TECHNICAL.md 模块划分 web/index.html 条目.
依据: 英文 PoC 中文 实验, demo 沿用卫星外观 (现行 web/index.html:1639 有 prototype 卫星分支可换键), poc 独立配色与地貌 (index.html:1201 配色表, 1213 地貌表, 均需新增条目), 图例为静态 HTML 块 (index.html:170-200). 与 D012 一致. 约束性为可调整, spec 从严落实, 无冲突.

### D013 [当前有效/必须遵守] - 落实
位置: PRODUCT.md G-006, AC-014; TECHNICAL.md 模块划分 docs/adr 条目.
依据: ADR 文件名 0024-demo-poc-milestone-types.md, 与 D013 指定完全一致; docs/adr 现有编号到 0023, 0024 是下一号; 既有 ADR 为无模板的标题+正文散文体, TECHNICAL "遵循既有格式" 可满足. AC-014 的旧分支/旧目录按历史证据保留, 不做读取兼容, 与 D001 历史条款一致.

### D014 [当前有效/必须遵守] - 遗漏, 并与 AC-011 构成安置矛盾 (P1, 最重问题)
PRODUCT.md 与 TECHNICAL.md 正文 (目标/业务规则/验收场景/模块接口/非功能要求) 均无 D014 的承接: 我亲裁终止时记关闭, close_summary 写明 "未证实即终止, 不构成可行性结论" 及原因, 按裁决从终点验收 blocked_by 移除, 不写 off_course. 两文件的决策引用节都列了 D014, 属引用了却没落实. 同时 PRODUCT.md AC-011 要求 poc 条目 "只有何时创建, 完成标准, 收口产物三部分", 而 D014 预计影响明确写 "navigate/SKILL.md 的 poc 条目终止处置句", 指针指向的 consensus PoC 词条里也没有终止流程 (只有 "未证实保持未完成"), 终止处置句在 spec 现有结构里无处安放. 需作者裁决安置位置 (并入三部分之一, 或放 navigate 验收终点/航行小节) 并补验收场景.

### D015 [当前有效/必须遵守] - 遗漏 (P2)
拆分判据 (一个结论能一次收口就一个 poc; 出现多个能分别收口的结论才拆, 用依赖串联, 各自收口; 单结论跨多会话保持进行中不拆; 会话规模只作经验不写进判据) 在 PRODUCT.md 无 G/AC, TECHNICAL.md 无对应设计条目; 决策引用列了 D015. D015 第 3 句 (实质是交付产品代码则属 task) 也未覆盖: AC-013 只承接 D018 的 "现状测量归 task", 与 D015 第 3 句是两个不同的指派.

### D016 [当前有效/必须遵守] - 落实
位置: PRODUCT.md G-004, BR-005, AC-011; TECHNICAL.md navigate SKILL 模块.
依据: 只写流程语, 交付与未证实词义指针指向 workflow/software-engineering-consensus/SKILL.md 的 PoC 词条; 该词条在场 (milestone-02 已落地), 指针目标真实存在.

### D017 [当前有效/必须遵守] - 落实
位置: PRODUCT.md AC-009 (G-003).
依据: 完成标准 "演示已做, 我看过并能据此判断要讨论的事", 不写死目录不补留档文件, 成品演示 close_summary 记 "演示了什么, 看的是哪个版本", 产物可空, 与 D017 三点逐条一致.

### D018 [当前有效/必须遵守] - 落实
位置: PRODUCT.md G-005, AC-013.
依据: "需要实测才能得出结论, 但结论是描述现状的工作归 task, 例如压测现有链路或采性能基线" 与 D018 及 F010 的 task 条目现状 (未提测量) 吻合.

### D019 [当前有效/必须遵守] - 大体落实, 有覆盖缺口 (P5)
落实: PRODUCT.md BR-006, AC-010 (SKILL.md 与 UI.md 两处清理约定), AC-004 分支名.
缺口: 见 P5 (LOGIC.md 清理句不在任何改动/核对范围) 与 P6 (SKILL.md 规则 1 定位句改写无 AC).

---

## 二. milestone-01 引用决策核对 (D004-D007, D013, D014)

- m01-D004 (MVP): 概念引用, 本变更不动 consensus 词条, 无需动作. 核对无冲突.
- m01-D005 (PoC 交付定义): 经 BR-005/G-004 指针间接落实, 指针目标与 D005 词义一致. 落实.
- m01-D006 (demo 演示用途, 不新增交付承诺): AC-008 "演示活动不新增产品交付承诺" 直接承接. 落实.
- m01-D007 (迭代只属于 MVP): 本变更不触碰迭代措辞, 引用作背景. 核对无冲突.
- m01-D013 (收录门槛): PoC/demo 已是 "我明确要求加入" 的概念且已收录, 本变更无词表动作. 核对无冲突.
- m01-D014 (domain-awareness 删旧引用): 与本变更改动集无交集, 无需动作. 但 PRODUCT.md 决策引用列了它而 TECHNICAL.md 未列, 两文件引用清单不一致, 见 P9.

## 三. ACCEPTANCE.md (m01/02/05) 与本 spec 冲突核对

无冲突. AC-02-05 的 PoC/demo 词义已落在 consensus skill, 本 spec 的指针策略与其相容且不复制正文; AC-05-07 (不跑同步, 不宣称安装效果) 与 BR-004/NG-004 一致; spec 的 AC 体系自洽于根 ACCEPTANCE "其他里程碑标准后续追加" 的安排.

---

## 四. 目标承接与验收可观察点

- G-001: TECHNICAL 承接 (workflow/demo/ 改名, roadmap.py TYPE_VALUES, web 类型元数据/图例/星球, render_checks, README). AC-001/002/003/016 覆盖. 落实.
- G-002: TECHNICAL 承接 (TYPE_VALUES 增 poc, web TYPE_META/图例/星球/配色, render_checks 类型清单与渲染用例, navigate SKILL). AC-005/006/007 覆盖. 落实.
- G-003: TECHNICAL 承接 (navigate SKILL 类型语汇只改文本). AC-008/009/010 覆盖. 落实.
- G-004: 同上模块. AC-011 覆盖. 落实 (但 D014 安置矛盾见 P1).
- G-005: 同上模块. AC-012/013 覆盖. 落实 (D011 后半遗漏见 P4).
- G-006: TECHNICAL docs/adr 模块. AC-014 覆盖. 落实.
- G-007: TECHNICAL 非功能要求 (pytest 全绿, check_skill.py, 不跑 sync). AC-015 两场景覆盖. 落实 (编号重复见 P8; G-007 中 "已安装 skills 与全局配置未被改动" 属仓库外审计声明, 无法用仓库内命令直接观察, 以 BR-004 审计口径处理可接受).

验收场景 "那么" 可观察点逐条点名: AC-001 (目录/文件/frontmatter 内容), AC-002/005 (退出码 0 + query 回读), AC-003 (退出码 1 + 合法值清单 + 文件逐字节不变), AC-004/007/008/009/010/011/012/013/014 (文件内容, 含 AC-009/011/012 的负向断言, 均可通过读取核对), AC-015 两条 (命令输出), AC-016 (三个文件内容) - 全部指得出可观察点. 唯 AC-006 的画布类断言因步骤缺 ?roadmap= 拼接而暂不可观察, 见 P7.

## 五. 非目标与技术设计禁止范围一致性

- NG-001 <-> TECHNICAL 模块接口 "不含 prototype 的兼容别名": 一致.
- NG-002 <-> TECHNICAL 目录边界 "可改 workflow/demo/, workflow/navigate/, docs/adr/, README.md; 其余文件不动": 一致, 历史一手目录均在边界外.
- NG-003 <-> TECHNICAL 模块清单 (无 workflow/poc/, demo 落位只换词): 一致.
- NG-004 <-> TECHNICAL 安全策略与非功能要求 (不触碰已安装 skills, 不跑 sync-to-pi.py): 一致, 且与仓库 AGENTS.md "禁止修改真实 agent skills" 相容.

## 六. 可行性核对

- 仓库 AGENTS.md 边界: spec 全部改动限于仓库内, BR-004/NG-004 明确不碰已安装 skills. 可行.
- roadmap.py: 错误文案确由 TYPE_VALUES 两处 join 拼出 (_fast_validate 与 _validate_milestone), TECHNICAL "只改常量, 文案由常量拼出, 不新增分支" 与代码事实相符; 单元测试 TC-002 (test_roadmap_validation.py:60) 只断言 "research" 出现在合法值清单, 枚举变更后仍通过, 无隐藏类型清单约束.
- render_checks.py: TECHNICAL 所说 "类型清单与其夹具里的类型值" 实际存在 (TYPES 行 30, 夹具 milestone-04 行 61), 描述准确; 现有断言不因加 poc 而破坏.
- check_skill.py: name 须 kebab-case 且与目录名一致 (demo 改名后满足), description 单行非空, disable-model-invocation: true 时不适用冒号限制. 可行.
- web_server.py start: 不带 NAVIGATE_WEB_RUNTIME_DIR 也可独立运行 (runtime 默认 /tmp), AC-006 的启动方式本身可行; 问题仅在 URL 拼接 (P7).
- 展示页未知类型回退: index.html:1544 确有 `TYPE_META[...] || TYPE_META.task` 回退, TECHNICAL 不变量与现状相符.
- 活跃区 prototype 词命中集: 恰为 TECHNICAL 模块清单 + prototype 本体三文件, 无清单外残留 (general/present/vendor/mermaid.min.js 的 .prototype 是 JS 语言属性, 不属类型名/路径/分支约定, BR-003 不涉).
- 枚举顺序四处一致: BR-001 = AC-003 合法值清单 = AC-016 TEMPLATES 行 = TECHNICAL 模块接口, 均为 research/deliberate/demo/poc/task/acceptance.

---

## 七. 问题清单

- P1 [D014] 遗漏+矛盾 (中高): D014 的 poc 终止处置 (亲裁终止记关闭, close_summary 固定话术, 解除终点验收 blocked_by, 不用 off_course) 在两份 spec 正文零承接; 且 PRODUCT.md AC-011 "条目只有三部分" 使 D014 预计的 "poc 条目终止处置句" 无处安放. 位置: PRODUCT.md 验收标准/决策引用, TECHNICAL.md 全文; 依据: milestone-03/DECISIONS.md D014 及其预计影响, consensus PoC 词条无终止流程.
- P2 [D015] 遗漏 (中): 结论边界拆分判据与 "会话规模只作经验" 无 G/AC/设计条目; D015 第 3 句 (产品代码归 task) 未被 AC-013 覆盖 (AC-013 只承接 D018). 位置: PRODUCT.md G-004/AC-011 附近缺失; 依据: D015 及其预计影响 "poc 条目拆分句".
- P3 [D004] 遗漏 (低中): demo skill 侧适用范围句 (拿已交付成品演示不调用本 skill) 与 "正文不提 PoC" 无 G/AC, TECHNICAL 仅写 frontmatter 重写. 位置: PRODUCT.md G-001/AC-001, TECHNICAL.md 模块接口 workflow/demo 条目; 依据: D004 内容与预计影响.
- P4 [D011] 遗漏 (低): research 条目 "工作目录内的事实就地查, 不单立里程碑" 澄清句无 AC. 位置: PRODUCT.md AC-012; 依据: D011 内容后半.
- P5 [D019] 遗漏 (低中): workflow/prototype/LOGIC.md 第 5 步 "原型文件在合并主干前由人类清理" 是 D019 取消的清理义务, 但 AC-010 只核对 SKILL.md 与 UI.md, LOGIC.md 不在改动描述与任何 AC 内; BR-003 只禁类型名/路径/分支残留, 盖不住这句, 不改即残留冲突. 位置: PRODUCT.md AC-010, TECHNICAL.md 模块划分; 依据: D019, D003 预计影响曾点名 LOGIC.md 第 5 步, 现行 LOGIC.md 原文.
- P6 [D003 已替代] 存疑 (低): TECHNICAL.md 模块划分把 "验证止于能演示" 当作 demo 模块内容; 该句出自已替代的 D003 规则 6, D019 沿用清单未列规则 6, 严格按账本口径其依据不足; 且现行 SKILL.md 规则 1 "注定被丢弃"/规则 5 "一次性分支"/规则 6 "验证止于冒烟" 的改写无任何 AC. 需作者确认规则 1/5/6 是否随 D019 一并改写并补核对点. 位置: TECHNICAL.md 模块划分 workflow/demo 条目; 依据: D003 已替代标记, D019 沿用部分清单, 现行 prototype/SKILL.md 规则 1/5/6.
- P7 [AC-006] 缺陷 (中): 当 步骤只写 "运行 web_server.py start 并打开它给出的地图页", start 返回的 URL 不带 ?roadmap= (web_server.py _instance_url), 画布类断言 (demo 带卫星, poc 另一套外观) 必须打开 "URL?roadmap=<前提里那份 ROADMAP.json 绝对路径>" 才可观察; 图例是静态 HTML 不需要参数, 会掩盖该断裂. 与 TECHNICAL 接口 "?roadmap=<绝对路径>" 及 navigate SKILL 制图 step 4 的交付方式不一致. 需补拼接步骤. 位置: PRODUCT.md AC-006; 依据: web_server.py start 输出, index.html:2096 params.get('roadmap'), TECHNICAL.md 模块接口.
- P8 [AC-015] 编号重复 (低): 两个不同场景 (pytest 全绿, check_skill 场景大纲) 共用 @AC-015, 追溯与逐项确认时无法区分. 位置: PRODUCT.md 验收标准; 依据: 文内标签.
- P9 [决策引用] 不一致 (低): PRODUCT.md 决策引用含 milestone-01 D014, TECHNICAL.md 未列; 该决策与本变更无实际交集, 建议两边对齐. 位置: 两文件 决策引用 节.

无依据新增: 未发现. 抽查的易漂移点均有出处: AC-006 卫星外观 (D012 + index.html 现状), AC-004 各落位 (D002 + UI.md 现状), AC-016 README 行 (D001 预计影响 + README.md:54 现状), AC-012 原句 (F004), NG-001 理由 (F001/F009), BR-002 标签 (D012), TECHNICAL 未知类型回退 (index.html:1544 现状). AC-016 把 deliberate 条目预期句定为 "无法靠演示提升保真度" 是对 D001 "点名 prototype 那句" 的具体措辞选择 (换词也可写作 "靠 demo"), 不算无依据, 实施时按 AC-016 文字执行即可.

## 八. 总体结论

spec 骨架健康: G-001..G-007 全部有技术承接, NG 与禁止范围一致, 已替代决策 (D003/D006/D007/D008/D009/D010) 基本未被误用, 可行性描述与仓库代码事实相符, 无方向性错误; 但 D014 完全没有承接且与 AC-011 存在安置矛盾 (P1), D015 无承接 (P2), 另有 demo skill 正文与 LOGIC.md 清理句两处覆盖缺口 (P3/P5/P6) 和 AC-006 步骤断裂 (P7), 建议作者修订这九项后再进实施.
