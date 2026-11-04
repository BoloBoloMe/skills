# 测试规范与人工抽查流程验证记录

## 版本与范围

- 分支: `refactor-skill-around-verification`.
- 初始提交: `ca9224f551857b119fb2bc86b90c0aa6343cf9e8`. 过程中 fetch 后快进接收宿主网络文档变更, 基线更新为 `f7e4dab9cd17ec06554a2b45b133248563b70405`, 与本次文件不重叠.
- 本次只修改 9 个 workflow Markdown 文件及本目录记录. 不修改真实 agent skills, 不运行同步, 不改 `verify-change` 或产品代码.
- 本次改变 skill 的实际操作要求, 按行为变更核对.

## 独立会话场景验证

- 复核者新会话: `01a1a579-9aeb-70ac-ab38-ad766c9a9610`, Herdr agent `test-rules-review-2`, tab `w1:t2R`. 由本会话新建, 未参与这些文档的编写/修复; 仓库只读.
- 实际模型: `cli/deepseek-flash`, thinking `high`, kind `pi`. 按 review 画像选型, coding 1.12, knowledge 0.93; 任务是按给定中文规则判断与追查, 不依赖外部专业知识. 稳定性评分依据偏弱, 由作者逐项核对结论, 不仅采信评分.
- 先试 `cli/glm-5.3-flash/xhigh`, 但上游额度耗尽返回 503, 未产出模型结论, 不计作验证.
- 实际输入见 [PROBE-PROMPT.md](PROBE-PROMPT.md), 复核者完整初检报告见 [REVIEW-01.md](REVIEW-01.md).
- S1/S2 拒绝假持久层和无数据库时以 mock 全绿关闭. S3 区分 H2 不能证明 PostgreSQL 锁/事务, 与真实 SQLite 内存实例可证明唯一键行为的有限范围.
- S4/S5 拒绝新增 Python 诊断程序并混成功能测试, 也拒绝只换 Java 就保留默认 CI 执行. S6 允许复用已有 Playwright 平台及 shell 启动命令.
- S7 停在用户选样/接受之前, 不接受作者挑好的 3 条或 AFK 自动确认. S8 要求排查共用 Fake 的全部使用处并复跑, 由用户复抽. S9 无测试代码变更时不硬加用例. S10 按用途区分手动点名的功能测试与调查脚本, 删除项也进清单.
- 上述是实际模型运行产生的场景决定, 不是 Java/数据库产品测试结果, 也不是正式人工验收.
- 作者复核时未把报告的所有扩展推断照单收下: S6 未说明 Playwright 实际执行情况, 不能据此断言套件漏跑; S1/S8 即使把 Fake 重新标为调查代码, 也不允许冒充真实持久层的功能验证. 场景决定只按已给事实和规范核对.

## 初检发现与处理

1. 汇报格式漏测试代码验收状态: 已在 `orchestration.md` 加独立状态项, 待抽查/返工不得正常收尾.
2. 无 issue/Roadmap 时缺清单基线: 已要求先核实并记录本次改动前提交, 核实不了报缺口.
3. 好测试条目口径变化与来源不明: 撤回对单一逻辑断言条目的改写, 保留原规则; 数据隔离和不得吞异常/删断言的补充在 REQUIREMENTS 落点中明记, 不冒充用户逐字指示.
4. 验收记录位置可能分叉: 已统一沿用正式验收记录及目录, 无记录才单独留档, 后续引用原件不重复建档.
5. navigate 指向整节的链接较宽: 保留. 目标节包含抽查与逐项产品确认, 链接有效且不妨碍执行, 无需新增独立锚点.
6. 缺本仓库验证记录位置: REQUIREMENTS 已链接本文件.

## 复检与文档检查

复检报告见 [REVIEW-02.md](REVIEW-02.md), 实际输入仍保存在 PROBE-PROMPT.md 的复检节. 复核者确认初检衔接项已处理, 无新增冲突, S1-S10 的分类和停点未因修订失效.

