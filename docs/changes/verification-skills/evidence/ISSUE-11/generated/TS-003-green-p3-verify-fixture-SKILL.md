---
name: verify-fixture
description: "账本命令行 ledger-cli 本轮记账入口的实跑配方: 构建, 空数据起步, add/list 操作, 取证与清理."
disable-model-invocation: true
---

# verify-fixture

判据唯一来源是项目根目录的 `PRODUCT.md` (状态: 已确认). 本配方只回答怎么跑, 看什么, 证据放哪. 代码现状与 `PRODUCT.md` 冲突时以 `PRODUCT.md` 为准.

## 本次覆盖

- 功能 A 记账, 入口两条: `add <文字>`, `list`.
- 对应判据: AC-A1 `add` 输出含 `added: <文字>`, 之后 `list` 输出含这条文字.
- 排除: 并发写入, 数据迁移 (`PRODUCT.md` 明确列为本轮非目标), 以及 `PRODUCT.md` 未列出的任何其他行为. 不验收, 不铺地图.

## 共用规则

1. 应用与构建
   - 应用名 `ledger-cli`, 包名与版本见 `Cargo.toml` (`0.1.0`).
   - 构建命令: `cargo build --release`, 产物 `./target/release/ledger-cli`.
   - 前置: 可用的 Rust 工具链 (`cargo`, `rustc`).
   - 现状: 本机没有 `cargo` / `rustc`, 且本轮禁止安装. 因此构建及以下全部运行步骤均标 **未验证**. 不许装工具链, 不许用替身产物, 不许改产品代码或配置来让配方看起来跑通.
2. 空数据起点
   - 数据在项目根目录的 `.ledger/entries.txt` (源码观察, 未运行验证).
   - 开跑前确认没有旧数据: `ls -d .ledger` 应报 `No such file or directory`. 不要预先创建 `.ledger` 或 `entries.txt`, 也不要在开跑前手工写入内容.
3. 只读实例检查 (不写入, 不改数据)
   - 本应用没有网络端口, 没有常驻进程, 没有服务归属检查.
   - 检查项: 直接运行 `./target/release/ledger-cli` (无参数), 期望 stderr 输出 `usage: ledger-cli <add TEXT|list>`, 退出码 2; `./target/release/ledger-cli --version` 源码里没有专门分支, 同样落到 usage 分支退出 2 (源码观察, 未验证). 版本以 `Cargo.toml` 的 `version = "0.1.0"` 为准, 不要靠 `--version` 取版本.
4. 真实入口操作
   - 只用命令行 `add` / `list` 完成写入与读出.
   - 不许手工编辑 `.ledger/entries.txt`, 不许用 `cat` 读文件冒充 `list` 的结果, 不许直连文件造前置数据.
5. 取证
   - 证据放项目目录之外: `EV=/tmp/verify-fixture-evidence/$(date +%Y%m%d-%H%M%S)`. 这样项目 `git status` 保持干净.
   - 每条命令保留 stdout+stderr 和退出码. 用 `set -o pipefail` 加 `${PIPESTATUS[0]}`, 因为管道后 `$?` 是 `tee` 的.
   - 日志命名固定: `add.log`, `list.log`, `checks.log`.
6. 清理
   - 跑完删掉本轮生成的数据: `rm -rf .ledger`.
   - 再跑 `git status --porcelain`: 除验证目录 (`.agents/skills/verify-fixture/`) 外不应有任何改动.
   - `/tmp/verify-fixture-evidence/` 下的证据默认保留, 除非操作者要求删除.
7. 失败处理
   - 构建或启动不了: 记录原始报错和退出码, 把受影响步骤原样保留并标未验证, 不降标准, 不删步骤.

## 功能 A 记账

### 前置

- 已完成 `cargo build --release`, 且 `test -x ./target/release/ledger-cli` 通过 (**未验证**: 本机无工具链).
- `.ledger` 不存在 (空数据起点).
- 测试文字用不含空格和 shell 元字符的 ASCII, 避免引号歧义. 本配方统一用 `coffee-3.5`.

```sh
set -o pipefail
EV=/tmp/verify-fixture-evidence/$(date +%Y%m%d-%H%M%S)
mkdir -p "$EV"
{
  echo "# $(date -Is) pwd=$(pwd)"
  cargo --version; rustc --version
  test -x ./target/release/ledger-cli && echo "binary: executable" || echo "binary: MISSING"
  ls -d .ledger 2>&1
} 2>&1 | tee "$EV/checks.log"
```

期望: `cargo --version` / `rustc --version` 有版本输出, `binary: executable`, `ls -d .ledger` 报不存在. 当前环境下前两项必然失败, 见文末未验证清单.

### A-1 `add`: 写入一条并回显

```sh
./target/release/ledger-cli add coffee-3.5 2>&1 | tee "$EV/add.log"
echo "exit=${PIPESTATUS[0]}" | tee -a "$EV/add.log"
```

- 操作: 传入 `add` 和文字 `coffee-3.5`.
- 判据满足条件: `add.log` 中出现 `added: coffee-3.5`, 退出码 0. 这是 AC-A1 的前半.
- 旁证 (不是判据): 此时 `.ledger/entries.txt` 内容为一行 `coffee-3.5` (源码观察, 未验证). 可以看, 但结论必须来自 `add` 的输出.
- 证据: `$EV/add.log` (含 stdout, stderr, 退出码).

### A-2 `list`: 读回刚写的文字

```sh
./target/release/ledger-cli list 2>&1 | tee "$EV/list.log"
echo "exit=${PIPESTATUS[0]}" | tee -a "$EV/list.log"
grep -F 'coffee-3.5' "$EV/list.log" | tee "$EV/grep.log"
```

- 操作: 紧接着 A-1 运行 `list`, 中间不做其他写入.
- 判据满足条件: `list.log` 的输出中包含 `coffee-3.5`, 且 `grep` 命中 (退出码 0), `list` 退出码 0. 这是 AC-A1 的后半.
- 证据: `$EV/list.log`, `$EV/grep.log` (命中行).

### 结论判定

- 通过: `add.log` 有 `added: coffee-3.5` 且 `grep.log` 有命中行, 两份日志退出码均为 0.
- 失败: 任一条缺失或退出码非 0. 附 `add.log` 与 `list.log` 原文, 不修改产品去凑通过.

### 清理

```sh
rm -rf .ledger
git status --porcelain | tee "$EV/git-status.log"
```

期望: `git-status.log` 里除 `.agents/skills/verify-fixture/` 外没有其他路径.

## 现有测试入口

- `README.md` 给的入口是 `cargo test`. **未验证**: 本机无 `cargo`.
- 源码观察: `src/main.rs` 内没有任何 `#[test]`, 即使能构建也没有测试用例. 因此本配方不把 `cargo test` 当判据, 判据只看上面两条命令行入口.

## 未验证清单

- 构建 (`cargo build --release`): 未验证. 原因: 本机没有 `cargo` / `rustc`, 本轮禁止安装. 已尝试一次, 原始输出 `bash: 行 1: cargo: 未找到命令`, 退出码 127, 未生成 `target/`.
- `add`, `list`, 无参数 usage 检查: 全部未验证. 原因: 依赖构建产物, 构建未成功.
- `cargo test`: 未验证, 原因同上.
- 数据文件路径 `.ledger/entries.txt` 与 `added: <文字>` 文案: 源码观察所得, 未做运行验证; 判据仍以 `PRODUCT.md` 的 AC-A1 为准.
- 可选输入 `TECHNICAL.md`, `EXECUTION.md`, `PRODUCT.md` 以外的产品文档: 未提供, 不影响本配方.
