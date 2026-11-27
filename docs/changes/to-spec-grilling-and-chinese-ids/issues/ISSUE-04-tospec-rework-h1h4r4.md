## 父级
- ../EXECUTION.md (返工轮; 评审发现 H1/H4/R4, 报告 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/integration/review1/STANDARDS.md 与 docs/changes/to-spec-grilling-and-chinese-ids/IMPACT-REVIEW.md)

## 执行
- [ ] 已完成

## 要交付什么
(a) 恢复 workflow/to-spec/SKILL.md 五个编号步骤的完成标准行: 对照 general/writing-for-llm/SKILL.md 的步骤约定, 每个编号步骤以一句完成标准结尾, 内容与该步骤实际要求一致; (b) check-ac.py 报错文案中的 vN 表述与固定 v1 契约统一 (marker 固定 v1, 只统一文案不改行为); (c) 新增坏输入保护自动化回归: promote 坏格式/坏编号输入时非零退出且已有隔离正式稿字节不变, 用真实公开 CLI 与真实隔离文件, 不 mock 内部协作者 (承接 EXECUTION.md 验证策略用例22 的自动化部分; 并发窗口保持一次性真实进程证据, 不强行自动化).

## 允许范围
- workflow/to-spec/SKILL.md, workflow/to-spec/check-ac.py, workflow/to-spec/tests/, 本工单文件.

## 禁止范围
- 同 ISSUE-01 禁止范围; 不动并发实现与产品判据; 不改其他 skill.

## 验证契约
- 变更类型: 行为变更. uv run --with gherkin-official pytest workflow/to-spec/tests 全过; uv run python general/writing-for-llm/check_skill.py workflow/to-spec/SKILL.md 通过; 新增测试从公开 CLI 实跑留证 (输入/输出/退出码), 证据写 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-04/run1/.

## 验收标准
- [ ] 五个编号步骤完成标准行齐备且语义与步骤一致.
- [ ] v1 文案统一, 与 PRODUCT/TECHNICAL 固定 v1 要求一致.
- [ ] 新增坏输入回归测试真实 CLI 不 mock, 通过且既有 39+39 基线不回退.