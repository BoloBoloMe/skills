# Standards 方向评审报告 (任务标识 m07-rev-std)

- 被评审仓库: /home/bolo/Workspace/improve
- 评审起点: 9e8dd1dfe92b3b446c88c2cb8fce33cb0c67a77a
- HEAD: 1e3c9844c6f2aea8df7135214c5225fcc2d3d766 (doc: milestone-07 评审门槛判定)
- 门槛判定: 起点到 HEAD 共 14 个提交, 审核时不晚于 1e3c984, 判定提交 1e3c984 之后无新提交, 判定正确.
- 评审范围: 产品与文档改动 16 文件 (README.md, docs/changes/to-spec-grilling-and-chinese-ids/{EXECUTION.md,issues/}, workflow/to-spec/{SKILL.md,GHERKIN.md,TEMPLATES.md,ac-draft.py,check-ac.py,tests/}, workflow/verify-change/{SKILL.md,REVERIFY.md}, workflow/navigate/{SKILL.md,ACCEPTANCE-GUIDE.md}). evidence/ 下 1211 文件只抽查 6 个路径, 不逐文件核对.
- 性质: 只读. 未改仓库任何文件, 未提交, 未推送. 本报告写在仓库外证据根.

## 一. 已检查范围

读全文:
- README.md
- workflow/to-spec/SKILL.md (90 行全读), GHERKIN.md (§2-§4 全读), TEMPLATES.md (diff 段与 PRODUCT 模板节)
- workflow/to-spec/ac-draft.py (全读 330 行), check-ac.py (全读 400 行)
- workflow/to-spec/tests/test_ac_draft.py (全读 377 行), test_ac_reading.py (全读 331 行)
- workflow/verify-change/SKILL.md (§设计验证方案 4 步 + 方案修订 + 执行第 1 步), REVERIFY.md (全读)
- workflow/navigate/SKILL.md (Milestone 类型/完成标准/阶段衔接/验收终点段), ACCEPTANCE-GUIDE.md (全读)
- docs/changes/to-spec-grilling-and-chinese-ids/EXECUTION.md (diff 段与执行记录), issues/ISSUE-01,02,03 (diff 段与交付证据全文)
- docs/changes/to-spec-grilling-and-chinese-ids/{PRODUCT.md(节选 1-120 行), TECHNICAL.md(全读 89 行)}
- 规范来源: 仓库 AGENTS.md, README.md, general/writing-for-llm/SKILL.md 与 check_skill.py 全文, /home/bolo/.agents/skills/verification-contract/reference/tests.md 全文, /home/bolo/.agents/skills/code-review/references/fowler-baseline.md 全文, workflow/verification-contract/SAFETY.md 标题结构, workflow/software-engineering-consensus/SKILL.md 相关行 (验证/验收词条), workflow/deliberate/SKILL.md:9, workflow/to-execution/SKILL.md:14-15, workflow/navigate/reference/VERIFICATION.md 全文, workflow/verify-change/reference/{EVIDENCE,SCENARIO-CHECK}.md (确认/采纳段), pytest.ini, agent-prompts/PUBLIC.md:4

实跑核对:
- uv run --with gherkin-official --with pytest python -m pytest workflow/to-spec/tests -q -> 39 passed, 39 subtests passed. 与 EXECUTION.md 与 ISSUE-01 记录一致.
- uv run python general/writing-for-llm/check_skill.py 三个改动 SKILL.md -> 均 OK, exit 0 (工具链强制项, 按约定不报结论).
- 对比 ~/.agents/skills/{to-spec,verify-change,navigate}/SKILL.md 与仓库版本 -> 三份均不同, 证实未同步安装目录, 与 EXECUTION.md "安装目录 0 差异" 一致.
- 全角/非 ASCII 标点扫描: 对 diff 全部新增行按 unicode category P/S 扫描.
- 行号核对: ISSUE-03 交付证据声明的 README:41,50-51,65-67 与 navigate/SKILL.md:41-42,55-56,71,75 逐行核对, 与声明一致.