- R1: 无 issue 且直接取当前 HEAD 生成空清单, 被拒绝; 须先核实真实改动前提交, 展示比较范围与依据, 不能漏未提交部分. 复核者建议再明写半句, 本轮不继续加字: 当前规则已要求核实改动前提交和完整本轮变更, R1 也实际被正确拦下; 人工接受仍绑定目标提交.
- R2: task 目录已有绑定本轮版本的人工接受记录, 最终验收只引用原件, 不重抄.
- R3: 产品核验全绿但用户未选样/接受, 汇报必须写待抽查与所需决定, 不得正常收尾或宣布正式交付.

复检没有替用户接受本次规范; 作者已逐项核读两份报告, 未将其超出题设的推断作为已证实缺陷. 最终文档检查已完成: 14 个 Markdown 文件, 33 个相对链接/锚点, 代码围栏, 新增内容的尾空格/标点及文件末尾换行全部通过; `git diff --check` 通过. 检查使用项目已有 Python 的一次性 `uv run python -` 命令, 未新增测试程序或依赖. 未顺手修改 navigate 正文原有的一处行尾空格.

本轮检查与规则文件 SHA-256 原始输出如下, 用于将场景复核绑定到提交内的实际规则内容; 不依赖随 HEAD 前移的简称:

```text
Changed Markdown files: 14; local links/anchors checked: 33
Scope: Markdown-only changes, local links/anchors, fences, whitespace/newlines, added punctuation.
All checked items passed.
41f5a4fff3aa30e890ce5d2a547f07df7dd2db46629e0251ec9d2a77677b7ff9  workflow/verification-contract/SKILL.md
bf8ba0593c24bdac08ca8d56932a8178ef6c7eecce69bc8c1b4307ae30f1487c  workflow/verification-contract/reference/tests.md
2b7e0b2a4ef1a7215191c3bae21756ca4314997fc5201e89d096d1d822b0c92c  workflow/code-review/SKILL.md
c0611d939658f0e9ca9e8e69c3aab6e036137eaa975292762375ec3580959ed6  workflow/code-review/references/reviewer-briefs.md
5e6a9165225a9da5e0bcb2d4955d88de56f00d1bb75e8a5306b72c6e96a39308  workflow/drive-execution/SKILL.md
dac4254bf5735b856cec9c0fcb8c2e0dee17ba093d6a04adbe1bd7b0be371670  workflow/drive-execution/reference/orchestration.md
40e24ec5ba81cb29981a22d576950bc06bf59395ffd5268c2a9ca03f70d73811  workflow/navigate/SKILL.md
8995943bf0f24f1724fdf26242ffff23e6d2eab7cb88c8b6e187a374bba20e5d  workflow/navigate/ACCEPTANCE-GUIDE.md
ba9af5de05009f0221aa9a28c2b0a9aca715ecba25065fc342f3706d20a7da07  workflow/to-execution/TEMPLATES.md
```

两轮复核结果已取回并归档, 失败模型的 tab 与完成复核的 tab 均已关闭. 后半程双方信箱 presence 曾显示离线而本地工具称仍运行, 因此复检明确改走 Herdr 提交与等待, 未强投, 未把消息状态当业务结果.

## 本次测试代码验收适用性

比较基线为上文 f7e4dab, 本次仅为 Markdown 规则与记录, 没有新增/修改/删除/移动功能测试, 手动验证程序, 夹具, 替身或测试运行配置. 场景输入/复核报告是文档证据, 不是项目功能测试代码. 因此记录无相关代码变更, 不虚构样本和用户接受结论.

## 未覆盖范围

未运行仓库 pytest/整套测试, 未启动外部服务或数据库, 未把 drive-execution/navigate 从实施到正式验收走完, 未同步并验证安装版. 文档链接/格式检查不能代替这些范围; 场景复核也不证明未来每个 LLM 会话一定遵守规则. 最终人工接受仍由用户决定.
