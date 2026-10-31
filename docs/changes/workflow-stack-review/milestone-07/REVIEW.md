# milestone-07 独立复核报告

任务标识: workflow-stack-review-m07-review. 复核者: 未参与实施的独立 pi 会话 `01a19294-fd3d-7645-b8db-136d7c4e5b75` (pi/cli-glm-5.3-flash/max), 仅做文本与可运行检查, 不修复, 不替用户改决定, 不关闭里程碑.

- 目标提交: `c77f6af446d294c3d498c570feb88bd41fe79bb6` (doc: milestone-07 落地流程接口与执行哲学, 17 文件).
- 基准父提交: `6717c5e3f966821aa3fedcf0b8459e4fa2537b3a`.
- 权威依据: `../ACCEPTANCE.md` 的 AC-06-01..09 与 AC-07-01..06 (用户已确认), `../milestone-06/DECISIONS.md` 与 `../milestone-10/DECISIONS.md` 的当前有效决定.
- 作者 `IMPLEMENTATION.md` 只作待核实线索, 其中可实际验证的检查 (check_skill, tests.md 保真, navigate 子集, pytest 阻塞) 均由本复核独立重跑证实; 文件释放/信件等过程性声明无法从仓库验证, 不作通过依据, 也不构成疑点.
- 目标后提交 `e567e84` (5 个证据文档) 与 `c94c548` (ROADMAP.json) 未触碰 17 个目标文件; 本报告绑定固定目标提交.
- 全部实际命令, 时间, 输出见同目录 `REVIEW-CHECKS.log`.

## 逐项结论

milestone-06 (本轮按原项核对, 不复制标准):

- **AC-06-01 通过 (文本核对).** benchmark-checklist 的一次性实验节已收敛为指针: 写明任何一次性实验 (不限影响调查证明脚本) 都适用 blast-radius 第 5 节 (位置: `workflow/benchmark-checklist/SKILL.md` 一次性实验的边界节); 测量特有记录 (自启进程停止, 数据留存位置与停止结果) 保留在 benchmark. blast-radius 第 5 节逐条覆盖旧 benchmark 删除的全部边界条目, 锚点链接与实际节名匹配. 两份 reference/PROVENANCE.md 相关行同步, 历史决策原文未改. 未验证缺口: 链接锚点按 markdown 常规规则人工核对, 未用渲染器实测.
- **AC-06-02 通过 (文本核对).** drive-execution 执行循环已删独立 "旧行为影响复查" 节点; 评审节点调用 code-review 时传入评审起点, 产物根目录和判定结果; 顺序约束改为 "各评审方向 (含按门槛纳入的旧行为影响方向) 未定案不核验"; 免做判定由总指挥在调用评审前做出, 理由在 EXECUTION.md 执行记录留一行并提交; IMPACT-REVIEW.md 只在实做轮产出; 返工后对新集成提交按门槛重做 (code-review 汇总节与 drive-execution 重构节点两处衔接一致). 位置: `workflow/drive-execution/SKILL.md` 执行循环, `workflow/code-review/SKILL.md` 步骤 4/6.
- **AC-06-03 通过 (文本核对).** 旧行为影响方向落入 code-review: 门槛免做条件与判定依据 (类型声明 + 实际差异触碰面) 只维护在步骤 4 一处; reviewer 输入含评审起点, commit 列表, 产物根目录及上轮 IMPACT-REVIEW.md; 任务简述逐项承接报告构成 (目标提交, 逐项发现与已排除项, 代码依据, 既有检查及本轮运行结果, 未证实路径写缺口, 不以搜索命中充当安全证明, 不声称有限检查找到全部影响) 与逐轮追加不覆盖; 该方向由未参与实现与修复的独立审核者运行, 无人可派报缺口不由作者补位; 发现进三方向并列汇总, 由调用方总指挥分流 (实现破坏拆返工 ISSUE, 产品取舍报缺口逐级到用户); 明确写出不进入 Spec 评审方向或 verify-change 的输入判据, 保留 "调查报告, 不新增产品判据". 位置: `workflow/code-review/SKILL.md` 步骤 4/5/6 与结论口径.
- **AC-06-04 通过 (文本核对).** navigate 验收终点节新增单句边界, 条件式表述 (判据能否在真实入口重复执行), 无按交付物类型枚举; verify-change 与验收指南 (PRODUCT.md 转正规则) 未改. 位置: `workflow/navigate/SKILL.md` 验收终点节首句.
- **AC-06-05 通过 (文本核对).** README 调用关系口径行旁新增维护者规则: 调用关系变化时人工核对 README 技能表与各 skill 正文中的执行调用语句, 并经非作者复核; 未新增任何调用边校验测试 (目标 diff 无新测试文件). 位置: `README.md:11`.
- **AC-06-06 通过 (文本核对).** `general/grill-me/` 已删除, README 通用技能表对应行已删, 两份 PUBLIC 未动, 历史决策文档未动, 活跃引用归零 (rg 零命中). 安装副本仍在, 与 "保留至宿主下次同步裁掉, 本变更不运行同步" 的既定边界一致.
- **AC-06-07 通过 (实际运行).** 7 个本轮修改的 SKILL.md (benchmark-checklist, code-review, drive-execution, navigate, software-engineering-consensus, to-execution, verification-contract) 全部通过仓库 `general/writing-for-llm/check_skill.py`, exit=0, Python 3.11.2, 本复核独立执行. 作者同命令记录 (CHECKS.log) 与我结果一致.
- **AC-06-08 通过 (文本核对).** 目标 diff 只含本仓库文件, 无已安装 skills/全局配置改动, 无同步脚本运行痕迹; README 技能表只删 grill-me 行与 tdd 行 (tdd 行属 AC-07-01) 并更新 code-review 描述, 未新增条目; benchmark 指向 blast-radius 边界节属引用, 按 README 口径不算调用边. 检查结论只覆盖静态文本与可运行检查, 模型遵从率/安装效果未验证 (按实施边界, 不作缺口计).
- **AC-06-09 通过 (实际检索).** 指定五处 (code-review/SKILL.md, fowler-baseline.md, verification-contract 的 code-review 引用行, drive-execution 相应句, README code-review 表行) 评审语境 "轴" 全部清零 (rg exit=1), "为何双轴" 节名改 "为何分开评审" 且无其他文件引用旧锚点; 全仓剩余 "轴" 命中 (follow-the-money 三根轴, use-sandbox-worktree 记录轴, 测试历史注释) 均非评审语境, 在 AC 范围外. 历史决策文档未改.

