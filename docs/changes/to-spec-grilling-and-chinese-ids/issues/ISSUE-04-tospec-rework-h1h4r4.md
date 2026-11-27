## 父级
- ../EXECUTION.md (返工轮; 评审发现 H1/H4/R4, 报告 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/integration/review1/STANDARDS.md 与 docs/changes/to-spec-grilling-and-chinese-ids/IMPACT-REVIEW.md)

## 执行
- [x] 已完成

## 要交付什么
(a) 恢复 workflow/to-spec/SKILL.md 五个编号步骤的完成标准行: 对照 general/writing-for-llm/SKILL.md 的步骤约定, 每个编号步骤以一句完成标准结尾, 内容与该步骤实际要求一致; (b) check-ac.py 报错文案中的 vN 表述与固定 v1 契约统一 (marker 固定 v1, 只统一文案不改行为); (c) 新增坏输入保护自动化回归: promote 坏格式/坏编号输入时非零退出且已有隔离正式稿字节不变, 用真实公开 CLI 与真实隔离文件, 不 mock 内部协作者 (承接 EXECUTION.md 验证策略用例22 的自动化部分; 并发窗口保持一次性真实进程证据, 不强行自动化).

## 允许范围
- workflow/to-spec/SKILL.md, workflow/to-spec/check-ac.py, workflow/to-spec/tests/, 本工单文件.

## 禁止范围
- 同 ISSUE-01 禁止范围; 不动并发实现与产品判据; 不改其他 skill.

## 验证契约
- 变更类型: 行为变更. uv run --with gherkin-official pytest workflow/to-spec/tests 全过; uv run python general/writing-for-llm/check_skill.py workflow/to-spec/SKILL.md 通过; 新增测试从公开 CLI 实跑留证 (输入/输出/退出码), 证据写 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-04/run1/.

## 验收标准
- [x] 五个编号步骤完成标准行齐备且语义与步骤一致. (`SKILL.md:25,37,55,71,96`; 五句各自的可核对观察对象见证据 `issue-04/run1/INDEX.md` 第 2 节)
- [x] v1 文案统一, 与 PRODUCT/TECHNICAL 固定 v1 要求一致. (`check-ac.py` docstring 校验项0与标记位置报错改用 `CONFIRMATION_MARKER`; `MARKER_RE` 与接受范围未改, 基线/目标同输入退出码逐例一致: `issue-04/run1/logs/marker-*`)
- [x] 新增坏输入回归测试真实 CLI 不 mock, 通过且既有 39+39 基线不回退. (新测试 `test_promote_rejects_bad_format_and_bad_numbering_inputs_keeping_output`, 11 例; 全量 `pytest workflow/to-spec/tests` 40 passed + 50 subtests, exit 0; 基点基线 39 passed + 39 subtests)

## 填写结果 (2026-11-27)

- 提交: `bbc038d` `feat: ISSUE-04: 补回 to-spec 五步完成标准, 统一固定 v1 文案, 新增坏输入转正回归` (代码/条文/测试); 本文件所在 docs 提交只补执行结果, 最终顶端 SHA 见证据 `issue-04/run1/logs/final-commit.txt`. 按派工不推送, 不合并.
- 改动文件: `workflow/to-spec/SKILL.md` (五步完成标准), `workflow/to-spec/check-ac.py` (固定 v1 文案, 行为不变), `workflow/to-spec/tests/test_ac_draft.py` (新增坏输入回归), 本工单文件.
- (a): 五步各补一句 `完成标准`, 内容从该步现行要求提炼 (闭环确认与入账 / 反方收敛与三份原件就位 / 退出码与整组失败处理 / 三项检查与发现分流 / 预览 JSON 与挂载范围), 未复用被删旧文. `check_skill.py` OK/0.
- (b): 只统一文案; `MARKER_RE` 仍按 `v数字` 匹配以兼容旧文件, 该兼容事实在 docstring 明写; 缺标记/标记位置/v1/v2 四种输入基线目标退出码一致.
- (c): 11 个坏格式/坏编号用例逐个经真实 `ac-draft.py promote` 进程运行, 断言非零退出, 既有正式稿字节不变, 报错命中规则名, 输出目录无残留临时文件; 并发三窗口按工单保持 issue-01 run5 的一次性进程证据, 未自动化.
- 证据: `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-04/run1/` (`INDEX.md`, `manifest.sha256`, `probe04.json`, `logs/`, `files/`, `baseline/`, `change.patch`).
- 未验证: 全量 `uv run pytest` (容器无 podman), 交父级集成检查.

