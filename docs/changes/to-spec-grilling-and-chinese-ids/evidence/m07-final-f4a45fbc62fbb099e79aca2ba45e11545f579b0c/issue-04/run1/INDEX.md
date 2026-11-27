# ISSUE-04 run1 证据索引

任务: m07-rw-04; 工作树 `/home/bolo/Workspace/improve.worktrees/ISSUE-04`, 分支 `issue/04`, 基点 `1874ede`.
绑定提交: `bbc038d` (代码/条文/测试) + `e6b7962` (仅工单文档, `logs/doc-only-diffstat.txt`); 最终提交 `e6b7962d4815d00ec006cb7c839e6df74ad7d701` 上复跑 pytest 与 check_skill 全绿 (`logs/post-commit-*`).
范围: 返工发现 H1 (五步完成标准), H4/R7 文案 (固定 v1), R4 的可自动化部分 (坏格式/坏编号 promote 回归).
环境: Python 3.11.2, pytest 9.1.1, gherkin-official 43.0.0, Linux (容器内).

## 1. 命令与退出码

| 命令 | 结果 | 原件 |
| --- | --- | --- |
| `uv run --with gherkin-official pytest -p no:cacheprovider -v workflow/to-spec/tests` | 40 passed, 50 subtests passed, exit 0 | `logs/final-pytest.{cmd,stdout,stderr,exit}` |
| `uv run --with gherkin-official pytest --collect-only -q workflow/to-spec/tests` | 40 tests collected, exit 0 | `logs/collect.*` |
| `uv run --with gherkin-official pytest -v workflow/to-spec/tests/test_ac_draft.py -k bad_format_and_bad_numbering` | 1 passed (11 subtests), 21 deselected, exit 0 | `logs/new-test.*` |
| `uv run python general/writing-for-llm/check_skill.py workflow/to-spec/SKILL.md` | `workflow/to-spec/SKILL.md: OK`, exit 0 | `logs/check-skill.*` |
| `uv run --with gherkin-official python probe04.py` | 4 标记用例 + 11 坏输入用例全部达到预期, exit 0 (提交后复跑同结果) | `probe04.py`, `probe04.json`, `logs/*` |
| 最终提交复跑 pytest | 40 passed, 50 subtests, exit 0 | `logs/post-commit-pytest.*` |
| 最终提交复跑 check_skill | OK, exit 0 | `logs/post-commit-check-skill.*` |

基线不回退: 改动前同一命令为 **39 passed, 39 subtests, exit 0** (本分支基点实测, 与 `evidence/to-spec-grilling-and-chinese-ids/issue-01/run5/logs/final-pytest.*` 的 39+39 一致). 本次新增 1 个测试方法 (11 个 subTest), 因此 40 passed + 50 subtests.

## 2. (a) 五个编号步骤的完成标准

写法依据: `general/writing-for-llm/SKILL.md` "步骤 与 完成标准" 节 — 每个步骤以一句可判定、带足够要求量的完成标准结尾, 边界写清 done/not-done; 内容从当前步骤实际要求提炼, 未复用被删旧文.

| 步骤 | 完成标准位置 | 提炼依据 (同一步骤的现行要求) |
| --- | --- | --- |
| 1 核实输入, 盘问并确认 | `SKILL.md:25` | 闭环条目: 展示两份模板每节已问/未碰 + 盲区扫描 + 待裁决项关闭 + 明确结束; 入账条目: 决定与依据事实入账 |
| 2 写前反方与主会话落笔 | `SKILL.md:37` | 反方发现逐项核实收敛才落笔; 落笔缺依据先补问入账; 三份临时原件的位置与内容约束 |
| 3 机检与机械落正式 | `SKILL.md:55` | 闭环确认须可核实; 转正退出 0 且 `success` true, 其余命令 0; 输入/目标变化停止替换; 整组未完成保留现场 |
| 4 写后独立检查与修正 | `SKILL.md:71` | 三项检查 (对账/反向覆盖/达标); 发现分流 (误报驳回记理由/有据修文/缺判定补问入账); 最终整份有检查覆盖 |
| 5 预览与整组交付 | `SKILL.md:96` | 预览 `success` true 才用返回值; 只挂专用 `review` 目录; 汇报两份路径与结论; 失败按失败出口只交文件 |

语义自检: 五句都写成 "达成条件 + 未达成就停在此步", 每句均有可外部核对的观察对象 (chat 明确结束, 三份原件就位, 退出码与 JSON 字段, 三项检查结论, 预览 JSON 与挂载目录), 未把执行机制写成步骤内容. 行文与原步骤条文无矛盾, 未引入新要求在 `达标标准与检查边界` 或模板之外.

## 3. (b) 确认标记文案统一为固定 v1