evidence/ 抽查:
- issue-01/run5/logs/trace-atomic-formal-check.*, issue-01/run5/trace.py (全文 175 行), run5/logs 文件清单
- issue-02/check1/{INDEX.md,CHECKS-ISSUE-02.md} (结论摘要与第 9 节疑点表)
- integration/run1/{INDEX.md,pytest.stdout,pytest.exit-code.txt,archive-verify.txt}, evidence 根 pre-impl-snapshot/post-impl-snapshot 目录清单

未检查 (明确不算已检查):
- evidence/ 下 1211 文件中其余部分 (probe.py, target.py, 大量 .stdout/.exit, 1212 个归档件的逐文件摘要)
- docs/changes/ 下其他历史变更目录 (只用 grep 做交叉检索)
- workflow/to-spec/check-tech.py (本轮未改动), workflow/navigate/reference/VOYAGE.md, TEMPLATES.md 的 Navigate 部分
- 真实浏览器渲染与 present 常驻服务 (仓库自己也记为未验证, 我不重复判定)

## 二. 硬性违规 (违反已记录规范)

### H1 workflow/to-spec/SKILL.md 五个编号步骤全部丢失"完成标准"
- hunk: workflow/to-spec/SKILL.md 全新 §1-§5, HEAD:15, 25, 35, 51, 76. diff 中被删除的旧文本含 9 处 "完成标准:" (git show 9e8dd1df:workflow/to-spec/SKILL.md | grep -c 完成标准 -> 9; HEAD 文件 grep -> 0).
- 规范: general/writing-for-llm/SKILL.md:54 "每个 **步骤** 以一句 **完成标准** 结尾: 告诉 agent 这一步何时算做完的条件, 也就是它用来判断的目标", 并说明模糊边界会诱发过早完成. 该 skill 是本仓库记录下来的 skill 写作规范, README.md 技能表也把它列为"编写供 LLM 消费的 skill"的唯一入口; check_skill.py 只校验 frontmatter, 不覆盖该条, 不属工具链强制项.
- 事实: 新 §1 末条是"闭环"说明, §2 以"保留三份临时原件"清单结束, §3 以"不向下游宣称规格齐备"结束, §4 以"确保最终整份规格均有检查覆盖"结束, §5 以"盘问结束和检查通过均不是成品验收"结束. 这五段是约束或理由, 不是"何时算做完"的可判定条件. 同一 diff 的 workflow/verify-change/SKILL.md 四个设计步骤全部保留 "完成标准:" (HEAD:22,29,34,41), 执行步骤也全保留 (HEAD:53,58,63,66,71), 说明书内标准并未变, 是 to-spec 单方回退.
- 后果: agent 在盘问未真正闭环, 反方未收敛, 或两份正式稿只完成一半时都可能宣告本步完成并滑到下一步; 尤其 §3 "整组未完成" 与 §4 "首次全量覆盖" 都是容易假完成的步骤. 建议按 verify-change 的写法为 5 步各补一句可检查的完成标准.

### H2 ISSUE-02 交付证据含全角顿号 U+3001
- hunk: docs/changes/to-spec-grilling-and-chinese-ids/issues/ISSUE-02-verify-change-method-flow.md:64 (提交 34ae059 新增行), 一处行内 3 个 U+3001: "验收31-40全部场景, 验收41中 ...", "最终 73 行验证、整合复核及用户验收", "未试跑需求、未改测试、未开启 milestone-08".
- 规范: 本容器 AGENTS.md "标点一律半角 ASCII, 禁用全角 (尤其 U+3001). 普通并列用 `,`"; 仓库内同一约定的成文副本 agent-prompts/PUBLIC.md:4. 评审补充约束也把该约定列为优先于基线的仓库规范.
- 后果: 违反仓库书写约定; 同段其余并列已用半角逗号, 属笔误级不一致. 修法: 3 处换成 ", ".

### H3 ISSUE-01 交付证据含 3 个破折号 U+2014
- hunk: docs/changes/to-spec-grilling-and-chinese-ids/issues/ISSUE-01-tospec-flow-and-cli.md:62, 63, 64 (提交 3229525 新增行), 形如 "`fd26618` `feat: ...` — 7 文件".
- 规范: 同 H2 的半角 ASCII 约定; 仓库已有先例把破折号计为违规并全量清除: docs/changes/workflow-skills-writing-review/REVIEW.md:31 (F-01 "破折号 — 共 44 处, 违反仓库半角 ASCII 标点约定 ... 44 处破折号与 5 对「」全部换成逗号, 冒号, 分号, 括号或 ASCII 引号").
- 后果: 同一类问题在本仓库已被判为违规并返工过, 新提交重现. 修法: 换成 ", " 或 ":".
- 附注 (不计为违规): 同文件另有 10 余处箭头 U+2192, 但 base 提交已有 962 行使用箭头, 仓库从未把它按标点违规处理; 我不把它算违规, 只建议保持既有用法一致.

