# demo 改名与 PoC 类型落地 Product Spec

## 背景

本仓库的 `navigate` skill 用里程碑类型表示一片工作属于哪一类. 现状有两处错位: 表示"演示"的类型和同名 skill 还叫 `prototype`, 但它的实际用途已经从"一次性原型"扩到"让人看清某个样子, 行为或过程", 也能用于演示已经做好的成品; 而 PoC 这种"验证某个技术方案能不能做成"的独立工作没有自己的类型, 只能勉强塞进 `research` (靠"须先做实验测出"半句) 或 `task`.

概念与责任边界已在 milestone-01 定清 (MVP/PoC/demo 各自交付什么, 适合怎样验证, 不能据其声称什么), 名字与类型策略已在 milestone-03 裁决 (改名, 不保别名, 三子形态落位只换词, PoC 新增为 AFK 类型, 用指针而非复述). 本变更把这些裁决落到仓库的枚举, 正文, 网页, 视觉测试与 ADR 上. 提出方和维护者是仓库主人, 受益者是按这套 skill 工作的 agent 与本人.

## 目标

- G-001: 演示类工作的里程碑类型名与 skill 名都是 `demo`, skill 目录为 `workflow/demo/`, `roadmap.py` 接受 `demo` 并拒绝 `prototype`.
- G-002: 新增里程碑类型 `poc`, 在执行期间由代理独立驱动 (AFK), `roadmap.py` 接受该值, 并在网页上以英文 `PoC` 中文 `实验` 显示, 与 `demo` 各有独立可辨的外观.
- G-003: `navigate` 的 `demo` 条目按已裁决的演示语义写: 可用于演示现成成品, 完成标准是"我看过并能据此判断", 用成品演示时关闭摘要记一行, 不写死留档目录.
- G-004: `navigate` 的 `poc` 条目只写流程语 (何时创建, 完成标准, 收口产物, 终止处置), 交付物定义用指针指向 `software-engineering-consensus` 的 PoC 词条, 不复述其正文.
- G-005: `research` 条目的创建条件删去"或等一个无处可查的结论, 须先做实验测出", `task` 条目写明"需要实测算出结论但结论是描述现状的工作"归 `task`.
- G-006: 仓库新增 `docs/adr/0024-demo-poc-milestone-types.md`, 说明 `demo` 取代 `prototype`, `poc` 为新增类型, 以及旧名在历史材料里的处置边界.
- G-008: `workflow/demo/SKILL.md` 正文按演示语义重写: 写明拿已交付的成品或线上系统演示时不调用本 skill (直接跑成品), 正文不提 PoC; 通用规则 1 从"注定被丢弃"改为"不进产品, 不承诺交付, 材料可保留回看", 规则 5 的捕获改为记录演示了什么, 想让我据此判断什么, 材料位置与相关 issue 指针, 规则 6 从"验证止于冒烟"改为"验证止于能演示".
- G-009: `navigate` 的 `poc` 条目补两条: 按结论边界拆分 (一个结论能一次收口就一个里程碑, 出现多个可分别收口的结论才用依赖串成多个; 单个结论跨多个会话时保持进行中不拆; 会话规模只作经验, 不作判据), 以及实质是交付产品代码的工作归 `task`.
- G-010: `navigate` 的 `poc` 条目写明终止处置: 未证实默认保持未完成, 只有仓库主人裁决终止时才记关闭, 关闭摘要写明"未证实即终止, 不构成可行性结论"及原因, 并按裁决把它从终点验收的依赖里移除, 不记成歧路.
- G-011: `research` 条目补写"工作目录内的事实就地查, 不单立里程碑", 并给出指派: 查影响面用 `blast-radius`, 查领域用 `domain-awareness`; 需要单独立项才查得清的内部调查通常说明里程碑划错了.
- G-012: `workflow/demo/LOGIC.md` 第 5 步的"原型文件在合并主干前由人类清理"改为与"材料可保留回看, 清理由仓库主人点名"一致的说法.
- G-007: 仓库自检通过: `workflow/navigate` 的测试全绿, 本次改过的 SKILL.md 通过 `general/writing-for-llm/check_skill.py`; 已安装 skills 与全局配置未被改动, 也未运行 `sync-to-pi.py`.

## 非目标

