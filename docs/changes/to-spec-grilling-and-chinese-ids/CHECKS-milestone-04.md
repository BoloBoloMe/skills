# milestone-04 规格整理与检查记录

## 确认来源与范围

- 用户明确要求本会话改用拟改的盘问方式对齐规格, 不阅读固定草稿. 旧草稿的 review_id 采纳步骤已由 DECISIONS.md 决策19替代.
- 产品要求承接 milestone-03 已确认决定. 本轮确认闭环清单不额外附逐节结论, 采纳交接文档补充覆盖/盲区扫描/明确节奏要求, 并重新逐节对齐技术方案.
- 技术盘问八项建议由用户统一回复 "确认". 内容按完整决定记录在 DECISIONS.md 决策22-29, 相关查证事实按随决策确认的方式记录.
- 本次交付 PRODUCT.md 与 TECHNICAL.md, 不实施待改技能, 不将当前对话作为已实现新版技能的成品试跑证据.

## 领域与权威输入

- 仓库约定: AGENTS.md 要求只改本仓库, 禁止改已安装技能.
- 领域语言: docs/language/UBIQUITOUS_LANGUAGE.md. 沿用既有规格, 决策账本, 交付单元, 接缝与依赖等定义.
- 相关 ADR: 0020, 0025, 0027. 本轮未引入新领域概念, 未作难以逆转的架构选择, 不新增领域文档或 ADR.
- 起草依据: 当前有效的 DECISIONS.md 条目, 路线图已确认范围, 当前模板与 GHERKIN.md 格式约定. 历史演示和被替代决定只供理解历史, 不作为现行内容依据.

## 已完成的输入检查

- 决策编号1-29与事实编号1-10连续, 无重复.
- 对照本轮开始前的 Git 版本, 历史决策1-18/事实1-8原文保留.
- 账本变更的 Git 空白检查通过.
- 旧的未知海域唯一项已明确属于范围外且已有相同 off_course 记录, 从 unknown_seas 删除重复项; 未增加真实试跑或调参工作.

## 正式生成与机检

- 本轮工作区: /tmp/to-spec-ac-ml71iqdi. 产品暂存稿为 PRODUCT.base.md, 验收草稿为 review/to-spec-ac-ml71iqdi-AC-v2.md, 技术草稿为 review/to-spec-ac-ml71iqdi-TECHNICAL-v2.md.
- 草稿机检: `uv run --with gherkin-official python workflow/to-spec/check-ac.py <产品暂存稿> --draft <验收草稿>` 退出0, 38个场景/30个AC; `uv run python workflow/to-spec/check-tech.py <技术草稿>` 退出0, 6节.
- 机械生成: 现有 ac-draft.py preview/promote 返回 success=true. 本次 --review 参数仅满足尚未改造的现有工具的字节校验, 不表示用户看过或采纳了 hash, 实际内容确认依据为决策19与本轮答复.
- 技术稿用文件复制生成 TECHNICAL.md, 草稿与正式稿字节比较一致.
- 正式机检: `uv run --with gherkin-official python workflow/to-spec/check-ac.py docs/changes/to-spec-grilling-and-chinese-ids/PRODUCT.md` 退出0, 38个场景/30个AC.
- 正式机检: `uv run python workflow/to-spec/check-tech.py docs/changes/to-spec-grilling-and-chinese-ids/TECHNICAL.md` 退出0, 6节.
- PRODUCT.md SHA256: fc9b7eabd5a0cc7110b2d4117ccba67b19a42127c5fe47307e4df8f7357ce8c5.
- TECHNICAL.md SHA256: f5394ec29d5a72b0c811227fdbd311f491454b70530030d81d2bf91a897a719e.
- 可选 HTML 为 /tmp/to-spec-ac-ml71iqdi/review/2026-11-26-acceptance-5400f3d57f88-aa15ba5a.html, 页面自检 success=true, 本机 HTTP 200 且与脚本原件字节一致. 局域网入口为 http://192.168.65.165:37857/2026-11-26-acceptance-5400f3d57f88-aa15ba5a.html.
- 预览沿用现有脚本格式, 本轮不再将其中旧的待审提示作为确认步骤; 改造预览提示属于后续实施.
- 新增规格与报告未发现非 ASCII 标点. 本轮没有 SKILL.md 或代码改动, 不运行 pytest/check_skill.py, 不据此宣称成品行为已通过验证.

## 正式规格独立检查

- 报告: REVIEW-milestone-04.md. 执行会话未参与盘问, 反方或写稿, 只检查并写报告, 未修改规格.
- 检查对象绑定上述两份 SHA256. 对账覆盖目标/非目标/规则, 38场景/30个AC和技术判定; 从账本及用户答复反推覆盖, 检查可观察点, 产品到技术承接与跨条目矛盾.
- 结论: 无阻塞. 两项正式机检在独立会话复跑均退出0. 报告中的三条备忘不影响下游理解/执行/验证, 不作返工或新增要求.
- 本轮收敛后账本为决策1-30/事实1-10. 决策15原正文保留, 依用户新确认的修文范围标为由决策30替代, 其余旧决策正文保留.
- 两份规格已足以供 milestone-05 设计验证方案和 milestone-06 拆分执行. 此结论不代表后续技能改造已实施或通过成品验收.

## 反方报告核实与收敛

独立报告为 OPPOSING-milestone-04.md, 执行者未参与本轮盘问与落盘.

- F1 采纳文字冲突: 用户本轮明确确认了修文按影响范围复查, 以决策30替代旧决策15的覆盖深度表述, 首次全量, 返修复查受影响处, 未受影响部分沿用既有核对结论. 检查会话提出范围, 主会话按既有复核规则核实. 未采纳反方提出的一改覆盖标签就强制全量等额外门槛, 因其不在已确认要求中.
- F2 未成立为新增决策缺口: 账本 "预计影响" 不是拟新增的节标题. 规格按现有模板将跨产品转正/技术复制/检查的失败处理放进关键流程, 无须增设节名.
- F3 采纳引用不完整: 既有共用脱敏规则实际位于 workflow/verification-contract/SAFETY.md 的脱敏节, 适用于捕获材料的传递/展示; 事实10补齐引用, 安全节直接指向该规则. 材料经现有会话任务输入和账本引用传递, 不新增盘问常设记录. 未另定新的脱敏制度.
- F4 采纳取证改进: 机械文件复制本身已有机械成分, 不是由 LLM 重写. 为直接证实原文一致, 技术稿复制后做字节比较; 比较方式留作可调整实现, 不新增服务或公开接口.
- 原反方会话针对上述四项再次独立复核, 报告末尾记录 F1-F4 已收敛, 仍有真实阻塞为无. 历史决策15仅更新替代状态, 正文保留; 新规格引用决策30.