### H4 确认标记口径自相矛盾: 文档说"固定 v1", 代码文案与实现按 "vN"
- hunk: workflow/to-spec/check-ac.py:11 (本 diff 修改了这一行, 改成"由 to-spec 转正流程写入固定 v1"却仍写 `<!-- confirmed-flow: vN -->`), :175 报错文案仍写 vN, :43 MARKER_RE = `v\d+`; 对照 workflow/to-spec/GHERKIN.md:116 (本 diff 新增"含固定标记 `<!-- confirmed-flow: v1 -->`") 与 workflow/to-spec/SKILL.md:49 ("在代码块前加固定 `<!-- confirmed-flow: v1 -->` ... 标记是流程格式, 不随修文升版").
- 规范: GHERKIN.md §4 校验项 7 与 SKILL.md §3 是本轮确认下来的现行规则; 同一变更自己的新技术条文要求"固定 v1". 仓库另有"同一口径只维护一处"的成文要求 (docs/changes/workflow-stack-review/ACCEPTANCE.md:70, AC-10-02).
- 事实: 我把同一行原文读成两层冲突: 占位符写 vN, 括注写"固定 v1"; 实现上 MARKER_RE 接受 v1..vN, 因此把标记写成 v2 的正式稿能通过机检, 所谓"固定 v1"只靠文档自觉. 同时 :175 的报错把 vN 告知用户, 与 :171 的报错 (打印 CONFIRMATION_MARKER=v1) 口径不同.
- 后果: 检者与写者读到两套规则; 若下游按"固定"去核验 (例如 grep v1), 一个 v2 文件会同时"机检通过"又"不合规". 建议: docstring/报错文案统一成 v1 常量, 若真要容忍历史 vN, 在 GHERKIN.md 写明"机检接受 vN, 现行写 v1".

### H5 ISSUE-02 明确交接给集成核对的跨文件项, 集成记录里没有闭环
- hunk: docs/changes/to-spec-grilling-and-chinese-ids/issues/ISSUE-02-verify-change-method-flow.md:63 ("其旧确认用语及 `workflow/navigate/reference/VERIFICATION.md` 第9行的重确认表述留待调用方集成核对, 不声称跨切片一致"); docs/changes/to-spec-grilling-and-chinese-ids/EXECUTION.md 执行记录的集成检查行 (只列 pytest, 3 个 SKILL.md 的 check_skill, 规则12 范围审计, 安装目录摘要 0 差异, 证据归档与密钥扫描); workflow/navigate/reference/VERIFICATION.md:9 现状仍写 "判据或方案依据变化须先更新权威输入并重新确认方案".
- 规范: 仓库记录的交付纪律要求全局结果在切片集成后补入父级执行记录并回链 (issues/ISSUE-03:50 "在全部切片集成后执行, 结果回链 `../EXECUTION.md#执行记录`; 本 issue 未执行或等待, 不作为本 issue 合并前置"); 三份 issue 的验收标准都要求"验证方法受环境阻塞的项明确记为未验证, 不报告通过", 而这一项既未给结论也未记未验证.
- 事实: 我逐条核对了 EXECUTION.md 的集成检查清单与其证据 (integration/run1 的 INDEX, pytest.stdout 39 passed, archive-verify.txt), 其中没有 navigate/reference/VERIFICATION.md 或"旧确认用语"的字样; 也 grep 了 evidence 全树, 没有该项的核对记录. 现状文本"重新确认方案" 与新 verify-change "只补问新增或改变的验证决定 ... 不恢复逐版整份审阅" (HEAD:47 方案修订) 方向不完全一致.
- 后果: 已交接的待办悬空, 读者无法从记录判断这是有意保留还是漏改; 同仓两处条文对"方案修订后要不要重新确认"给出不同强度的说法. 建议: 或改 VERIFICATION.md:9 措辞, 或在 EXECUTION.md 记录"已核对, 保留不改及理由".

