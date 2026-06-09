# 文件范围策略

所有文件路径必须是 POSIX 风格的 workspace-relative path。

## 禁止路径

以下路径非法：

- 绝对路径；
- 父目录穿越；
- 反斜杠路径；
- 前后有空白的路径；
- 指向 workspace 根目录的路径；
- 解析后逃逸 workspace 的路径。

## glob 语义

- `*` 只匹配一个路径段。
- `?` 只匹配一个路径段中的单个字符。
- `**` 作为完整路径段时，匹配零个或多个路径段。
- `src/*` 匹配 `src/a.py`，不匹配 `src/a/b.py`。
- `src/**` 匹配 `src/` 下任意深度文件。

## 双重门禁

1. 修改前：planned files 必须在 `blueprint.execution_contract.allowed_files` 内，且不触犯 prohibited files / scope。
2. 完成前：actual changed files 必须仍在允许范围内。

unit 执行时还必须满足 unit 自身的收窄范围。

## 脚本输入来源

`check_allowed_files.py` 支持以下来源：

- `--planned-file`：显式 planned files 文本。
- `--planned-from-plan execution/plan@vN|execution/runbook@vN`：从 Plan / Runbook 的 `unit_plans[].planned_files` 汇总。
- `--changed-file`：显式 changed files 文本。
- `--changed-from-git --repo-root . --git-base HEAD --include-untracked`：从 git 收集实际变更。

`--write-snapshot snapshot.txt` 可在执行前记录已有变更；完成后用 `--exclude-existing-before snapshot.txt` 从 git changed files 中扣除执行前既有变更，避免把无关工作区改动算入本次 close gate。
