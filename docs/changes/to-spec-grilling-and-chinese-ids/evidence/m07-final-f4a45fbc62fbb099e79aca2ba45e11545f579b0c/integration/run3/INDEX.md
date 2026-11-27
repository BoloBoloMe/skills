# milestone-07 返工轮三集成检查 / run3 证据索引

- 任务标识: m07-int-3; 执行者: 里程碑集成检查会话 (未参与 ISSUE-07 条文编写).
- 现场: 主仓库 `/home/bolo/Workspace/improve`, 分支 `improve`. 合并前顶端 `92e146e` (来信写 `6cc9417`; 差额是本轮要求先提交的工单提交 "doc: milestone-07 返工工单 ISSUE-07", 属预期前移). 合并提交 `5bc32d2` (merge: issue/07, 切片顶端 `8e776be`); 记录提交 A3 `de3b589` (检查时 HEAD, 见 `head-commit.txt`).
- 合并策略 `--no-ff`, 无冲突; 工单 `- [ ] 已完成` 已在切片内勾选.

## 1. `workflow/to-spec/tests` 回归

- 命令 (`pytest.command.txt`): `uv run --with gherkin-official pytest workflow/to-spec/tests`
- `pytest.stdout`: `collected 40 items`, `40 passed in 4.08s`; `pytest.stderr` 空; 退出码 (`pytest.exit-code.txt`) = **0**.
- 与预期 40 passed 一致. 派工预期还写了 50 subtests, 但本机 pytest 输出没有 subtest 汇总行 (本仓库未启用 pytest-subtests 插件时子测试以断言计); 实际只有 "40 passed" 一行, 不与预期冲突, 但无法在这里核对 50 这个数.
- 平台 linux, Python 3.11.2, pytest 9.1.1, pluggy 1.7.0.

## 2. 改动 `SKILL.md` 格式检查

- 清单来源: `git diff 9e8dd1dfe92b3b446c88c2cb8fce33cb0c67a77a..HEAD --name-only` -> `changed-files.txt` (1232 个, 含归档证据树), 过滤 `SKILL.md` -> `changed-skillmd.txt`:
  1. `workflow/navigate/SKILL.md` -> `workflow/navigate/SKILL.md: OK`, exit **0**
  2. `workflow/to-spec/SKILL.md` -> `workflow/to-spec/SKILL.md: OK`, exit **0**
  3. `workflow/verify-change/SKILL.md` -> `workflow/verify-change/SKILL.md: OK`, exit **0**
  4. `docs/changes/to-spec-grilling-and-chinese-ids/evidence/m07-1bc15f6.../issue-02/check1/originals/SKILL.md` -> exit **1**, stderr `name 与目录名不一致: verify-change != originals`
- 第 4 个仍非产品 skill: 它是归档的候选条文快照 (`originals/` 目录名与 frontmatter `name: verify-change` 不符), 未被任何产品流程引用. 与 run2 同一条误报, 未修改归档文件 (证据内容不改). 产品清单按预期仍是 3 个, 全部通过.

## 未验证 / 局限

- 全量 `uv run pytest`: 容器无 Podman, 未验证 (同 run1/run2).
- 本 run 只做回归与格式检查, 不作条文语义评审, 不代表用户验收.
