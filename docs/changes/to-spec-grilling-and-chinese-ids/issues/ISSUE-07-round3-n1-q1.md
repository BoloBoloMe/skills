## 父级
- ../EXECUTION.md (返工轮三; 发现 N1 [IMPACT-REVIEW.md 第二轮] 与 Q1 [integration/review1/SPEC.md])

## 执行
- [ ] 已完成

## 要交付什么
(a) workflow/verify-change/SKILL.md 修订段 (约 47 行) 补一句禁止新增盘问专用记录格式的表述, 与 :28 现有禁令语义一致, 不改其他内容 (Q1, 轻微); (b) workflow/navigate/SKILL.md:71 与 README.md:65 中 verify-change 的 设计方式 改为 设计验证方案, 与该 skill :11/:18 的调用方式名一致 (N1), 语义零变化.

## 允许范围
- workflow/verify-change/SKILL.md, workflow/navigate/SKILL.md, README.md, 本工单文件.

## 禁止范围
- 同 EXECUTION 全局禁止范围; 不动其他 设计方式 残留 (verification-contract/SKILL.md:15 在范围外, 只记录不改).

## 验证契约
- 变更类型: 行为变更 (条文). uv run python general/writing-for-llm/check_skill.py 对两个改动的 SKILL.md 通过; diff 仅目标行; 证据写 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-07/run1/.

## 验收标准
- [ ] 修订段禁令句与 :28 一致; 两处术语对齐; 格式检查通过; 无范围外混入.