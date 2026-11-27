## 父级
- ../EXECUTION.md (返工轮; SPEC 报告线索 Q4, 报告 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/integration/review1/SPEC.md)

## 执行
- [x] 已完成

## 要交付什么
workflow/verify-change/SKILL.md 术语统一: 设计方式 与 H2 设计验证方案 不一致处 (约第 45, 79 行, 以 SPEC 报告引用为准) 改为与标题一致的表述, 语义不变.

## 允许范围
- workflow/verify-change/SKILL.md, 本工单文件.

## 禁止范围
- 同 ISSUE-02 禁止范围; 只做术语统一, 不改任何流程语义.

## 验证契约
- 变更类型: 行为变更 (条文). uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md 通过; 改动前后 diff 只含术语处; 证据写 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-05/run1/.

## 交付证据
- 提交: `dd40f98` `feat: ISSUE-05: 统一 verify-change 设计验证方案术语` (只改 `workflow/verify-change/SKILL.md`); 随后 `docs: ISSUE-05: 填写交付证据与验收标准` 只改本工单文件. 按派工不推送, 不合并.
- 改动位置: `workflow/verify-change/SKILL.md:45,51,79`, 均为 `设计方式` -> `设计验证方案` (与 `:11` 调用方式名和 `:18` H2 标题一致). 依据 `integration/review1/SPEC.md:151` 的 Q4 条目; 现场 `grep` 改前恰好命中这三行.
- 语义不变证明: 逐行比对 HEAD 与工作区, 变更行号只有 45/51/79, 每行新内容 == 旧行把 `设计方式` 换成 `设计验证方案` 后的字符串, 其余字符逐字节一致; 新文件 `设计方式` 计数 0, 旧为 3. 原件 `run1/term-normalized-diff.txt`, `run1/diff-numstat.txt` (`3 3` 单文件), `run1/diff.patch`.
- 格式检查: `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` -> `OK`, exit 0 (`run1/check-skill.txt`); 改前同命令 `OK`, exit 0 (`run1/pre/check-skill.txt`).
- 证据根: `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-05/run1/` (索引 `INDEX.md`, 清单 `manifest.sha256`).
- 未覆盖: 允许范围只含本文件; 现场仍有同类 `设计方式` 用法在 `workflow/navigate/SKILL.md:71`, `workflow/verification-contract/SKILL.md:15`, `README.md:65`, 均在本工单范围外, 未改未擅扩. 全量 `uv run pytest` 属父级完成定义, 与 ISSUE-01 同因本容器无 Podman, 未验证.

## 验收标准
- [x] 术语统一且语义不变, 格式检查通过. (`dd40f98`; `run1/term-normalized-diff.txt`; `run1/check-skill.txt` OK/exit 0)