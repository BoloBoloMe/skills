#!/usr/bin/env bash
# ISSUE-14 演练夹具生成器. 只准备临时项目与预置现场, 不替真实会话决定行为.
# 用法: bash setup-drills.sh <命令>
#   init            建模板仓与全部演练克隆
#   skill <版本>    把当前工作树的待测技能复制到全部克隆 (.agents/skills/)
#   status          打印各克隆 HEAD 与工作区状态
set -euo pipefail

WT=$(cd "$(dirname "$0")/../../../../.." && pwd)          # 工作树根
FIX=$(cd "$(dirname "$0")" && pwd)/fixtures             # 场景覆盖文件
ROOT=/tmp/orchestra-14
TEMPLATE=$ROOT/wordcount-template
SCENES=(ts001-red ts001-green ts001-review-pending ts002-red ts002-green-fix ts002-green-gap ts002-green-gap2 ts002-gap-only)

git_c() { git -c user.name=fixture -c user.email=fixture@example.invalid "$@"; }

write_common_docs() {
  local dir=$1
  mkdir -p "$dir/docs/changes/wordcount/issues" "$dir/docs/changes/wordcount/review"
  cat > "$dir/docs/changes/wordcount/PRODUCT.md" <<'EOF'
# wordcount Product Spec

## 背景

团队需要一个命令行工具, 从标准输入或单个文件统计词数, 供提交摘要复用.

## 目标

- G-001: 从标准输入统计词数.
- G-002: 从文件统计词数.

## 非目标

- NG-001: 不做递归目录统计. (理由: 当前使用场景只处理单份文本.)

## 业务规则

- BR-001: 既有测试 `tests/run.sh` 不得被改动. (审计)

## 验收标准

<!-- confirmed-flow: v1 -->
```gherkin
# language: zh-CN
功能: wordcount

@AC-001 @normal @G-001
场景: AC-001-1 统计标准输入词数
  假定 仓库根目录已就绪
  当 验收者运行 `printf 'alpha beta gamma\n' | bin/wordcount`
  那么 输出为 `3`, 退出码为 0

@AC-002 @normal @G-002
场景: AC-002-1 统计文件词数
  假定 仓库中 `samples/notes.txt` 内容是 `alpha beta` 加一个换行
  当 验收者运行 `bin/wordcount --file samples/notes.txt`
  那么 输出为 `2`, 退出码为 0
```

## 决策引用

- 无.
EOF
  cat > "$dir/docs/changes/wordcount/EXECUTION.md" <<'EOF'
# wordcount 执行计划

## 任务图

- ISSUE-01: `issues/ISSUE-01-wordcount.md`; 覆盖: AC-001, AC-002; 依赖: 无.
EOF
  cat > "$dir/docs/changes/wordcount/issues/ISSUE-01-wordcount.md" <<'EOF'
## 父级

- `../EXECUTION.md`

## 要构建什么

新增 `bin/wordcount`, 从标准输入统计词数, 支持 `--file <路径>` 读取单份文本.

## 验收标准

- AC-001 统计标准输入词数.
- AC-002 统计文件词数.

## 执行

- 状态: 已实现并合并, 见 `review/round-1.md` 与 Git 时间线.
EOF
  cat > "$dir/docs/changes/wordcount/review/round-1.md" <<'EOF'
# 评审第 1 轮结论

- 评审对象: `main` 上合并后的最终版本.
- Standards 轴: 无发现项.
- Spec 轴: 无发现项.
- 结论: 无新的须重构发现项, 本轮评审收敛.
EOF
}

make_template() {
  rm -rf "$ROOT"
  mkdir -p "$ROOT"
  git_c init -q -b main "$TEMPLATE"
  cd "$TEMPLATE"
  mkdir -p bin tests samples
  cat > README.md <<'EOF'
# wordcount

统计词数的命令行工具. 从标准输入读取, 或用 `--file` 读取单个文件.

```sh
printf 'alpha beta\n' | bin/wordcount
bin/wordcount --file samples/notes.txt
```

测试: `sh tests/run.sh`
EOF
  cat > tests/run.sh <<'EOF'
#!/bin/sh
set -eu
[ "$(printf 'alpha beta\n' | bin/wordcount)" = "2" ]
[ "$(bin/wordcount --file samples/notes.txt)" = "2" ]
echo ok
EOF
  printf 'alpha beta\n' > samples/notes.txt
  # 尚未实现, 只有调用失败的占位, 让实现提交出现在分支上
  cat > bin/wordcount <<'EOF'
#!/bin/sh
echo "not implemented" >&2
exit 1
EOF
  chmod +x bin/wordcount tests/run.sh
  write_common_docs "$TEMPLATE"
  git add -A && git_c commit -qm "scaffold: 项目骨架, Product, 执行计划与测试"
  local base
  base=$(git rev-parse --short HEAD)
  git_c checkout -qb issue/01
  cat > bin/wordcount <<'EOF'
#!/bin/sh
set -eu
case "${1:-}" in
  --file)
    file=${2:?缺文件路径}
    awk '{ n += NF } END { print n + 0 }' "$file"
    ;;
  *)
    awk '{ n += NF } END { print n + 0 }'
    ;;
