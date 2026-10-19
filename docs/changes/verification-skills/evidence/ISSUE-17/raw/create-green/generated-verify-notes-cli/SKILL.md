---
name: verify-notes-cli
description: notes-cli 端到端验证配方, 用隔离数据目录实跑 add 与 show 并留存证据
disable-model-invocation: true
---

# notes-cli 验证配方

判据唯一来源是 `docs/PRODUCT.md` (状态: 已确认, 2026-10-20). 本配方只说明怎么跑, 怎么取证; 通过与否按 `PRODUCT.md` 的原文判断. 源码现状不能替代产品判据.

## 覆盖范围

| 功能 | 入口 | `PRODUCT.md` 判据 | 本配方小节 |
| --- | --- | --- | --- |
| 查看笔记 (空数据) | `./notes.sh show` | 输出 `(empty)`, 退出码 0 | 入口 1 |
| 记录笔记 | `./notes.sh add <正文>` | 退出码 0; 输出 `added: <正文>`; 之后 `show` 在列表末尾看到这条正文 | 入口 2 |
| 查看笔记 (有数据) | `./notes.sh show` | 每行 `<序号>\t<正文>`, 序号从 1 连续递增, 顺序与实际记录一致 | 入口 3 |

排除项:

- `./notes.sh export <path>` 是 `PRODUCT.md` 明确的非目标, 本配方不执行, 也不为它取证.
- `./notes.sh status` 只用于共用规则里的只读版本/路径检查, 它不是本轮通过判据.
- `add` 空正文的用法错误, 含制表符或换行的正文, 并发写入: `PRODUCT.md` 未定义, 不在本轮范围.

## 共用规则

### 只读检查

这是纯 CLI, 没有常驻进程, 不监听端口. 不要找端口或 PID, 也不要后台启动 `notes.sh`.

开工前只读确认:

```bash
cd /tmp/orchestra-17/proj-create
test -x notes.sh
./notes.sh status
```

期望: 输出 `notes-cli 0.2.0`, 下一行 `data_path:` 指向数据文件, 退出码 0. 版本号是现场观察值, 不是通过判据; 若版本不是 0.2.0, 记录实际值后继续按 `PRODUCT.md` 的判据跑.

### 隔离数据, 不碰项目里的真实笔记

本配方用 `NOTES_DATA` 指向 `/tmp` 下的临时文件. 这是 README 声明的数据路径开关, 只改数据落点, 不改产品代码; `status` 会打印实际路径, 用它确认隔离生效.

硬规则:

- 本配方所有 `add` / `show` 都必须带已导出的 `NOTES_DATA`.
- 不要运行不带 `NOTES_DATA` 的 `./notes.sh add`, 否则会写项目内 `data/items.txt`.
- 不要删除或改写项目内已有的 `data/items.txt`; 本次验证不需要碰它.
- 不修改 `notes.sh`, `README.md`, `docs/`, 测试或配置; 不安装工具链.

### 取证

每条命令的标准输出, 标准错误, 退出码都落到 `$EVID/<用例名>.out|.err|.code`. 断言命令的结果落到 `$EVID/<用例名>.check`. 最后生成 `summary.txt`. 证据目录在临时运行目录内, 清理前必须打印或抄录到交付报告.

### 清理

清理只删本次临时目录 `$RUN`, 保留 `.agents/skills/verify-notes-cli/`. 清理后必须用 `git status --porcelain` 和 `git diff --stat` 对照改动范围.

## 准备

从这一节开始按顺序执行, 不要跳节; 中途换了 shell 就从准备段重来, 否则空数据用例会失真.

```bash
PROJ=/tmp/orchestra-17/proj-create
RUN=/tmp/verify-notes-cli-run
rm -rf "$RUN"
mkdir -p "$RUN/evidence"
EVID="$RUN/evidence"
export NOTES_DATA="$RUN/items.txt"
cd "$PROJ"
set +e

./notes.sh status >"$EVID/status.out" 2>"$EVID/status.err"
echo $? >"$EVID/status.code"
cat "$EVID/status.out"
test "$(cat "$EVID/status.code")" = 0
grep -Fx "data_path: $NOTES_DATA" "$EVID/status.out"
```

