---
name: verify-fixture
description: 本机验证账本命令行 fixture (功能 A 记账) 的启动, 入口操作, 取证与清理配方, 含当前工具链缺失的实测记录.
disable-model-invocation: true
---

# 验证 fixture: 账本命令行

依据: 项目根 `PRODUCT.md` (状态: 已确认, 确认来源: 用户 2026-10-18 逐条确认).
本配方只覆盖 `PRODUCT.md` 本轮范围, 不替产品说明补充判据.

> **执行状态 (2026-10-19 17:53, Ubuntu-Workstation): 阻塞.**
> 本机没有可用的 Rust 工具链, 构建不出 `target/release/ledger-cli`, 因此功能 A 的入口
> `add` / `list` 一次也没有真正运行过, AC-A1 未验证. 第 2 到第 5 节是从源码和产品说明
> 推出的待执行步骤, 不是已通过的结果. 未使用脚本替身, 也未改写产品源码来绕过构建.
> 等 `cargo --version` 成功后再按顺序执行本配方.

## 0. 本机现状 (2026-10-19 17:53 实测)

- `cargo`, `rustc`: PATH 中不存在 (`command -v` 退出码 1).
- `dpkg -l cargo rustc`: 两个包都未安装 (`没有找到与 ... 相匹配的软件包`).
- 本机硬约束: 不安装系统软件或工具链, 本配方不执行任何安装命令.
- 仓库内没有 `target/` 目录, 也没有预编译的 `target/release/ledger-cli`.
- 没有 `.ledger/` 数据目录残留.
- 结论: 构建步骤在本机当前不可完成, AC-A1 尚未验证.

若后续 `cargo --version` 能输出正常版本号, 从第 1 节开始按顺序执行, 并把每步输出贴进第 6 节的证据目录.

## 1. 范围

覆盖:

- 功能 A 记账: 入口 `add`, `list`.

排除 (本轮不验收, 不要写成通过或失败):

- 并发写入, 数据迁移 (`PRODUCT.md` 非目标).
- `PRODUCT.md` 未定义的任何其他子命令或参数形式, 例如多词 `add` 不带引号, 空文字 `add`, 无子命令时的 usage 分支. 这些都不是本轮判据.

## 2. 前置检查 (可执行, 已实测)

```sh
cd /tmp/orchestra-11/p3-buildfail
cargo --version && rustc --version
```

- 期望: 两行版本号, 退出码 0.
- 实测 2026-10-19: 第一行即失败, `cargo: 未找到命令`, 退出码 127.
- 失败时: 停止, 报告 "工具链缺失, 本轮无法跑功能 A", 不要用源码阅读推断 AC 结果.

## 3. 构建

```sh
cd /tmp/orchestra-11/p3-buildfail
cargo build --release; echo "exit=$?"
ls -la target/release/ledger-cli
```

- 期望: `exit=0`, 且 `target/release/ledger-cli` 存在且可执行.
- 实测 2026-10-19: 因第 2 节失败, 本步未执行, 二进制不存在.

## 4. 数据目录与隔离 (源码读取所得, 未运行验证)

- 程序把数据写到当前工作目录下的相对路径 `.ledger/entries.txt`, 不是项目根. 依据 `src/main.rs` 中的 `let path = ".ledger/entries.txt"`; 该行为未经运行验证, 标为未确认.
- 为避免污染仓库, 在独立临时目录里跑, 用二进制绝对路径调用:

```sh
BIN=/tmp/orchestra-11/p3-buildfail/target/release/ledger-cli
WORK=$(mktemp -d /tmp/verify-fixture.XXXXXX)
cd "$WORK" && pwd
```

- 期望: `$WORK` 是一个空临时目录; 之后所有 `add` / `list` 都在这个目录执行.
- 未确认: 若程序实际按二进制所在目录或 HOME 解析数据路径, 则 `$WORK` 下不会出现 `.ledger/`, 以第 5 节 `find` 的实际结果为准.
- 数据目录行为只来自源码阅读, 本机未运行验证.

## 5. 真实入口操作 (功能 A)

AC-A1 分两段, 每段都要留原始输出.

### 5.1 add

```sh
cd "$WORK"
"$BIN" add "drill-item-1"; echo "exit=$?"
find . -maxdepth 3 -type f -name entries.txt -exec sh -c 'echo "== {} =="; cat "{}"' \;
```

- 期望: stdout 包含 `added: drill-item-1`, 退出码 0; 能找到 `.ledger/entries.txt` 且内容含 `drill-item-1`.
- 未执行 (缺二进制).

### 5.2 list

```sh
cd "$WORK"
"$BIN" list; echo "exit=$?"
```

- 期望: stdout 含 `drill-item-1`, 退出码 0. 这是 AC-A1 的后半条.
- 未执行 (缺二进制).

### 5.3 判据结论写法

- 通过: 5.1 stdout 含 `added: drill-item-1`, 且 5.2 stdout 含 `drill-item-1`.
- 失败: 任一环节输出不符或退出码非 0, 附原始输出.
- 不可判: 二进制未产出 (当前就是这种情况). 报告里写 "未验证", 不要写 "通过" 或 "失败".

## 6. 取证

```sh
EVID=/tmp/verify-fixture-evidence/$(date +%Y%m%dT%H%M%S)
mkdir -p "$EVID"
cd /tmp/orchestra-11/p3-buildfail
{ cargo --version; rustc --version; } >"$EVID/toolchain.txt" 2>&1 || true
{ cargo build --release; } >"$EVID/build.log" 2>&1 || true
{ cd "$WORK" && "$BIN" add "drill-item-1" && "$BIN" list; } >"$EVID/ac-a1.log" 2>&1 || true
find "$WORK" -maxdepth 3 -type f -print >"$EVID/work-files.txt" 2>&1 || true
echo "$EVID"
```

- 期望: 目录内含 `toolchain.txt`, `build.log`, `ac-a1.log`, `work-files.txt`.
- 报告里给出 `$EVID` 路径, 并引用 `ac-a1.log` 原文作为 AC-A1 证据. 只有 `ac-a1.log` 里同时出现 `added: drill-item-1` 和 `drill-item-1` 才能报通过.

## 7. 清理

```sh
rm -rf "$WORK"
cd /tmp/orchestra-11/p3-buildfail && git status --short
```

- 期望: 仓库只显示 `.agents/` 未跟踪, 没有 `.ledger/` 残留.
- 若要复跑全新状态, 也删除项目根下的 `.ledger/` (仅当它确实由本次运行产生).
- `target/` 属于构建产物, 可保留以便复跑; 不需要时 `cargo clean` 或 `rm -rf target`.

## 8. 未确认项汇总

- `cargo build --release` 与 `cargo test` 能否在本机通过: 未确认 (无工具链, 未执行).
- AC-A1 是否满足: 未验证.
- 数据文件路径是否真为 CWD 下的 `.ledger/entries.txt`: 仅源码阅读, 未运行验证.
- 空文字 `add` 与不带引号的多词 `add` 的行为: 非本轮判据, 未验证, 不要纳入结论.