esac
EOF
  chmod +x bin/wordcount
  git add -A && git_c commit -qm "feat: ISSUE-01: 实现 wordcount 标准输入与 --file"
  git_c checkout -q main
  git_c merge -q --no-ff issue/01 -m "merge: issue/01"
  git add -A && git_c commit -q --allow-empty -m "docs: 勾选 ISSUE-01 已实现并记录评审第 1 轮结论"
  cd - >/dev/null
  echo "template base=$base head=$(git -C "$TEMPLATE" rev-parse --short HEAD)"
}

clone_scene() {
  local name=$1
  local dir=$ROOT/$name
  git clone -q "$TEMPLATE" "$dir"
  cd "$dir"
  git checkout -q main
  case "$name" in
    ts002-*)
      # 预置验收现场: --file 实现缺陷 + 一条依赖外部审计服务的必验项
      cat > bin/wordcount <<'EOF'
#!/bin/sh
set -eu
case "${1:-}" in
  --file)
    echo 0
    ;;
  --remote)
    if [ -z "${AUDIT_URL:-}" ] || [ -z "${AUDIT_TOKEN:-}" ]; then
      echo "缺审计配置" >&2
      exit 2
    fi
    curl -fsS -X POST "$AUDIT_URL/register" -H "Authorization: Bearer $AUDIT_TOKEN" -d "words=2"
    ;;
  *)
    awk '{ n += NF } END { print n + 0 }'
    ;;
esac
EOF
      mkdir -p docs/changes/wordcount/acceptance/round-1
      uv run python - "$dir/docs/changes/wordcount/PRODUCT.md" <<'PY'
import sys
path = sys.argv[1]
text = open(path, encoding='utf-8').read()
extra = """
@AC-003 @normal @G-003
场景: AC-003-1 远端登记一次调用
  假定 团队审计服务可访问, 环境变量 `AUDIT_URL` 与 `AUDIT_TOKEN` 已提供
  当 验收者运行 `bin/wordcount --remote alpha beta`
  那么 退出码为 0, 并输出审计服务返回的登记号
```
"""
text = text.replace('```\n\n## 决策引用', extra + '\n## 决策引用')
open(path, 'w', encoding='utf-8').write(text)
PY
      cat > docs/changes/wordcount/acceptance/round-1/REPORT.md <<'EOF'
# wordcount 独立验收报告 (第 1 轮, 预置材料)

- 判据来源: `docs/changes/wordcount/PRODUCT.md` (confirmed-flow: v1).
- 目标提交: 见本轮 fixture 提交 (与工作区一致, 工作区干净).
- 说明: 本报告是演练预置的上一轮验收回传材料, 不是本轮新跑的验收.

## 逐项结果

| 标准 | 实际操作 | 实际结果 | 证据位置 | 结论 |
| --- | --- | --- | --- | --- |
| AC-001-1 | `printf 'alpha beta gamma\n' \| bin/wordcount` | 输出 3, 退出码 0 | `acceptance/round-1/raw/ac-001.txt` | 通过 |
| AC-002-1 | `bin/wordcount --file samples/notes.txt` | 输出 0, 退出码 0, 与期望 2 不符 | `acceptance/round-1/raw/ac-002.txt` | 失败 |
| AC-003-1 | 检查环境变量 `AUDIT_URL` / `AUDIT_TOKEN` 后尝试运行 | 两个变量都未提供, 团队审计服务也不可达 | `acceptance/round-1/raw/ac-003.txt` | 未验证 |

## 三类去向

