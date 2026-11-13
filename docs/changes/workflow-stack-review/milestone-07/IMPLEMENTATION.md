# milestone-07 实施记录

## 输入与范围

- 用户指定本轮处理 milestone-07; 实施前提出六项标准, 经 wtf 用大白话说明后, 用户回复"按这个做". 已确认标准在 `../ACCEPTANCE.md` 的 AC-06 与 AC-07, 不在本文件复制判据.
- 直接权威输入是 `../milestone-06/DECISIONS.md` 的当前有效 D001/D004-D008 与 `../milestone-10/DECISIONS.md` 的当前有效 D003/D005/D006/D011-D021. D002/D003 (milestone-06) 已由 D008 替代; milestone-10 旧条目的替代关系按账本, 不复活旧决定.
- 开始实施时基线: `ec44b55` (milestone-12 路线图更新). milestone-11 的改名与缺陷修复链条已在 `49d0d60a3e67e262ba489913a6e844b7c0bc0c06` 落地, 本轮只承接其接口和补齐 milestone-07 所属增量.
- 本轮是非编码的工作流行为变更, 不是普通非行为文字修订: skill 会改变实际操作. 不新增程序/测试或调用边校验, 不需要补编码规格/EXECUTION/issues, 按 navigate 的非编码 task 直接实施. 文本核对和格式检查不证明实际 LLM 遵从率; 程序回归测试按已确认标准另记真实结果.

## 共用文件协调

- milestone-11 会话通过 Herdr `w1:p15` 明确释放 `README.md`, `workflow/verification-contract/SKILL.md`, `../ACCEPTANCE.md` 的整文件编辑与暂存窗口; 已提交版本是 `49d0d60`, 对方本轮不再写入. 对方独立信箱 `01a1909e-86ab-746d-a023-2561b49e17d0`, 释放信 id `0d471efbfadb44f093c5dcf9c62cc770`. 本会话随后才编辑三文件, 保留 AC-11 与 fix-bugs 改名结果.
- `workflow/navigate/SKILL.md` 另向 milestone-04 指挥会话 `01a19001-045f-7461-af16-51f92495b496` 请求释放, 请求信 `87364985bf6f4711be42098986717fb4`. 随后通过 Herdr `w1:pN` 核到对方明确答复: 编辑已结束, 目标提交 `2166d75`, 该文件可释放, 39271 空闲; 核验在独立 `verify/m04` 检出, 不受主仓文档改动影响. 对方当时信箱判我离线故未强投, 本会话从 Herdr 读到实际答复后才修改. 不以工作区干净或 idle 推断释放.
- 不代交他人未提交改动. ROADMAP.json 只由守门脚本逐字段读写, 本轮不改其他里程碑状态/产物或可视化海域; 源码提交不夹带共享路线图.

## 决策到落点

| 决策 | 落点与处理 |
| --- | --- |
| milestone-06 D001 | benchmark 一次性实验节改指 blast-radius 完整边界, 明确适用于任何一次性实验; 保留测量特有的自启进程停止与数据位置记录; 两份 PROVENANCE 同步. blast-radius 边界正文保持原义与完整性. |
| milestone-06 D004 | navigate 文件释放后, 验收终点补确认判据的单句边界, 不动验收指南的 PRODUCT.md 转正规则. |
| milestone-06 D005 | README 调用关系口径旁补维护者人工核对技能表/正文执行调用与非作者复核要求; 不新增自动校验. |
| milestone-06 D006 | 删除 general/grill-me 与 README 行; 真实安装副本不动. |
| milestone-06 D007/D008 | 统一评审方向称谓; 旧行为影响从 drive-execution 独立节点迁入 code-review, 门槛只维护在后者. 保留独立审核者, 完整报告与逐轮追加, 总指挥分流和返工重做, 不让报告进入 Spec/verify-change 判据. |
| milestone-10 D003/D013 | 按确认文本新增垂直切片词条, 就地修改 to-execution 的既有完成标准并补例外, 不新增同义条目. |
| milestone-10 D005/D006/D014/D015 | verification-contract 唯一维护尽早真实验证的闭环机制; 行为变更补端到端证据边界, 结构变更改为同条件同检查的前后证据; mock 只补理由与禁令, 清单不复制. |
| milestone-10 D011/D012/D014 | tdd 只迁 tests.md, 原文件无需链接修正则保持逐字相同; mocking.md 有意丢弃, 因共用底线已有唯一边界且设计期接口建议不属于验证 skill. 缺陷修复节承接 fix-bugs, 补取证成本判断/失败原因与意外通过判断, 保留原红态与复验要求并补受影响面复验与独立复核记录. |
| milestone-10 D016 | drive-execution 独立核验节点只加作者材料作对照的分工句, 不复制闭环机制, 不改 verify-change. |

## 明确不动的项

- 不新增调用边自动校验: 按 milestone-06 D005 的自然语言分类脆弱与维护成本理由, 由 README 的维护规则与非作者复核承接.
- code-review 的 Standards 双源机制保持原样: 仓库规范优先, Fowler 基线始终携带且仅作判断性发现, 工具链已覆盖项跳过 (milestone-06 F011).
- 不收"验收"词条, 不废 ACCEPTANCE.md, 不改 verify-change 或 navigate 验收指南; 按 milestone-06 D004 保持分工与转正阀门.
- 不复制 mock 清单, 不迁 mocking.md, 不复制端到端闭环到 drive-execution, 不在 to-execution 另加同义完成标准, 依照 milestone-10 当前有效裁决.
- ADR 0025 已由 milestone-10 完成, 不重写或修改旧 ADR; milestone-11 的改名, 阶段链, 分工不重复实施; 不追溯 milestone-04/09 的已定规格与执行规则.
- 不改现有真实入口/端到端概念的其他活跃定义, 不声称概念级唯一维护.
- 不改真实已安装 skills 或全局配置, 不运行 sync-to-pi.py, 不宣称安装/触发率/遵从率已测. 原安装版 domain-awareness 的 WORKFLOW_VOCABULARY.md 指针已落后于本仓库, 当前领域依据为 `workflow/software-engineering-consensus/SKILL.md`, 不把旧指针补回仓库.

## 验证安排与初始事实

- 逐项检查 AC-06/AC-07, 运行修改过的 SKILL.md 的仓库 `check_skill.py`; 迁移 tests.md 核对字节, 检查现有链接与执行引用; 不用检索无命中冒充模型实跑.
- 已实际预跑 `uv run python -m pytest -m "not e2e"`: 在 `tests/conftest.py:236` 的会话启动阶段因缺少 `podman` 退出 3, 尚未运行用例. 原始记录 `/tmp/workflow-stack-review-m07/pytest-before.log`. 这是环境阻塞, 不是测试通过或本轮实现失败.
- 已向出生宿主具体会话请求安全可用的完整测试环境, 请求信 `84feeb9f210a42209453c40fcf5c5a6f`. 不造 podman 替身, 不改测试或环境假装通过.
- 非作者复核选用独立 Herdr 新会话 `m07review`, `pi` + `cli/glm-5.3-flash` + `max`. 依据 llm-select 的 review 画像: coding/knowledge/longctx/stability 为基准 1, review 总分 1.000, 适合复杂文本审查; 比当前作者模型成本低且为不同厂商, 降低共同盲区. 配置与原生参数已核实, 未参与实施. 最终报告须绑定源文件提交, 不将作者说明直接当作通过依据.
- 所有检查与独立复核记录后续记入本目录, 有缺口时 milestone-07 保持进行中. 不提前关闭 milestone-08 或宣称正式交付.
