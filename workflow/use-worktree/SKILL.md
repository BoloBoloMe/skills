---
name: use-worktree
description: Git worktree 布局识别, 创建, 删除, 迁移, 安全检查流程.
disable-model-invocation: true
---

# use-worktree

开始前, 调用 `domain-awareness` skill 只读感知当前工作目录的领域模型.

## 标准布局

```text
<workspace>/<project>/
├─ <project>-<master-branch-slug>                         # main worktree / 基线 repo
├─ <project>-<source-branch-slug>-<branch-slug>
└─ ...
```

- `<project>` 优先从 `origin` 远端仓库名推断; 无 `origin` 或无法推断时询问我.
- main worktree 为 `<project>-<主分支名>`.
- linked worktree 目录名记录创建时的来源分支: `<project>-<来源分支 slug>-<目标分支 slug>`.
- 目录名只是创建时约定; 后续 rebase/merge/upstream 变化不自动改名.

## slug 规则

使用 `scripts/slug.py` 预览 (脚本路径解析见硬规则).

- `/ \ : * ? " < > |` 与控制字符 -> `-`
- 空格 -> `_`
- 连续 `-` 压缩为单个 `-`
- 首尾空格/点号去除
- 保留中文/Unicode
- 每个分支 slug 最长 60 字符; 超长截断为 52 字符 + `-` + SHA-1 前 7 位
- 若生成目录名与已有路径冲突: 停止并询问我指定目录名

## 硬规则

- Git 操作始终进入具体 worktree, 或用 `git -C <worktree>`; 不在 workspace/project 父目录假定 Git 上下文.
- 脚本 (`scripts/slug.py`, `scripts/status.py`) 以本 SKILL.md 所在目录为基准解析, 调用时换算为绝对路径, 从任意 cwd 运行, 不受上一条约束.
- 修改前必须报告: 目标 worktree, 分支, HEAD, `git status --short --branch --untracked-files=all`.
- 一次任务默认只改一个 worktree; 跨 worktree 对照默认只读.
- 禁止手删 `.git` 文件或 `.git/worktrees/*`; 删除/清理用 `git worktree remove/prune`.
- 目标 worktree dirty (含 untracked) 时停止并询问我.
- 我未指定 repo/worktree 时, 从当前路径向上识别标准 `<workspace>/<project>/`; 不确定则列信息并询问.

## 状态检查

```text
uv run python scripts/status.py <任意路径>
```

脚本只读; 输出 `layout=standard|nonstandard`, 项目, main worktree, 每个 worktree 的分支/HEAD/dirty/stale 状态.

## 新建 worktree

1. 用 `uv run python scripts/status.py <目标路径>` 检查目标仓库布局.
2. 若布局标准:
   - 确认来源分支, 目标分支; 未给出则询问.
   - 询问是否执行 `git fetch --all --prune`.
   - 用 `uv run python scripts/slug.py <project> <source-branch> <target-branch>` 生成目录名.
   - 若目标分支已存在且未被其他 worktree checkout: `git worktree add <dir> <target-branch>`, 并告知我这是 checkout 已有分支.
   - 若目标分支不存在: `git worktree add -b <target-branch> <dir> <source-branch>`.
   - 若目标分支已被其他 worktree checkout: 停止并告知已有路径.
3. 若布局非标准: 先询问是否迁移到标准 `<workspace>/<project>/`; 没有 base 目录时可在批准后新建.

## 删除 worktree

- 按硬规则报告后, 询问 `是否执行?`.
- 执行: `git worktree remove <path>`.
- 删除后询问是否执行 `git worktree prune`; 确认后再执行.

## 迁移非标准布局

支持迁移单个 main repo 或已有 sibling worktree 集合到标准布局.

迁移前必须:

- 推断或询问 `<project>`.
- 检查涉及的所有 worktree 均干净, 不限于当前目标; 任一 dirty 即停止 (硬规则).
- 展示 before/after 路径, 移动命令 (以平台无关方式表述), `git worktree repair <paths...>`, 验证命令.
- 询问 `是否执行?`.

迁移后执行 `git worktree repair` 修复登记路径, 再用 `git worktree list` 与 `uv run python scripts/status.py` 验证.

## 汇报格式

- 执行后: 修改/创建/删除的路径, 测试或验证命令, 最终 Git 状态.