milestone-07:

- **AC-07-01 通过 (实际运行 + 文本核对).** `workflow/tdd/` 整目录删除; `tests.md` 迁至 `workflow/verification-contract/reference/tests.md`, cmp 逐字节相同 (两侧 md5 dbb6b61d991689c6cce7d2b1ba7ca7ea), 原文无链接与自指句, 无需修正; `mocking.md` 按当前有效 D011 有意丢弃, 理由成立 (边界清单唯一在共用底线, 设计期接口建议不属验证 skill). 活跃执行调用与文件链接无悬空: 全仓活跃命中仅 SKILL-MECHANICS.md:21 的命名举例 (非调用术语举例, AC 允许保留) 与两处测试历史注释; README tdd 行已删; v-c "按需自动化" 条新增指向 reference/tests.md 的按需指针, 目标文件存在.
- **AC-07-02 通过 (文本核对).** 垂直切片词条逐字符合 milestone-10 D003 确认原文 (定义句与 _避免_ 行一字不差, 主词 "垂直切片 (tracer bullet)"), 位置在概念词条区 (迭代之后), 标题格式与该文件既有词条一致; to-execution 就地改既有完成标准条 ("能从真实入口独立验证, 可独立交付并能演示") 并同条补预重构/纯核验/非行为改动例外, 宽重构例外说明原样保留, 未新增同义完成标准条. 位置: `workflow/software-engineering-consensus/SKILL.md` 垂直切片节, `workflow/to-execution/SKILL.md` 起草完成标准.
- **AC-07-03 通过 (文本核对).** v-c 共用底线 "边开发边实跑" 改写为 "尽早完成真实验证闭环": 最短交付路径, 可验证版本, 真实入口端到端, 修复后重跑同一端到端, 循环到闭环, 并写明不强制先写测试或红绿顺序; 行为变更完成证据补端到端优先, 分层/自动化测试只作补充, 环境不可得报缺口不充抵; 结构变更删去步骤式 "做法" 句, 改为证据要求 (同一检查同输入/条件改前改后结果, 改前就应通过, 类型检查与 lint 不能单独证明行为未变); mock 只在 "替身只在系统边界" 条后补理由与禁令, 边界清单未复制. 闭环机制全仓仅此一处 (rg 证实), drive-execution 未复制. 位置: `workflow/verification-contract/SKILL.md` 共用底线/行为变更/结构变更节.
- **AC-07-04 通过 (文本核对).** 缺陷修复节做法句承接 milestone-11 已落地链条 (复现 → 定位原因 → 制定修复方案 → 执行修复 → 验证修好且没改坏, 与 `workflow/fix-bugs/SKILL.md` 正文一致) 与手段优先级 (既有测试/开发命令/CLI 入口 → 真实入口 → 必要时一次性临时脚本, 不提交跑完清理, 不新增专用脚本); 基准版已有的失败记录/同一检查通过/原始场景复跑要求原样保留; 本轮补齐 tdd 迁出的取证选择判断 (低成本测试 vs 六类改用非测试手段并写明理由) 与两条红态细则 (失败须来自目标问题而非环境或测试代码自身; 意外通过先怀疑没覆盖症状), 完成证据追加受影响范围复验结果与独立复核记录 (写明范围/手段/缺口, 不把有限检查说成全部没改坏); 未重复实施 milestone-11 的改名与阶段链 (fix-bugs 文件未动). 位置: `workflow/verification-contract/SKILL.md` 缺陷修复节.
- **AC-07-05 通过 (文本核对).** drive-execution 独立核验节点新增一句: 作者侧端到端验证记录只作对照, 不作任何必验项的通过依据; 关键真实路径结论只取独立核验者本轮实跑. verify-change 未改; 未复制共用底线闭环机制; 现有 "核验只产证据, 不产验收结论" 与 "另起独立会话" 保留. 位置: `workflow/drive-execution/SKILL.md` 独立核验节点.
- **AC-07-06 部分完成, 全量 pytest 未验证 (实际运行).** check_skill.py 七个技能全部通过 (本复核独立执行). `uv run python -m pytest -m "not e2e"` 在本容器复跑: tests/conftest.py:236 会话启动缺 podman, INTERNALERROR, exit=3, 0 条用例运行, 与作者两次记录一致; 该阻塞已由作者向宿主请求补跑, 结果尚未回, 本复核不把它算通过, 不以文字核对代替实际测试通过. navigate 子集 30 条由本复核独立复跑通过 (exit=0), 仅作额外回归记录, 不充抵全量结果. "由未参与修改的另一位代理逐项复核" 即本报告, 绑定目标提交. 全量非 e2e 测试真实结果 = AC-07-06 当前唯一未验证缺口.

