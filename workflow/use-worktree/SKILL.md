---
name: use-worktree
description: 管理符合用户习惯的本地 Git worktree 布局:识别标准目录,选择/创建/删除/迁移 worktree,检查 dirty 状态并避免误改仓库.通常由 orchestrate 路由;仅当用户明确点名 use-worktree 或已处于 worktree 流程时直接使用.用户明确要求操作本地 git repo,创建/清理 worktree,整理 repo 布局,分支隔离或避免改错分支时走本 skill.
---

# use-worktree

## 标准布局

```text
<workspace>/<project>/
├─ <project>-<master-branch-slug>                         # main worktree / 基线 repo
├─ <project>-<source-branch-slug>-<branch-slug>
└─ ...
```

- `<project>` 优先从 `origin` 远端仓库名推断;无 `origin` 或无法推断时询问用户.
- main worktree 为 `<project>-<主分支名>`.
- linked worktree 目录名记录创建时的来源分支:`<project>-<来源分支slug>-<目标分支slug>`.
- 目录名只是创建时约定;后续 rebase/merge/upstream 变化不自动改名.

## slug 规则

使用 `scripts/slug.py` 预览.

- `/ \ : * ? " < > |` 与控制字符 -> `-`
- 空格 -> `_`
- 连续 `-` 压缩为单个 `-`
- 首尾空格/点号去除
- 保留中文/Unicode
- 每个分支 slug 最长 60 字符;超长截断为 52 字符 + `-` + SHA-1 前 7 位
- 若生成目录名与已有路径冲突:停止并询问用户指定目录名

## 硬规则

- 始终进入具体 worktree,或用 `git -C <worktree>`;不要在 workspace/project 父目录假定 Git 上下文.
- 修改前必须报告:目标 worktree,分支,HEAD,`git status --short --branch --untracked-files=all`.
- 一次任务默认只改一个 worktree;跨 worktree 对照默认只读.
- 禁止手删 `.git` 文件或 `.git/worktrees/*`;删除/清理用 `git worktree remove/prune`.
- 目标 worktree dirty(含 untracked)时停止并询问用户.
- 用户未指定 repo/worktree 时,从当前路径向上识别标准 `<workspace>/<project>/`;不确定则列信息并询问.

## 状态检查

```text
uv run python scripts/status.py <任意路径>
```

脚本只读;输出 `layout=standard|nonstandard`,项目,main worktree,每个 worktree 的分支/HEAD/dirty/stale 状态.

## 新建 worktree

1. 用 `uv run python scripts/status.py` 检查目标仓库布局.
2. 若布局标准:
   - 确认来源分支,目标分支;若未给出则询问.
   - 询问是否执行 `git fetch --all --prune`.
   - 用 `uv run python scripts/slug.py <project> <source-branch> <target-branch>` 生成目录名.
   - 若目标目录已存在但不是目标 Git worktree:停止并询问.
   - 若目标分支已存在且未被其他 worktree checkout:`git worktree add <dir> <target-branch>`,并告知用户这是 checkout 已有分支.
   - 若目标分支不存在:`git worktree add -b <target-branch> <dir> <source-branch>`.
   - 若目标分支已被其他 worktree checkout:停止并告知已有路径.
3. 若布局非标准:先询问是否迁移到标准 `<workspace>/<project>/`;没有 base 目录时可在批准后新建.

## 删除 worktree

- 只允许删除干净 worktree.
- 删除前展示路径,分支,HEAD,状态,命令,并询问 `是否执行?`.
- 执行:`git worktree remove <path>`.
- 删除后询问是否执行 `git worktree prune`;确认后再执行.

## 迁移非标准布局

支持迁移单个 main repo 或已有 sibling worktree 集合到标准布局.

迁移前必须:

- 推断或询问 `<project>`.
- 检查所有相关 worktree 均干净;任何 dirty 即停止.
- 展示 before/after 路径,移动命令,`git worktree repair <paths...>`,验证命令.
- 询问 `是否执行?`.

迁移后执行 `git worktree repair` 修复登记路径,再用 `git worktree list` 与 `uv run python scripts/status.py` 验证.

## 汇报格式

- 执行前:目标 worktree,分支,HEAD,dirty 状态,将执行的命令.
- 执行后:修改/创建/删除的路径,测试或验证命令,最终 Git 状态.