## 三. 判断性发现 (基线坏味道 / 测试真实性)

以下均引用 hunk, 按 fowler-baseline.md 每条"是什么 -> 如何修复"给出; 仓库已记录规范优先于基线, 所以这些不定为违规, 是否返工由用户决定.

### J1 判断性 (Duplicated Code): 同一盘问纪律写了两遍, 同一方案核对口径写了五遍
- hunk A: workflow/to-spec/SKILL.md:21-22 ("续问"/"入账" 两条) 与 workflow/verify-change/SKILL.md:28 (第 2 步第三段) 是同一段业务的两次成文: 换会话前先入账, 再 handoff, 交接写当前可问问题/已否决分支及理由/逐题与逐节(或实际方案范围)覆盖进度/盲区扫描进度/待裁决项/我明确提出的节奏要求, 已入账内容只引用, 不推测我的状态, 不新增盘问专用文件/章节/格式, 免问不留痕. 两版只在"逐节"与"实际方案范围"一词上不同.
- hunk B: "执行/复验前核实当前方案内容及引用来源仍适用; 只补问新增或改变的验证决定; 有依据的转述错误直接修正并独立复查; 内容修订递增版本并保留确认依据" 这一条同时出现在 README.md:67, workflow/navigate/SKILL.md:71, workflow/navigate/ACCEPTANCE-GUIDE.md:14, workflow/verify-change/SKILL.md:51 (执行第 1 步), workflow/verify-change/REVERIFY.md:7.
- 规范依据: general/writing-for-llm/SKILL.md 剪枝节 "让每个意义住在单一真相源: 一个权威位置, 改变行为只需一处编辑"; docs/changes/workflow-stack-review/ACCEPTANCE.md:70 "同一口径只维护一处".
- 现实后果已出现: H4 与 H5 全是漏改其一处的产物.
- 修法: 续问/入账/交接只留 verify-change 一处, to-spec 用一句话指名 (例如"续问与入账按 `verify-change` 的设计方式第 2 步的账本与交接纪律"), 或抽到 decision-ledger/handoff 由双方引用; 方案核对口径只留 verify-change 一处, README 与 navigate 只写结论不复制流程细节.

### J2 判断性 (Shotgun Surgery): 一次"确认语义"变更散落到 8 个文件, 已漏 2 处
- hunk: 为同一件事 (盘问闭环代替逐版采纳) 需同时改 workflow/to-spec/SKILL.md, GHERKIN.md, TEMPLATES.md, workflow/verify-change/SKILL.md, REVERIFY.md, workflow/navigate/SKILL.md, ACCEPTANCE-GUIDE.md, README.md; 而 workflow/navigate/reference/VERIFICATION.md:9 与 workflow/to-spec/check-ac.py:11,175 未跟上 (即 H4/H5).
- 修法: 把"确认语义"收成一个可引用的权威段落 (例如 SOFTWARE-ENGINEERING-CONSENSUS 词条或 verify-change 方案修订节), 其余文件只放指向该段的指针, 使下次变更只需改一处加若干指针检查.

### J3 判断性 (测试保护缺口, 且交付记录对覆盖的表述不成立): 删 6 个用例后有 2 项保护无任何替代
- hunk: workflow/to-spec/tests/test_ac_draft.py 删除 test_replace_failure_preserves_old_output_and_cleans_temp_file, test_formal_recheck_failure_preserves_old_output; 对应保留实现仍在 workflow/to-spec/ac-draft.py:265-283 (_atomic_write 的 finally unlink 与 _existing 复检) 与 :294 `checker.validate_product(candidate)`.
- 交付记录的声称 (ISSUE-01:96 "后者的保护目标改由真实外部进程时序 (trace-*) 与真实 CLI 用例承担") 只对 2/4 成立: 我读了 evidence 的 issue-01/run5/trace.py 全文, 四个窗口是 atomic (成功路径), base/draft (输入在转正过程中变化), output (正式目标在过程中变化), 并断言无残留 .tmp; 没有覆盖 os.replace 抛 OSError 的清理路径, 也没有覆盖"候选正式稿复检失败保留旧文件"这一分支. 新增的 test_promote_rejects_invalid_draft_without_altering_existing_output 只走到 :292 validate_draft 就退出, 到不了 :294 validate_product(candidate).
- 规范: verification-contract/reference/tests.md "功能测试: ... 用来长期防止行为退化"; "手动验证代码 ... 即使使用 JUnit/pytest 或放在 test/ 下, 也不能因此算功能测试", 即一次性取证脚本不能顶替防退化的测试.
- 修法: 用真实接口补两条用例 (临时目录内把目标路径造成目录或只读以触发写入失败; 用只在候选稿上违规的夹具触发正式复检失败), 或者在 ISSUE-01 中把"改由 trace-* 承担"改成如实表述并登记未覆盖的保护.