## 发现

### 已证实问题

无. 15 项 AC 未发现违背确认标准或决策账本的落点错误, 旧要求丢失, 判据混入或越界改动.

专项核对结果 (任务点名项): 门槛规则唯一落 code-review 步骤 4, drive-execution 只引用不重复; 该方向审核者独立性 (未参与实现与修复, 不由作者补位) 在; 报告构成七要素与逐轮追加不覆盖在, 且旧报告只供该方向闭环与汇总分流; 返工重做在 code-review 汇总与 drive-execution 重构节点两处衔接; IMPACT-REVIEW 不进 Spec 方向与 verify-change 判据; mock 边界清单唯一, 只补理由; tests.md 逐字节保真且无悬空引用; navigate 单句验收边界无类型枚举; to-execution 例外 (预重构/纯核验/非行为改动) 就地补进同一条; Standards 的仓库优先 + Fowler 判断性双源机制逐字未动; milestone-10 F014 四处 "真实入口/端到端" 表述未动.

### 待核实疑点 (不阻塞, 供用户裁决时参考)

1. 全量 pytest 缺口 (同 AC-07-06): 宿主补跑结果未回前, milestone-07 不具备按 AC-07-06 关闭的条件. 这是环境阻塞不是本轮改动的失败证据, 但在补跑通过前应保持进行中.
2. v-c 缺陷修复 "取证选择" 句与 milestone-10 D012 账本措辞有两处微差: "要改大量无关测试数据" (账本为 "要改动"), 另有账本未列的增量 "在安全环境改用非测试手段取证" 与 "无法安全复现则报缺口". 语义与 D012 及共用底线一致, 无信息丢失, 判为可接受措辞差异, 非缺陷; 如用户要求逐字落账可再校.
3. AC-06-03 的分流链是两跳: code-review 写 "需要产品取舍的先报缺口交我裁决" (skill 语境的 "我" = 调用方总指挥), 由 drive-execution 评审节点 "待裁决缺口停下向我汇报" (向用户) 抵达用户. 与 D008 "产品取舍报缺口交用户" 的链路整体一致, 无矛盾; 单读 code-review 一文时 "交我" 的指代依赖调用方语境.
4. 垂直切片词条头词用 `## ` 节标题呈现, D003 账本内联文本为加粗主词; 定义与避免行逐字相同, 且与该文件既有词条 (MVP/PoC/demo/迭代) 的呈现格式一致, 判为格式适配非偏离.
5. 安装目录观察: `/home/bolo/.agents/skills/` 下 grill-me 与 tdd 安装副本仍在. 与 AC-06-06/D011 "本变更不运行同步, 由宿主下次同步自动裁掉" 的既定边界一致, 非违规; 提醒宿主同步未发生前两处安装副本与仓库状态不一致属预期.

## 实际范围声明

- 已验证: 17 个目标文件全部读取并与基准逐块比对; 7 个 SKILL.md 的 check_skill.py 实跑; tests.md 逐字节比对; tdd/mocking/diagnosing-bugs/grill-me/评审语境 "轴"/IMPACT-REVIEW/闭环机制/双轴的全仓活跃检索 (排除 docs/changes, docs/adr, vendor); blast-radius 第 5 节对旧 benchmark 条目的覆盖逐条比对; F014 四处与 verify-change, to-spec, ACCEPTANCE-GUIDE, 两份 PUBLIC, ADR 未动的确认; navigate 子集测试实跑.
- 未验证: 全量 `pytest -m "not e2e"` (容器缺 podman, 待宿主补跑); 模型实际触发/遵从率, 安装效果 (按实施边界不在本轮范围); 文件释放与信件往来等过程性声明 (无法从仓库核实, 未发现反证).
- 本报告绑定目标提交 `c77f6af446d294c3d498c570feb88bd41fe79bb6`. 复核完成不等于 milestone-07 关闭: AC-07-06 全量测试缺口按标准须先闭环, 正式验收仍归 milestone-08.
