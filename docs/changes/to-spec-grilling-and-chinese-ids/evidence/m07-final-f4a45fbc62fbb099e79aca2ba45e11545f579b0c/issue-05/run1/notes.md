# ISSUE-05 术语统一 证据记录 (run1)

任务标识 m07-rw-05. 分支 `issue/05`, 基点 `1874ede`. 改动类型: 术语统一, 语义零变化.

## 1. 依据与引用核对

- 工单: `docs/changes/to-spec-grilling-and-chinese-ids/issues/ISSUE-05-verifychange-terms-q4.md` (全文生效).
- 报告线索: `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/integration/review1/SPEC.md:151` 行 Q4 条目, 引用位置为 `verify-change/SKILL.md:45,51,79`.
- 现场核对结果: 改前 `grep -n '设计方式' workflow/verify-change/SKILL.md` 恰好命中 45,51,79 三行, 与报告引用一致, 无第四处.
- 术语基准: 同文件 `:11` 的两种调用方式名为 **设计验证方案** / **执行验证方案**; `:18` 的 H2 标题为 `## 设计验证方案`. 故统一到 **设计验证方案**.

## 2. 逐处对照 (位置 / 原表述 / 新表述)

| 行 | 所在节 | 原句片段 | 新句片段 | 语义判断 |
| --- | --- | --- | --- | --- |
| 45 | 方案修订 | 只按设计方式补问并入账受影响的决定 | 只按设计验证方案补问并入账受影响的决定 | 指向 `:18` 设计验证方案一节的补问规则, 指代对象不变, 要求不变 |
| 51 | 执行验证方案 第1步 | 先回设计方式按 [方案修订](#方案修订) 分流 | 先回设计验证方案按 [方案修订](#方案修订) 分流 | 同上; `#方案修订` 是 `:18` 节下的 H2, 归属关系不变 |
| 79 | 边界 | 方案需要变更时先回设计方式. | 方案需要变更时先回设计验证方案. | 同上 |

判定: 三处均为对 `:18` 节的指代, 换成与标题一致的名称后, 条件, 动作, 禁止项, 流程顺序全部不变.

## 3. 语义零变化的形式证明

`term-normalized-diff.txt`: 逐行比对 `HEAD` 版与工作区版 (均 79 行).
- 变更行号只有 `[45, 51, 79]`, 无其他行.
- 三行各自满足 "新行 == 旧行把 `设计方式` 替换为 `设计验证方案` 后的字符串", 逐字节一致.
- 新文件 `设计方式` 计数 0, 旧文件 3.
- `diff-numstat.txt`: `3 3 workflow/verify-change/SKILL.md`, 无第二文件 (见 `changed-files-pre-commit.txt`, 提交前只有这一个文件改动).

## 4. 检查命令与退出码

| 命令 | 结果 | 原件 |
| --- | --- | --- |
| 改前 `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` | OK, exit 0 | `pre/check-skill.txt` (用 `git show HEAD:...` 还原的副本, 目录名保持 `verify-change` 以通过 name 检查) |
| 改后 同命令 | OK, exit 0 | `check-skill.txt` |
| `git diff --numstat` | `3 3` | `diff-numstat.txt` |
| 逐行归一比对 | 无术语以外改动 | `term-normalized-diff.txt` |

环境: `environment.txt`.

## 5. 未覆盖范围 (允许范围外, 未改)

工单允许范围只含 `workflow/verify-change/SKILL.md`. 现场仍有 Q4 同类的 `设计方式` 用法, 均在范围外, 本 issue 未改, 仅记录供后续按新工单处理:

- `workflow/navigate/SKILL.md:71`
- `workflow/verification-contract/SKILL.md:15`
- `README.md:65`

其中 `workflow/verification-contract/` 不在本变更里程碑的允许范围内, `README.md` 与 `workflow/navigate/SKILL.md` 属 ISSUE-03 范围 (该切片已交付).

## 6. 未验证与限制

- 未运行候选 skill, 未试跑真实需求 (本 issue 交付物是术语, 验证契约为格式检查 + diff 核对).
- 未执行全量 `uv run pytest`: 属父级完成定义, 本容器无 Podman, 与 ISSUE-01 记录同因.