- NG-001: 不提供 `prototype` 旧名的别名或读取兼容, 类型枚举与文档直接换名. (理由: 仓库全部历史 ROADMAP.json 都没有用过该类型, 保别名只增校验分支和文档债务.)
- NG-002: 不改历史一手材料: 既有 `docs/changes/<slug>/prototypes/` 产物目录, 旧格式 `ROADMAP.md`/`MILESTONE-NN.md`, 历史提交里的 `prototype/<slug>` 分支名一律保持原样. (理由: 它们属于已完成变更的原始证据, 不是活跃约定.)
- NG-003: 不新建 `poc` skill 目录, 也不改变 `demo` 三个子形态的落位规则, 本变更只把 `prototype` 这个词换成 `demo`. (理由: 概念边界用 navigate 条目装得下, 新 skill 是多一处长期维护入口.)
- NG-004: 不做已安装 skill 的同步与安装效果验证. (理由: 仓库 `AGENTS.md` 禁止修改真实 agent skills, 本次完成边界只覆盖本仓库文本.)

## 业务规则

- BR-001: `roadmap.py` 的类型枚举为 `research`/`deliberate`/`demo`/`poc`/`task`/`acceptance`, 其它值被拒并报出合法值清单. (审计)
- BR-002: 网页上 `demo` 与 `poc` 各有独立的类型元数据, 图例与星球外观, 类型标签分别为 `演示` 与 `实验`, 英文分别为 `demo` 与 `PoC`. (审计)
- BR-003: 活跃内容 (skill 正文, 模板, 脚本, 网页, 测试, README) 里不残留 `prototype` 的类型名, 路径约定或分支约定; 已关闭变更的一手材料与记录旧名由来的 ADR 除外. (审计)
- BR-004: 本变更不修改已安装 skills 与全局配置, 不运行 `sync-to-pi.py`, 也不声称已验证安装效果或模型行为. (审计)
- BR-005: PoC 的交付定义 (可行/不可行结论与可复查依据, 未证实即保持未完成) 以 `software-engineering-consensus` 的 PoC 词条为唯一维护位置, `navigate` 只引用不复述.
- BR-006: 演示材料与变体分支不主动清理, 要清理时由仓库主人点名删除对象.

## 验收标准