### J4 判断性 (Mysterious Name / 断言与目标不符): 目录目标用例声称验证临时文件清理, 实际到不了那段代码
- hunk: workflow/to-spec/tests/test_ac_draft.py:301-308 test_promote_refuses_directory_target_without_leaving_temporary_file.
- 事实: 目录目标在 ac-draft.py:289 `previous = _existing(output)` 处就抛 IsADirectoryError (OSError, 退出 2), 早于 _atomic_write 的临时文件创建; 因此 `assertEqual(before, set(self.output.parent.iterdir()))` 恒真, 与"without leaving temporary file"无关.
- 修法: 改名说清 (例如 test_promote_refuses_directory_target), 或换成真能触发 _atomic_write 失败 (只读父目录, os.replace 失败) 的构造.

### J5 判断性 (断言与测试意图无关): CRLF 原字节用例里塞了卡片数断言
- hunk: workflow/to-spec/tests/test_ac_reading.py:321-327 test_preview_leaves_raw_input_bytes_unchanged 中 `assertEqual(3, len(self.preview().select("acceptance-card")))` 与本用例目标 (输入原字节不变) 无关; 该用例原先还核对 promote 把 CRLF 原字节嵌入正式稿, 现在只剩三行断言.
- 规范: tests.md 好测试"失败能指向目标行为"; 该行失败只会指向渲染条数, 与本用例名不符.
- 修法: 删掉该行 (卡片数已由 test_documented_example_is_valid_and_expands_to_three_cards 与 test_every_example_row_gets_background_steps_and_all_columns 覆盖); 若要保留 promote 的 CRLF 段, 在 test_ac_draft 的换行循环里已有, 或在此显式断言 promote 结果.

### J6 判断性 (一测多断言): 新用例把三件事塞进一个测试
- hunk: workflow/to-spec/tests/test_ac_draft.py:263-271 test_promote_rejects_removed_review_option 同时断言 --help 不含 --review, 传 --review 退出 2 且 stderr 命中 argparse 文案, 旧输出字节不变.
- 规范: tests.md 好测试"每个测试只有一个逻辑断言". 传入已删参数时旧输出不变, 属另一条独立主张.
- 修法: 拆成"选项已删除"与"拒绝时不改旧文件"两条, 或删掉第三条断言 (该保护可由 J3 建议的新用例承担).

### J7 判断性 (Mysterious Name, 术语漂移): "设计方式" 没有对应小节名
- hunk: workflow/verify-change/SKILL.md:45, 51, 79 与 README.md:65, workflow/navigate/SKILL.md:71 使用"设计方式", 文件内小节名是 `## 设计验证方案` (HEAD:18), 另有"执行方式" 指 `## 执行验证方案` (HEAD:49). 同文件 :16 首段也没定义"设计方式".
- 事实: 该词来自已确认账本 (DECISIONS.md:267,288,398), 所以不是我方造词, 但它在本 skill 里没有任何定义句或锚点.
- 修法: 首次出现处写"设计验证方案方式 (下称设计方式)", 或全量改成小节标题的原名. 证据侧 issue-02/check1/CHECKS-ISSUE-02.md 第 9 节 Q4 已作为非阻塞疑点提出.