改动 (`workflow/to-spec/check-ac.py`):
- 模块 docstring 校验项 0: 占位符由 `<!-- confirmed-flow: vN -->` 改为固定 `<!-- confirmed-flow: v1 -->`, 并写明 "机检按 `v数字` 匹配以兼容旧文件, 现行只写 v1".
- `extract_gherkin_block` 的标记位置报错改用常量 `CONFIRMATION_MARKER`, 不再是手写 `vN`.
- `MARKER_RE` (接受 `v\d+`) 与 `CONFIRMATION_MARKER` 未改, **行为不变**.

实测对照 (`baseline/check-ac.py` = `1874ede` 版, 同一输入, `logs/marker-*`):

| 输入 | 基线 exit | 目标 exit | 文案差异 |
| --- | --- | --- | --- |
| 正式稿缺标记 | 2 | 2 | 无 (两版都打印常量 v1) |
| 标记位于代码块之后 | 2 | 2 | 基线 `vN`, 目标 `v1` |
| 标记写 v2 | 0 | 0 | 无 (两版都接受, 行为未改) |
| 标记写 v1 | 0 | 0 | 无 |

结论: 只统一文案, 退出码与接受范围逐例一致. 与 `GHERKIN.md:116`、`SKILL.md` 第 3 步、`TECHNICAL.md:52` 的固定 v1 口径一致; 敏感的历史 `vN` 兼容事实在 docstring 明写, 不再自相矛盾.

## 4. (c) 坏格式/坏编号 promote 回归

新增测试: `workflow/to-spec/tests/test_ac_draft.py` 的 `test_promote_rejects_bad_format_and_bad_numbering_inputs_keeping_output`.

做法: 真实公开 CLI (`ac-draft.py promote` 进程), 真实隔离临时目录; 先用合法输入成功转正一次留下正式稿, 再逐例只改一个条件重跑, 断言 **非零退出 + 既有正式稿字节不变 + 退出码精确值 + 报错命中规则名 + 输出目录无残留临时文件**. 未 mock 内部协作者, 未用私有函数, 未 mock 解析器.

11 个用例 (逐例输入/输出/退出码原件在 `files/bad/<case>/`, `logs/bad-<case>.*`):

| 用例 | 类型 | exit | 报错要点 | 正式稿字节 |
| --- | --- | --- | --- | --- |
| variant-keyword (假设) | 坏格式 | 1 | 关键字白名单 | 不变 |
| synonym-keyword (并且) | 坏格式 | 1 | 关键字白名单 | 不变 |
| missing-feature-line | 坏格式 | 1 | 解析失败 | 不变 |
| feature-level-tag | 坏格式 | 1 | tag-position | 不变 |
| draft-with-marker | 坏格式 | 2 | 草稿不携带确认标记 | 不变 |
| prose-outside-fence | 坏格式 | 2 | 草稿只能包含一个 gherkin 块 | 不变 |
| unknown-goal (@G-999) | 坏编号 | 1 | 编号对账: 不存在 | 不变 |
| unknown-rule (@BR-999) | 坏编号 | 1 | 编号对账: 不存在 | 不变 |
| audit-rule (@BR-002) | 坏编号 | 1 | 编号对账: 指向 (审计) 条目 | 不变 |
| two-ac-one-scenario | 坏编号 | 1 | @AC 唯一性 | 不变 |
| duplicate-goal-entry | 坏编号 | 2 | 目标1 重复 | 不变 |

每例的顺序断言 (见 `probe04.json` 字段): `nonzero`, `exit == expected_exit`, `error_matches`, `output_bytes_unchanged`, `output_dir_entries == ["PRODUCT.md"]` 全为 true, 聚合脚本 exit 0.

并发窗口 (输入/正式目标在转正过程中变化) 按工单保持一次性真实进程证据, 未强行自动化: 引用 `evidence/to-spec-grilling-and-chinese-ids/issue-01/run5/logs/trace-{base,draft,output,atomic-formal-check}.*`. 本次未新增也未重复声称那三个窗口.

## 5. 文件清单

- 代码/条文: `workflow/to-spec/SKILL.md`, `workflow/to-spec/check-ac.py`, `workflow/to-spec/tests/test_ac_draft.py` (完整差异 `change.patch`).
- 基线副本: `baseline/SKILL.md`, `baseline/check-ac.py` (`1874ede` 版, 供文案对照复跑).
- 取证脚本与结果: `probe04.py`, `probe04.json`, `logs/`, `files/`.
- 摘要清单: `manifest.sha256`.

## 6. 未覆盖 / 未验证

- 全量 `uv run pytest` 需 Podman 与完整依赖, 本容器无 podman, 按 EXECUTION.md 交调用方: **未验证**.
- 并发三窗口的仓内自动化: 按工单不安排, 仍由 issue-01 run5 的一次性进程证据承担.
- 真实需求试跑, 预览视觉渲染: 不属本 issue 范围, 未做.