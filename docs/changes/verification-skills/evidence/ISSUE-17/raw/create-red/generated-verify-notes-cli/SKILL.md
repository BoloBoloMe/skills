---
name: verify-notes-cli
description: notes-cli 记录与查看笔记的真实入口验证配方
disable-model-invocation: true
---

# verify-notes-cli

判据来源只有一份: 目标项目的 `docs/PRODUCT.md` (状态已确认). 本配方与它冲突时以它为准.

## 本次覆盖

| 功能 | 真实入口 | PRODUCT 判据 |
| --- | --- | --- |
| 记录笔记 | `./notes.sh add <正文>` | 退出码 0; 输出 `added: <正文>`; 之后 `show` 在列表末尾看到这条正文 |
| 查看笔记 | `./notes.sh show` | 每行 `<序号>\t<正文>`, 序号从 1 连续递增, 顺序与记录一致; 无记录时输出 `(empty)` 且退出码 0 |

排除:
- `export`: `PRODUCT.md` 明确列为本轮非目标, 不运行, 不判定.
- `status`: `PRODUCT.md` 没有它的判据, 只在共用规则里当只读实例检查, 不判通过/失败.
- 空正文, 编码, 并发, 大文件, 数据文件损坏: 本轮判据未定义, 不验.

## 共用规则

1. 隔离数据: 每条验证命令都设 `NOTES_DATA`, 指向临时目录里的文件; 不碰仓库里的 `data/items.txt`.
2. 从空数据起步: 先保证临时数据文件不存在, 再跑第一条 `show`.
3. 只读实例检查: 用 `./notes.sh status` 确认工具存在, 版本和实际数据路径; 它不产出功能判据.
4. 只走真实入口: 判据看 `./notes.sh` 的 stdout/stderr 与退出码. 读数据文件只作辅助证据, 不替代命令输出.
5. 取证: 每条命令用同目录的 `capture.sh` 执行, 证据落在 `$EVIDENCE/<label>.log`, 含命令原文, 退出码, 原始输出.
6. 清理: 结束时删掉临时数据目录, 并确认项目里没有新增改动.

执行顺序: 准备 → 入口 2a (空数据) → 入口 1 (记录) → 入口 2b (列表) → 清理. 下面所有命令在同一个 shell 里连续执行; 换了会话就要重做"准备". `capture.sh` 会原样返回被测命令的退出码, shell 开了 `set -e` 时先 `set +e`.

## 准备 (每个验证会话一次)

```bash
set +e
cd /tmp/orchestra-17/proj-create
WORK=$(mktemp -d /tmp/verify-notes-cli-data.XXXXXX)
export NOTES_DATA=$WORK/items.txt
EVIDENCE=$(mktemp -d /tmp/verify-notes-cli-evidence.XXXXXX)
export EVIDENCE
CAP=.agents/skills/verify-notes-cli/capture.sh
rm -f "$NOTES_DATA"            # 空数据起点
echo "WORK=$WORK"; echo "EVIDENCE=$EVIDENCE"
```

期望: 打印两个临时目录路径; `NOTES_DATA` 指向的文件此时不存在.

只读实例检查:

```bash
"$CAP" status -- ./notes.sh status
```

期望: 退出码 0; 输出 `notes-cli 0.2.0` 和 `data_path: <上面的 $NOTES_DATA>`.

## 入口 1: 记录笔记

前置: `NOTES_DATA` 指向不存在或空文件.

```bash
"$CAP" add-1 -- ./notes.sh add "买牛奶"
"$CAP" add-2 -- ./notes.sh add "写周报"
"$CAP" add-3 -- ./notes.sh add "买牛奶"
```

期望, 三条都一样:
- 退出码 0;
- stdout 恰好一行 `added: <正文>`, 正文与传入一致 (含重复的"买牛奶", 重复不报错);
- 证据: `$EVIDENCE/add-1.log`, `add-2.log`, `add-3.log`.

注意: 正文含空格时必须整体加引号; 不加引号只会记录第一个词. 这是操作要求, 不额外算判据.

辅助证据 (不替代判据):

```bash
"$CAP" data-raw -- bash -c 'cat "$NOTES_DATA"'
```

期望: 三行正文, 顺序为 买牛奶, 写周报, 买牛奶.

入口 1 的"之后 show 能看到"一条与入口 2 共用下面的列表检查, 必须在入口 2 跑完后才能判入口 1 通过.

## 入口 2: 查看笔记

### 2a 空数据

前置: `NOTES_DATA` 指向的文件不存在, 或大小为 0.

```bash
rm -f "$NOTES_DATA"
"$CAP" show-empty -- ./notes.sh show
```

期望: 退出码 0; stdout 恰好一行 `(empty)`; 证据 `$EVIDENCE/show-empty.log`.

注意: 这一步会清空数据, 按上面的执行顺序排在入口 1 之前; 若已经做过入口 1, 就重跑"准备"再执行本步.

### 2b 有记录时的列表

前置: 入口 1 已按顺序添加 买牛奶, 写周报, 买牛奶.

```bash
"$CAP" show-3 -- ./notes.sh show
"$CAP" show-3-fields -- bash -c './notes.sh show | awk -F"\t" "{print NR\" fields=\"NF}"'
```

期望:
- `show-3` 退出码 0; stdout 恰好三行, 依次为:

```text
1	买牛奶
2	写周报
3	买牛奶
```

- 每行由序号 + 一个制表符 + 正文组成; 序号从 1 连续递增, 顺序与添加顺序一致, 重复正文照样占一行;
- `show-3-fields` 每行输出 `N fields=2`, 证明分隔符是制表符而不是空格;
- 证据: `$EVIDENCE/show-3.log`, `$EVIDENCE/show-3-fields.log`.

只看单行结尾的辅助检查 (可选):

```bash
"$CAP" show-3-single -- bash -c './notes.sh show | grep -c "^[0-9][0-9]*	"'
```

期望: 输出 `3`, 退出码 0.

## 判通过

| 判据 | 对应证据 | 结论 |
| --- | --- | --- |
| add 退出码 0 且输出 `added: <正文>` | add-1/2/3.log | |
| show 在列表末尾看到刚加的正文 | show-3.log | |
| 空数据 show 输出 `(empty)` 且退出码 0 | show-empty.log | |
| show 每行 `序号\t正文`, 从 1 连续, 顺序一致 | show-3.log, show-3-fields.log | |

全部满足才算本轮两个入口通过. 任一条不满足: 记录证据路径和实际输出, 判失败, 不改产品来迁就配方.

## 清理

```bash
"$CAP" cleanup -- bash -c "rm -rf '$WORK' && echo cleaned"
git status --porcelain
```

期望: `cleanup.log` 退出码 0 并输出 `cleaned`; `git status --porcelain` 为空 (或只列出本配方目录, 如果它尚未提交). 证据目录 `$EVIDENCE` 保留到报告写完, 之后可自行 `rm -rf "$EVIDENCE"`.

## 未验证与边界

- `export`: 本轮非目标, 未验证.
- `status`: 只作只读实例检查, 未按功能判据验证.
- `add` 空正文, 未定义行为: 未验证.
- 多字节/特殊字符正文: 只验证了中文, 其他编码未覆盖.
- 并行写入, 大文件, 数据文件手工损坏: 未验证.