期望: `status.code` 为 `0`; `status.out` 含 `notes-cli 0.2.0`, 且 `data_path:` 正好是 `$RUN/items.txt`. 最后一条 `grep` 退出码 0, 证明隔离数据路径生效.

`$RUN` 是新建的空目录, `$RUN/items.txt` 此时不存在, 满足"从空数据启动".

## 入口 1: 空数据查看

前置: 准备段已执行, `$RUN/items.txt` 不存在或为空.

```bash
cd /tmp/orchestra-17/proj-create
RUN=/tmp/verify-notes-cli-run; EVID="$RUN/evidence"; export NOTES_DATA="$RUN/items.txt"

set +e
./notes.sh show >"$EVID/show-empty.out" 2>"$EVID/show-empty.err"
rc=$?
echo "$rc" >"$EVID/show-empty.code"

cat "$EVID/show-empty.out"
{
  test "$rc" = 0
  grep -qFx '(empty)' "$EVID/show-empty.out"
  test ! -s "$EVID/show-empty.err"
} >"$EVID/show-empty.check" 2>&1
echo "check_exit=$?"
```

期望: `show-empty.out` 只有一行 `(empty)`; `show-empty.code` 为 `0`; `show-empty.err` 为空; `show-empty.check` 里没有报错, 最后一行 `check_exit=0`.

如果 `check_exit` 不是 0, 把 `$EVID/show-empty.check` 原文留下, 判为未通过, 继续跑后面的入口以便一次收齐证据.

## 入口 2: 记录一条笔记

前置: 入口 1 已跑完, 数据文件仍为空.

```bash
cd /tmp/orchestra-17/proj-create
RUN=/tmp/verify-notes-cli-run; EVID="$RUN/evidence"; export NOTES_DATA="$RUN/items.txt"

TEXT='第一条笔记'
set +e
./notes.sh add "$TEXT" >"$EVID/add-1.out" 2>"$EVID/add-1.err"
rc=$?
echo "$rc" >"$EVID/add-1.code"

cat "$EVID/add-1.out"
{
  test "$rc" = 0
  grep -qFx "added: $TEXT" "$EVID/add-1.out"
  test ! -s "$EVID/add-1.err"
} >"$EVID/add-1.check" 2>&1
echo "check_exit=$?"
```

期望: `add-1.out` 只有一行 `added: 第一条笔记`; `add-1.code` 为 `0`; `add-1.err` 为空; `check_exit=0`.

紧接着确认这条正文出现在列表末尾:

```bash
cd /tmp/orchestra-17/proj-create
RUN=/tmp/verify-notes-cli-run; EVID="$RUN/evidence"; export NOTES_DATA="$RUN/items.txt"

set +e
./notes.sh show >"$EVID/show-after-add-1.out" 2>"$EVID/show-after-add-1.err"
rc=$?
echo "$rc" >"$EVID/show-after-add-1.code"
printf '1\t第一条笔记\n' >"$EVID/show-after-add-1.expected"

cat -T "$EVID/show-after-add-1.out"
{
  test "$rc" = 0
  diff -u "$EVID/show-after-add-1.expected" "$EVID/show-after-add-1.out"
} >"$EVID/show-after-add-1.check" 2>&1
echo "check_exit=$?"
```

期望: `check_exit=0`; `cat -T` 显示 `1^I第一条笔记` (`^I` 表示真实的制表符, 不是两个字符); 列表最后一行就是刚加的正文.

## 入口 3: 多条笔记的编号与顺序

前置: 入口 2 已通过, 当前恰有 1 条笔记.

再追加两条, 最后一次性核对完整列表:

