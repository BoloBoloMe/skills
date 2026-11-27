# milestone-07 返工轮集成检查 / run2 证据索引

- 任务标识: m07-int-2; 执行者: 里程碑集成检查会话 (未参与返工切片编写).
- 现场: 主仓库 `/home/bolo/Workspace/improve`, 分支 `improve`; 返工前顶端 `783a528` (含 IMPACT-REVIEW.md 提交); 合并提交 `68a5f09`(issue/04), `ca9f7c3`(issue/05), `c055e5e`(issue/06); 检查时 HEAD `c055e5e` (见 `head-commit.txt`); 记录提交 A2 之后只加文档行, 不改产品文件, 故检查结论对所检查代码状态成立.
- 三切片全部 `git merge --no-ff` 顺序合入, 无冲突; 工单 `- [ ] 已完成` 已在切片内勾选, 集成时无需再改.

## 1. `workflow/to-spec/tests` 回归

- 命令 (`pytest.command.txt`): `uv run --with gherkin-official pytest workflow/to-spec/tests`
- `pytest.stdout`: `collected 40 items`, `40 passed in 4.25s`; `pytest.stderr` 空; 退出码 (`pytest.exit-code.txt`) = **0**.
- 与派工预期一致 (40 passed). 平台 linux, Python 3.11.2, pytest 9.1.1, pluggy 1.7.0.

## 2. 改动 `SKILL.md` 格式检查

- 清单来源: `git diff 9e8dd1dfe92b3b446c88c2cb8fce33cb0c67a77a..HEAD --name-only` -> `changed-files.txt` (1231 个, 含归档证据树), 过滤 `SKILL.md` -> `changed-skillmd.txt`:
  1. `workflow/navigate/SKILL.md` -> `workflow/navigate/SKILL.md: OK`, exit **0**
  2. `workflow/to-spec/SKILL.md` -> `workflow/to-spec/SKILL.md: OK`, exit **0**
  3. `workflow/verify-change/SKILL.md` -> `workflow/verify-change/SKILL.md: OK`, exit **0**
  4. `docs/changes/to-spec-grilling-and-chinese-ids/evidence/m07-1bc15f6.../issue-02/check1/originals/SKILL.md` -> exit **1**, stderr `name 与目录名不一致: verify-change != originals`
- 第 4 个不是产品 skill: 它是 ISSUE-02 非作者核对留下的候选条文快照 (只读证据原件), 被归档进仓库时保留了 `originals/` 目录名, 而 frontmatter `name: verify-change` 未改, 因此 check_skill 的目录名一致性规则不适用. 它未被任何产品流程引用, 内容与当前 `workflow/verify-change/SKILL.md` 的差异仅为本次 Q4 术语三处 (对照 diff 已核). 产品改动 `SKILL.md` 清单按派工预期为上述 3 个, 全部通过.
- 口径说明: 该失败是 "证据目录里放了一份带 SKILL.md 头部的快照" 造成的误报, 不是产品条文格式缺陷; 记录在此供评审与调度方核对, 未修改该归档文件 (证据内容不改).

## 3. 合并与记录

- `merges.txt`: 合并提交与顶端列表.
- 记录提交 A2: 见本文件同目录 `../` 之外的仓库提交 `doc: milestone-07 返工集成与执行记录`.

## 未验证 / 局限

- 全量 `uv run pytest`: 容器无 Podman, 仍未验证 (同 run1).
- 本 run 只做回归与格式检查, 不作条文语义评审, 不代表用户验收.