### J8 判断性 (信息层级与就近放置): 达标标准整节插在步骤 4 与步骤 5 之间
- hunk: workflow/to-spec/SKILL.md:65 "## 达标标准与检查边界" 位于 §4 (HEAD:51) 与 §5 (HEAD:76) 之间, 而 §4 正文用"下节达标标准"指它.
- 事实: 这是参考材料 (writing-for-llm 的信息层级第 2 级) 插在两条步骤序列中间, 读者顺序执行 1->5 时会被打断; 旧版把它放在"流程"之前, 阅读顺序是"规则-流程-收尾".
- 修法: 要么挪到"规格约束与停止条件"旁边 (同为参考材料), 要么留在原位但把 §5 一并收进 §4 的收尾, 使 5 个步骤连续.

### J9 判断性 (Duplicated Code, 既有非本轮引入): promote 对同一内容校验两遍
- hunk: workflow/to-spec/ac-draft.py:292-294: 先 `checker.validate_draft(...)` (内部 with_draft(confirmed=False) 后整份 validate_product), 再 `checker.with_draft(..., confirmed=True)` 后 `checker.validate_product(candidate)` 再跑一遍同样的解析与编号对账.
- 说明: 这一段在 base 提交即如此, 本 diff 只动了其中的错误文案与函数签名; 我列为发现仅为完整, 不要求本次返工. 修法 (下次): 让 validate_product 接受"是否带标记"的结果对象, 避免重复解析.

## 四. 已核对且未发现问题的点 (避免误解为漏查)

- review_id / --review 残留: 我 grep 了全仓 (排除 evidence 与历史变更), 产品文档与代码只剩"不存在"断言 (test_ac_draft.py:217) 与历史文档引用, 无兼容分支; 与 GHERKIN.md, SKILL.md 的新文案一致.
- 锚点与链接: to-spec/SKILL.md 引用的 ../verification-contract/SAFETY.md#脱敏, TEMPLATES.md/GHERKIN.md 引用的 SKILL.md#达标标准与检查边界, ACCEPTANCE-GUIDE 引用的 SKILL.md#milestone, REVERIFY/verify-change 引用的 #方案修订, deliberate/to-execution 引用的 to-spec/SKILL.md#规格约束与停止条件 全部有对应标题.
- 调用边: to-spec 不再整体调用 deliberate, 而 README:65 与 navigate/SKILL.md:41 都写明 deliberate 仍可独立调用; 我 grep 了 general/ 与 workflow/ 正文, 没有残留"to-spec 调 deliberate"或"to-spec 只做规格整理"的旧说法, README 的人工核对要求在本 diff 内没有可举证的违反.
- 测试事实核对: pytest 39 passed + 39 subtests 与记录一致; 删 6 加 3 与 42->39 一致; 新增子测试数 +2 可由 test_duplicate_rule_ids 改为 subTest 解释; 未发现"测试全绿但被绕过"的用例 (改动后 preview/promote/check 全部经真实 CLI 进程, 删掉的都是 mock 内部协作者型用例).
- 测试技术栈与夹具: 仍是 Python unittest + 临时目录 + 真实文件系统, 无持久层替身; evidence 里的 .py 取证脚本落在 docs/changes/ 下, pytest.ini 的 testpaths 不含该路径, 不会被默认收集, 不违反 tests.md 的手动验证隔离要求.
- 交付证据的可复查性抽查: integration/run1 有 pytest 原始输出与退出码, archive-verify.txt 逐文件 sha256 同值, trace.py 断言与 stdout/exit 原件齐备; EXECUTION.md 的"39 passed"与"安装目录 0 差异"两处声称与我能核对的现场一致.
- ISSUE-03 声明的行号: README:41,50-51,65-67 与 navigate/SKILL.md:41-42,55-56,71,75 逐行命中, 与声明一致.

## 五. 结论

- 发现总数 14: 硬性违规 5 (H1-H5), 判断性发现 9 (J1-J9, 其中 J9 为既有非本轮引入).
- 最严重: H1 (to-spec 五步全部丢失"完成标准"), 它直接影响 agent 何时算做完, 是仓库自身写作规范被回退; 次严重 J1/J2 (同一口径多处复制, 已实际导致 H4/H5 两处漏改).
- 测试方向: 无 mock 内部协作者残留, 无替身持久层, 技术栈沿用; 但删除用例后有两项失败保护无替代 (J3), 一个用例名不副实 (J4), 一个人工抽查时应看到的真实性问题.
- 人工抽查与是否接受仍由用户决定; 本报告不代表验收结论.