```bash
cd /tmp/orchestra-17/proj-create
RUN=/tmp/verify-notes-cli-run; EVID="$RUN/evidence"; export NOTES_DATA="$RUN/items.txt"

add_and_check() {
  n=$1; text=$2
  set +e
  ./notes.sh add "$text" >"$EVID/add-$n.out" 2>"$EVID/add-$n.err"
  rc=$?
  echo "$rc" >"$EVID/add-$n.code"
  {
    test "$rc" = 0
    grep -qFx "added: $text" "$EVID/add-$n.out"
    test ! -s "$EVID/add-$n.err"
  } >"$EVID/add-$n.check" 2>&1
  echo "add-$n check_exit=$?"
}

add_and_check 2 '第二条笔记'
add_and_check 3 '第三条笔记'

set +e
./notes.sh show >"$EVID/show-final.out" 2>"$EVID/show-final.err"
rc=$?
echo "$rc" >"$EVID/show-final.code"
printf '1\t第一条笔记\n2\t第二条笔记\n3\t第三条笔记\n' >"$EVID/show-final.expected"

cat -T "$EVID/show-final.out"
{
  test "$rc" = 0
  diff -u "$EVID/show-final.expected" "$EVID/show-final.out"
  test ! -s "$EVID/show-final.err"
  test "$(wc -l <"$NOTES_DATA")" = 3
} >"$EVID/show-final.check" 2>&1
echo "show-final check_exit=$?"
```

期望: 两次 `add` 的 `check_exit=0`; `show-final check_exit=0`; `cat -T` 依次显示:

```
1^I第一条笔记
2^I第二条笔记
3^I第三条笔记
```

这同时证明序号从 1 连续递增, 顺序与实际记录一致, 每行是 `<序号>` + 制表符 + `<正文>`.

## 汇总证据

```bash
cd /tmp/orchestra-17/proj-create
RUN=/tmp/verify-notes-cli-run; EVID="$RUN/evidence"

{
  echo "=== status ==="; cat "$EVID/status.out"; echo "status_exit=$(cat "$EVID/status.code")"
  for name in show-empty add-1 show-after-add-1 add-2 add-3 show-final; do
    echo "=== $name stdout ==="; cat "$EVID/$name.out"
    echo "=== $name code ==="; cat "$EVID/$name.code" 2>/dev/null || echo "(no code file)"
    echo "=== $name err ==="; cat "$EVID/$name.err" 2>/dev/null || echo "(no err file)"
    echo "=== $name check ==="; cat "$EVID/$name.check" 2>/dev/null || echo "(no check file)"
  done
  echo "=== git status ==="; git status --porcelain
  echo "=== git diff stat ==="; git diff --stat
} >"$EVID/summary.txt"

cat "$EVID/summary.txt"
```

交付报告里贴 `summary.txt` 的关键输出, 并写明 `$RUN` 的绝对路径. 证据在清理后会删除, 先抄录再清理.

## 清理与范围对照

```bash
cd /tmp/orchestra-17/proj-create
RUN=/tmp/verify-notes-cli-run

rm -rf "$RUN"
test ! -e "$RUN" && echo "temp_removed=yes"

echo "=== git status --porcelain ==="
git status --porcelain
echo "=== git diff --stat ==="
git diff --stat
```

期望:

- `temp_removed=yes`.
- `git status --porcelain` 只出现 `.agents/skills/verify-notes-cli/` (未跟踪) 或为空, 不得出现 `data/`, `notes.sh`, `README.md`, `docs/` 等改动.
- `git diff --stat` 为空.

若出现范围外改动, 停下报告, 不要用 `git checkout` 或删除文件掩盖; 由用户决定如何处理.

## 未验证与边界

- 本配方不使用项目默认数据路径 `data/items.txt`, 因此不检验默认路径下的真实笔记内容. 这是有意的隔离, 避免测试写入污染用户数据; 默认路径只在 `status` 里只读观察.
- 未验证 `export`: 本轮非目标.
- 未验证空正文, 特殊字符, 并发写入: `PRODUCT.md` 未定义.
- 若 `notes.sh` 在准备段就无法执行, 记录报错原文, 把受影响入口标为未验证, 不要安装工具或改脚本绕过.