<!-- confirmed-flow: v1 -->
```gherkin
# language: zh-CN
功能: demo 改名与 PoC 类型落地

背景:
假定 仓库维护者以仓库根为工作目录, 且本变更的 demo 改名与 poc 新增已经落地

@AC-001 @normal @G-001
场景: demo skill 的目录与命名
假定 仓库维护者打开仓库根目录
当 仓库维护者查看 workflow/demo/ 目录
那么 仓库维护者看到目录里有 SKILL.md, LOGIC.md, UI.md, 且 SKILL.md 的 frontmatter 写着 name: demo
而且 读者从 description 读到这个 skill 的用途是演示
而且 仓库维护者看到仓库里没有 workflow/prototype/ 目录

@AC-002 @normal @G-001
场景: 路线图脚本接受 demo 类型
假定 仓库维护者有一份 ROADMAP.json, 其中 milestone-01 的类型是 task
当 agent 运行 uv run python workflow/navigate/scripts/roadmap.py save /tmp/demo-check.json milestones.milestone-01.type demo
那么 agent 看到命令退出码 0 并报告成功
而且 agent 查询 milestones.milestone-01.type 得到 demo

@AC-003 @failure @G-001
场景: 路线图脚本拒绝 prototype 旧类型
假定 仓库维护者有一份 ROADMAP.json, 其中 milestone-01 的类型是 demo
当 agent 运行 uv run python workflow/navigate/scripts/roadmap.py save /tmp/demo-check.json milestones.milestone-01.type prototype
那么 agent 看到命令退出码 1 并报非法 type 值
而且 agent 看到报错里的合法值清单是 research, deliberate, demo, poc, task, acceptance, 不含 prototype
而且 仓库维护者核对文件内容与改动前逐字节相同

@AC-004 @edge @G-001
场景: demo 文档的落位与子形态判定按新名字写
假定 读者手边有 workflow/demo/LOGIC.md 与 workflow/demo/UI.md
当 读者读这两个文件里的子形态约定
那么 读者读到判定顺序是先子形态 A (贴现有页面), 仅当没有邻近宿主页面才用子形态 B (新页面), 没有前端项目时降级为子形态 C (独立文件)
而且 读者读到子形态 A 的变体文件以 demo. 前缀放在 src/ 宿主页面附近, 子形态 B 用 /demo/<name> 路由与 demo/ 多文件子目录
而且 读者读到子形态 C 的产物放在 docs/changes/<feature-slug>/demos/<demo-name>/, 子形态 A 与 B 的完整变体集提交到 demo/<feature-slug> 分支

@AC-005 @normal @G-002
场景: 路线图脚本接受 poc 类型
假定 仓库维护者有一份 ROADMAP.json, 其中 milestone-01 的类型是 task
当 agent 运行 uv run python workflow/navigate/scripts/roadmap.py save /tmp/demo-check.json milestones.milestone-01.type poc
那么 agent 看到命令退出码 0 并报告成功
而且 agent 查询 milestones.milestone-01.type 得到 poc

@AC-006 @normal @G-002
场景: 地图页把 demo 与 poc 画成两种外观
假定 仓库维护者有一份 ROADMAP.json, 里面有 demo 类型与 poc 类型各一枚里程碑
当 仓库维护者运行 uv run python workflow/navigate/scripts/web_server.py start, 并打开它给出的 URL 后面拼上 ?roadmap=<假定里那份 ROADMAP.json 的绝对路径>
那么 仓库维护者看到图例里有 "演示 demo" 与 "实验 PoC" 两个条目
而且 仓库维护者看到画布上 demo 里程碑是一颗带卫星环绕的星球
而且 仓库维护者看到 poc 里程碑用的是另一套配色与地貌, 不和 demo 共用同一套外观, 两者一眼能分开

@AC-007 @normal @G-002
场景: poc 是 AFK 类型并有自己的完成标准
假定 读者手边有 workflow/navigate/SKILL.md
当 读者读该文件的 Milestone 种类小节
那么 读者读到 poc 一行标着 AFK, 并说明实验由代理独立驱动, 不需要仓库主人在场
而且 读者读到同一文件的完成标准小节有一行 poc 的完成标准
而且 读者读到收口产物那一步把 poc 的产物写成它自己里程碑里的结论与依据

@AC-008 @normal @G-003
场景: demo 类型可以用于演示现成成品
假定 读者手边有 workflow/navigate/SKILL.md
当 读者读该文件里的 demo 类型条目
那么 读者读到何时创建写着问题是什么样子, 如何运行, 或需要让人看清某个样子, 行为, 过程以便讨论
而且 读者读到条目写明拿已交付的成品或线上系统演示也归 demo, 演示活动不新增产品交付承诺

@AC-009 @normal @G-003
场景: demo 的完成标准与成品演示的关闭摘要
假定 读者手边有 workflow/navigate/SKILL.md
当 读者读该文件里 demo 的完成标准句与收口产物句
那么 读者读到完成标准是演示已做, 仓库主人看过并能据此判断要讨论的事
而且 读者读到用现成成品演示的里程碑在关闭摘要里记一行, 写明演示了什么, 看的是哪个版本, 产物可以为空
而且 读者读到文件没有要求把演示材料必须放进 demos/ 目录留档, 也没有要求成品演示再补一份说明文件

@AC-010 @normal @BR-006 @G-003 @G-012
场景: 演示材料与变体分支由仓库主人点名清理
假定 读者手边有 workflow/demo/SKILL.md, workflow/demo/UI.md 与 workflow/demo/LOGIC.md
当 读者读这三个文件里的保留与清理约定
那么 读者读到三处都写明演示材料与变体分支可以留着回看, 代理不主动删除
而且 读者读到要清理时由仓库主人点名删除对象, 三处都没有合并主干前清理或用完即删的义务
而且 读者读到 LOGIC.md 第 5 步原来那句合并主干前由人类清理, 已经换成与点名删除一致的说法

@AC-011 @normal @BR-005 @G-004
场景: poc 条目只写流程语并用指针指向共享词条
假定 读者手边有 workflow/navigate/SKILL.md
当 读者读该文件里的 poc 类型条目
那么 读者读到条目只有何时创建, 完成标准, 收口产物, 终止处置四部分
而且 读者读到交付什么与未证实如何处置写成指向 workflow/software-engineering-consensus/SKILL.md 里 PoC 词条的指针
而且 读者读到条目里没有重复抄写可行或不可行结论与可复查依据的定义

@AC-012 @normal @G-005
场景: research 条目只留查看工作目录之外的事实
假定 读者手边有 workflow/navigate/SKILL.md
当 读者读该文件里 research 的何时创建
那么 读者读到这句话只保留决策在等一个藏在当前工作目录之外的事实这一种情形
而且 读者读到原来的 "或等一个无处可查的结论, 须先做实验测出" 半句已经不在这条里

@AC-013 @normal @G-005
场景: task 条目承接需要实测但只描述现状的工作
假定 读者手边有 workflow/navigate/SKILL.md
当 读者读该文件里 task 的何时创建
那么 读者读到条目写明需要实测才能得出结论, 但结论是描述现状的工作归 task, 例如压测现有链路或采性能基线

@AC-014 @normal @G-006
场景: ADR 记下改名与新增类型的由来
假定 仓库维护者打开仓库根目录
当 读者读 docs/adr/0024-demo-poc-milestone-types.md
那么 读者读到文件说明 demo 取代 prototype 作为演示类工作的名称, poc 是新增的里程碑类型
而且 读者读到文件划出旧名处置边界, 旧的 prototype/ 开头分支与 docs/changes 下的 prototypes/ 产物目录按历史证据原样保留, 不做读取兼容

@AC-015 @normal @G-007
场景: navigate 的测试全绿
假定 agent 在仓库根目录, 依赖已就绪
当 agent 运行 uv run python -m pytest workflow/navigate/tests
那么 agent 看到退出码 0, 最后一行显示全部通过, 没有失败用例

@AC-016 @normal @G-001
场景: 类型术语在 README, 模板与 navigate 正文同步
假定 读者手边有 README.md, workflow/navigate/TEMPLATES.md 与 workflow/navigate/SKILL.md
当 读者核对这三处里的里程碑类型说法
那么 读者读到 README.md 工作流技能表里 demo 那一行指向 workflow/demo/SKILL.md, 用途写成演示
而且 读者读到 TEMPLATES.md 的 type 枚举行是 research / deliberate / demo / poc / task / acceptance
而且 读者读到 workflow/navigate/SKILL.md 的 deliberate 条目写 "无法靠演示提升保真度", 该条目不再出现 prototype

@AC-017 @normal @G-007
场景大纲: 改过的 skill 文件通过硬约束检查
假定 agent 在仓库根目录, 依赖已就绪
当 agent 运行 uv run python general/writing-for-llm/check_skill.py <文件>
那么 agent 看到退出码 0 并输出 OK

例子:
| 文件 |
| workflow/demo/SKILL.md |
| workflow/navigate/SKILL.md |

@AC-018 @normal @G-008
场景: demo skill 只管造演示材料, 演示成品时不调用
假定 读者手边有 workflow/demo/SKILL.md
当 读者读该文件的适用范围句
那么 读者读到拿已交付的成品或线上系统演示时不调用这个 skill, 直接跑成品
而且 读者核对全文, 找不到 PoC 字样

@AC-019 @normal @G-008
场景: demo skill 的通用规则 1/5/6 按演示语义写
假定 读者手边有 workflow/demo/SKILL.md
当 读者读该文件的通用规则 1, 5, 6
那么 读者读到规则 1 写演示材料不进产品, 不承诺交付, 可以保留回看, 不再写注定被丢弃
而且 读者读到规则 5 的捕获写记录演示了什么, 想请仓库主人据此判断什么, 材料位置与相关 issue 指针, 不再写归档并清理
而且 读者读到规则 6 写验证止于能演示, 不再写验证止于冒烟

@AC-020 @normal @G-009
场景: poc 条目写清拆分判据与产品代码归属
假定 读者手边有 workflow/navigate/SKILL.md
当 读者读该文件 poc 条目里的拆分与归属约定
那么 读者读到一个结论能一次收口就一个里程碑, 出现多个可分别收口的结论才拆成多个并用依赖串起来
而且 读者读到单个结论跨多个会话时保持进行中继续推进, 不拆里程碑, 会话规模只作经验, 不作判据
而且 读者读到实质是交付产品代码的工作归 task

@AC-021 @normal @G-010
场景: poc 的终止处置
假定 读者手边有 workflow/navigate/SKILL.md
当 读者读该文件 poc 条目里的终止与未证实处置
那么 读者读到未证实默认保持未完成
而且 读者读到只有仓库主人裁决终止时才把该里程碑记关闭, 关闭摘要写 "未证实即终止, 不构成可行性结论" 及原因
而且 读者读到按裁决把它从终点验收的依赖里移除, 不记成歧路

@AC-022 @normal @G-011
场景: research 条目补写就地查与指派
假定 读者手边有 workflow/navigate/SKILL.md
当 读者读该文件 research 条目里关于工作目录内事实的段落
那么 读者读到工作目录内的事实就地查, 不单立里程碑
而且 读者读到查影响面用 blast-radius, 查领域用 domain-awareness
而且 读者读到需要单独立项才查得清的内部调查通常说明里程碑划错了
```

## 决策引用

- `docs/changes/workflow-stack-review/milestone-01/DECISIONS.md`: D004, D005, D006, D007, D013
- `docs/changes/workflow-stack-review/milestone-03/DECISIONS.md`: D001, D002, D004, D005, D011, D012, D013, D014, D015, D016, D017, D018, D019
