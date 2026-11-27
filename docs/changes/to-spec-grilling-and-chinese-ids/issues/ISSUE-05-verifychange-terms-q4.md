## 父级
- ../EXECUTION.md (返工轮; SPEC 报告线索 Q4, 报告 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/integration/review1/SPEC.md)

## 执行
- [ ] 已完成

## 要交付什么
workflow/verify-change/SKILL.md 术语统一: 设计方式 与 H2 设计验证方案 不一致处 (约第 45, 79 行, 以 SPEC 报告引用为准) 改为与标题一致的表述, 语义不变.

## 允许范围
- workflow/verify-change/SKILL.md, 本工单文件.

## 禁止范围
- 同 ISSUE-02 禁止范围; 只做术语统一, 不改任何流程语义.

## 验证契约
- 变更类型: 行为变更 (条文). uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md 通过; 改动前后 diff 只含术语处; 证据写 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-05/run1/.

## 验收标准
- [ ] 术语统一且语义不变, 格式检查通过.