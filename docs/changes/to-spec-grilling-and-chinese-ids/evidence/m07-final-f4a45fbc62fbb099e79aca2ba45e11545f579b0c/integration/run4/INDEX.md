# milestone-07 返工轮四集成检查 / run4 证据索引

- 任务标识: m07-int-4; 执行者: 里程碑集成检查会话 (未参与 ISSUE-08 条文编写).
- 现场: 主仓库 `/home/bolo/Workspace/improve`, 分支 `improve`. 合并前顶端 `cc1ef59` (与来信一致); 切片 `issue/08` 顶端 `1efb0f0a984add7de223645851ec4eb849f9e603`; 合并提交 `b9cb2dbcee92e948f7d2725e275e607f1da7273b`; 记录提交 A4 `3e486d37d5caea2b5bc937bbd2c77474b50b97fb` (检查时 HEAD, 见 `head-commit.txt`).
- 合并 `--no-ff`, 无冲突; 切片内产品改动只有 `workflow/navigate/reference/VERIFICATION.md` 一行, 工单勾选已在切片内完成.

## 1. `workflow/to-spec/tests` 回归

- 命令 (`pytest.command.txt`): `uv run --with gherkin-official pytest workflow/to-spec/tests`
- `pytest.stdout`: `collected 40 items`, `40 passed in 4.13s`; `pytest.stderr` 空; 退出码 (`pytest.exit-code.txt`) = **0**. 与预期 40 passed 一致.

## 2. 改动 `SKILL.md` 格式检查

- 清单: `git diff 9e8dd1df...HEAD --name-only` -> `changed-files.txt` (1234, 含归档证据树), 过滤 -> `changed-skillmd.txt`:
  1. `workflow/navigate/SKILL.md` -> OK, exit **0**
  2. `workflow/to-spec/SKILL.md` -> OK, exit **0**
  3. `workflow/verify-change/SKILL.md` -> OK, exit **0**
  4. `docs/changes/to-spec-grilling-and-chinese-ids/evidence/m07-1bc15f6.../issue-02/check1/originals/SKILL.md` -> exit **1** (`name 与目录名不一致: verify-change != originals`): 归档的候选条文快照, 非产品条文, 与前几轮同一条误报, 未改动.
- 产品清单按预期仍为 3 个, 全部通过.

## 3. `workflow/navigate/reference/VERIFICATION.md` (非 SKILL.md, 跑 diff --check)

- 命令与结果 (`verification-diff-check.out` / `.exit.txt`): `git diff --check 9e8dd1df...HEAD -- workflow/navigate/reference/VERIFICATION.md` -> 无输出, 退出码 **0** (无空白错误).
- 实际差异 (`verification-md.diff`): 仅第 3 步一处句子替换, 把 "判据或方案依据变化须先更新权威输入并重新确认方案" 换成 "只有方法变化不改产品判据. 验证决定新增或改变时只补问相关决定并递增方案版本, 有依据的转述错误直接修正并经独立复查; 新产品判据仍回原规格维护流程, 不恢复逐版阅读或采纳整份方案." 第 3 步其余内容与第 1 步未动.
- 语义核对属评审与影响方向职责; 本 run 只留 diff 供核对.

## 未验证 / 局限

- 全量 `uv run pytest`: 容器无 Podman, 未验证 (同前几轮).
- 最终证据归档与路线图关闭由调度方做, 不在本 run 范围.
