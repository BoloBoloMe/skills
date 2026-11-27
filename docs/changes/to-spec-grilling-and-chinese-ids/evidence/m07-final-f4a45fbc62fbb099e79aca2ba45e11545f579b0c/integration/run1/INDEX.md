# milestone-07 集成检查 / run1 证据索引

- 任务标识: m07-int-1; 执行者: 本里程碑集成与集成检查会话; 时间起 `started-at.txt`.
- 现场: 主仓库 `/home/bolo/Workspace/improve`, 分支 `improve`; 合并前顶端 `775b5a2`; 合并提交 `9eedb3a`(issue/01), `f9bfe71`(issue/02), `1dfc38a`(issue/03); 记录提交 A `1bc15f6` (检查时 HEAD, 见 `head-commit.txt`).
- 三切片全部 `git merge --no-ff` 顺序合入, 无冲突; 合并后工作树改动仅工单勾选与 EXECUTION.md 记录 (提交 A).

## a. `workflow/to-spec/tests` 回归

- 命令 (`pytest.command.txt`): `uv run --with gherkin-official pytest workflow/to-spec/tests`
- 输出 `pytest.stdout`: `collected 39 items`, `39 passed in 3.62s`; `pytest.stderr` 空; 退出码 `pytest.exit-code.txt` = **0**.
- 平台: linux, Python 3.11.2, pytest 9.1.1, pluggy 1.7.0, rootdir `/home/bolo/Workspace/improve`, configfile `pytest.ini`.

## b. 改动 `SKILL.md` 格式检查

- 清单来源: `git diff 775b5a2..HEAD --name-only` -> `changed-files.txt` (16 个文件), 过滤 `SKILL.md` -> `changed-skillmd.txt`:
  - `workflow/navigate/SKILL.md`
  - `workflow/to-spec/SKILL.md`
  - `workflow/verify-change/SKILL.md`
- 逐个 `uv run python general/writing-for-llm/check_skill.py <路径>`; 每条命令/输出/stderr/退出码在 `check-skill/<文件>.{command.txt,stdout,stderr,exit-code.txt}`, 汇总 `check-skill/results.txt`:
  - 三个文件均输出 `<路径>: OK`, stderr 空, 退出码 **0**.

## c. 编号/历史范围审计 (规则12)

- 报告: `audit-renumbering.md`. 范围 `182ff18..HEAD`, 对象 `workflow/` 与 `general/`.
- 原始与中间产物: `audit-full-changed-files.txt` (41 文件), `audit-diff-workflow-general.patch` (798 行), `audit-rg-hits.txt` (755 行旧编号命中), `audit-other-hits.txt` / `audit-old-entry-forms.txt` / `audit-rule-like-lines.txt` / `audit-added-lines-old-ids.txt` / `audit-m01-nine-files.txt`, 退出码 `audit-rg-exit.txt`.
- 结论: **无新违规**; 命中全归既有例外 (Gherkin 标签 / ISSUE 文件名 / milestone 与历史引用 / 无关同形); milestone-01 的 9 文件汉化保留未回退.

## d. 安装目录只读摘要 (实施后)

- 命令: `find ~/.agents/skills -type f | sort | xargs sha256sum`, 摘要 `../post-impl-snapshot/skills-manifest.sha256` (231 行), 取时 `../post-impl-snapshot/taken-at.txt`.
- 与 `../pre-impl-snapshot/skills-manifest.sha256` (231 行) 比对: 原始清单仅路径前缀写法不同 (相对 `./` vs 绝对), 归一化后 `diff` 退出码 **0**, 0 行差异. 详见 `../post-impl-snapshot/COMPARE.md`.
- 结论: 无差异, 未触碰已安装技能.

## 未验证 / 局限

- 全量 `uv run pytest` (仓库 `pytest.ini`) 未验证: 容器无 Podman (`podman: command not found`), 完成定义要求的隔离环境不具备.
- 本 run 只做工程检查与范围审计, 不作条文语义评审, 不代表用户验收.