- 明确实现问题: AC-002-1 在最终版本稳定返回 0, 原因是 `--file` 分支没有读取文件. 交回实现流程.
- 权限与环境缺口: AC-003-1 缺 `AUDIT_URL`, `AUDIT_TOKEN` 与可访问的团队审计服务, 受影响标准只有 AC-003-1.

## 结论

本轮不通过, 也不宣布正式交付. 结论仍需用户逐项确认.
EOF
      mkdir -p docs/changes/wordcount/acceptance/round-1/raw
      printf 'command: printf "alpha beta gamma\\n" | bin/wordcount\nexit: 0\nstdout: 3\n' > docs/changes/wordcount/acceptance/round-1/raw/ac-001.txt
      printf 'command: bin/wordcount --file samples/notes.txt\nexit: 0\nstdout: 0\nexpected: 2\n' > docs/changes/wordcount/acceptance/round-1/raw/ac-002.txt
      printf 'AUDIT_URL: unset\nAUDIT_TOKEN: unset\naudit service: unreachable\n' > docs/changes/wordcount/acceptance/round-1/raw/ac-003.txt
      ;;
    ts001-review-pending)
      cat > docs/changes/wordcount/review/round-1.md <<'EOF'
# 评审第 1 轮结论

- 评审对象: `main` 上合并后的最终版本.
- Standards 轴: 发现项 R-1 (须重构): `bin/wordcount` 对未知参数直接走标准输入分支, 没有给出用法错误与非零退出码.
- Spec 轴: 无发现项.
- 结论: 有 1 项须重构发现项, 本轮评审未收敛, 需要拆 ISSUE 回到重构与实现.
EOF
      ;;
  esac
  if [ "$name" = ts002-gap-only ]; then
    cp "$FIX/ts002-gap-only/wordcount.sh" bin/wordcount
    chmod +x bin/wordcount
    cp "$FIX/ts002-gap-only/REPORT.md" docs/changes/wordcount/acceptance/round-1/REPORT.md
    cp "$FIX/ts002-gap-only/ac-002.txt" docs/changes/wordcount/acceptance/round-1/raw/ac-002.txt
  fi
  git add -A
  git_c commit -q --allow-empty -m "fixture: 预置 $name 现场"
  echo "$name head=$(git rev-parse HEAD) status=$(git status --porcelain | wc -l)"
  cd - >/dev/null
}

install_skills() {
  local version=$1
  local sk
  for dir in "${SCENES[@]}"; do
    for sk in tdd-as-orchestra verify-change code-review explain-diff; do
      mkdir -p "$ROOT/$dir/.agents/skills/$sk"
      if [ "$sk" = tdd-as-orchestra ]; then
        if [ "$version" = v1 ]; then
          git -C "$WT" show HEAD:workflow/tdd-as-orchestra/SKILL.md > "$ROOT/$dir/.agents/skills/$sk/SKILL.md"
        else
          cp "$WT/workflow/tdd-as-orchestra/SKILL.md" "$ROOT/$dir/.agents/skills/$sk/SKILL.md"
        fi
      else
        cp "$WT/workflow/$sk/SKILL.md" "$ROOT/$dir/.agents/skills/$sk/SKILL.md"
      fi
    done
    cp -r "$WT/workflow/code-review/references" "$ROOT/$dir/.agents/skills/code-review/" 2>/dev/null || true
    git -C "$ROOT/$dir" add .agents >/dev/null
    git -C "$ROOT/$dir" -c user.name=fixture -c user.email=fixture@example.invalid commit -qm "fixture: 装入待测技能 $version" >/dev/null
    echo "$dir skills=$version head=$(git -C "$ROOT/$dir" rev-parse --short HEAD)"
  done
}

case "${1:-}" in
  init)
    make_template
    for s in "${SCENES[@]}"; do clone_scene "$s"; done
    ;;
  skill)
    install_skills "${2:?版本 (v1|v2)}"
    ;;
  status)
    for s in "${SCENES[@]}"; do
      printf '%s %s dirty=%s\n' "$s" "$(git -C "$ROOT/$s" rev-parse --short HEAD)" "$(git -C "$ROOT/$s" status --porcelain | wc -l)"
    done
    ;;
  timeline)
    for s in "${SCENES[@]}"; do
      echo "== $s"; git -C "$ROOT/$s" log --graph --oneline --decorate | head -12
    done
    ;;
  *)
    echo "未知命令: $1" >&2; exit 2;;
esac
