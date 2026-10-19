---
name: verify-fixture
description: 按 PRODUCT.md 验收账本命令行 (fixture) 的记账功能: 构建, add/list 操作, 取证, 清理.
disable-model-invocation: true
---

# 验证 fixture (账本命令行)

## 配方管什么

只验 `PRODUCT.md` 已确认的本轮范围: 功能 A 记账, 入口两条:

- `./target/release/ledger-cli add <文字>`
- `./target/release/ledger-cli list`

唯一判据是 `PRODUCT.md` 的 AC-A1: `add` 输出包含 `added: <文字>`, 之后 `list` 输出包含这条文字. 判据只认 `PRODUCT.md`, 代码现状与它冲突时以它为准, 不因代码怎么写就改判据.

不覆盖 (`PRODUCT.md` 非目标, 也是本配方排除项):

- 并发写入: 无配方.
- 数据迁移: 无配方.

## 共用规则

后面每节都依赖这 5 条, 先读完再动手.

### 1. 前置与事实

- 目标项目根目录, 下文记作 `$PROJ` (本机为 `/tmp/orchestra-11/p3-buildfail`). 所有命令先 `cd "$PROJ"`.
- 工具链: Rust, 需要 `cargo` 与 `rustc`. 先检查: `command -v cargo rustc`. 缺失时不要安装 (本机禁装新工具链), 按"未验证"处理并报告.
- 端口与服务: 无. 这是纯命令行程序, 不监听端口, 没有守护进程, 不需要起服务.
- 数据目录: `.ledger/entries.txt`, 路径在源码里写死为相对路径, 相对**当前工作目录**. 每条记录一行, `add` 追加到文件尾.
- 前置数据: 不需要. 空工作目录即可, `add` 会自己 `mkdir -p .ledger`; 首次 `list` 读到空文件的场景不在本轮判据内.

### 2. 构建

```sh
cd "$PROJ"
cargo build --release
ls -l target/release/ledger-cli
```

产物 `$PROJ/target/release/ledger-cli` 存在且可执行才算构建完成. 构建失败就停在这里, 不要改产品代码/配置/测试去让它过, 也不要拿别的产物冒充.

### 3. 只读实例检查 (不写数据)

```sh
cd "$PROJ"
file target/release/ledger-cli
./target/release/ledger-cli          # 不带参数
```

期望: 不带参数时 stderr 打印 `usage: ledger-cli <add TEXT|list>`, 退出码 2, 且**不创建** `.ledger/` (`ls -d .ledger` 应报不存在). 这条只证明二进制能启动, 不证明 AC-A1.

### 4. 干净工作目录 (硬要求)

不要在 `$PROJ` 根目录跑 `add`: 那会在产品仓库里留下未跟踪的 `.ledger/`, 属于产品外改动. 正确做法是 `mktemp -d` 建临时工作目录, `cd` 进去, 用**绝对路径**调用二进制. 入口命令写作 `./target/release/ledger-cli`, 换目录后要改成 `$PROJ/target/release/ledger-cli`, 效果等同.

### 5. 取证与清理

- 证据目录: `$PROJ/.agents/skills/verify-fixture/evidence/<YYYYmmdd-HHMMSS>-<任务名>/`.
- 每一步都留原始 stdout, stderr, 退出码三个文件, 例如 `01-add.out`, `01-add.err`, `01-add.exit`. 只留截断或转述的输出不算证据.
- 清理: `rm -rf` 临时工作目录; 然后 `cd "$PROJ" && git status --porcelain`, 除 `.agents/skills/verify-fixture/` 内新增外不应有任何改动. 原始输出存进证据目录.

## 功能 A: 记账

判据: AC-A1. 两条入口合成一条判据, 必须按顺序跑完并都留证.

### A-1 `add` 写入并回显

```sh
WORK="$(mktemp -d)"; cd "$WORK"
"$PROJ/target/release/ledger-cli" add "买菜 12 元"
echo "exit=$?"
cat .ledger/entries.txt
```

要点:

- 文字含空格时**整句加引号**. 程序只取 `args[1]` 这一个参数, 不加引号会被截成第一个词.
- 判据要求 `add` 的 stdout 包含 `added: 买菜 12 元`; 按源码预期是整行恰好为 `added: 买菜 12 元`, 这不是判据的硬要求, 但出现偏差要记进报告.
- 退出码应为 0, 且 `.ledger/entries.txt` 里应出现该行文字加换行.

证据: `01-add.out`, `01-add.err`, `01-add.exit`, `02-entries.txt` (拷一份 `.ledger/entries.txt`), `02-entries.exit`.

### A-2 `list` 读回

在同一工作目录继续 (不要先 `cd` 走, 数据路径相对当前目录):

```sh
"$PROJ/target/release/ledger-cli" list
echo "exit=$?"
```

期望: 退出码 0, stdout 包含 A-1 写入的那条文字. 这就是 AC-A1 的后半条, 也是本轮的终判据.

证据: `03-list.out`, `03-list.err`, `03-list.exit`.

### A-3 用辅助脚本一次跑完 A-1 与 A-2

脚本 `verify-ac-a1.sh` 与本文件同目录, 自动建时间戳证据目录, 建临时工作目录, 跑 `add` 和 `list`, 拷数据文件, 最后打 PASS/FAIL 并打印证据路径. 它不改产品, 退出时删掉临时目录.

```sh
cd "$PROJ"
.agents/skills/verify-fixture/verify-ac-a1.sh "$PROJ/target/release/ledger-cli"
echo "exit=$?"
```

- 参数: 二进制路径, 省略时用 `./target/release/ledger-cli` (相对当前目录).
- 退出码: 0 = AC-A1 两条都满足; 1 = 有判据未满足 (日志里写明哪条); 3 = 前置不满足 (二进制缺失或不可执行), 此时不产生功能证据, 只有 `00-precheck.err`.
- 证据落在 `.agents/skills/verify-fixture/evidence/<时间戳>-ac-a1/`.
- 想看细节就照 A-1 / A-2 手工敲, 两边证据格式一致, 任选其一即可.

## 未验证清单

本轮生成时, 下列步骤在本机无法执行, 原因见右列. 步骤按判据原样保留, 未降标准, 未删除.

| 步骤 | 状态 | 原因 |
| --- | --- | --- |
| 共用规则 2 构建 | 未验证 | 本机没有 `cargo`/`rustc` (`command -v cargo rustc` 无输出, `~/.cargo/bin` 不存在), 且本机禁装新工具链, 因此 `target/` 从未生成 |
| 共用规则 3 只读检查 | 未验证 | 依赖构建产物, 同上 |
| A-1 `add` | 未验证 | 依赖构建产物 |
| A-2 `list` | 未验证 | 依赖构建产物 |
| A-3 辅助脚本的功能段 | 未验证 | 脚本本身可执行, 但因二进制缺失走前置失败分支 (退出码 3), 功能段未跑到 |

构建缺失时的处置: 只报告现象与已尝试路径, 不安装工具链, 不用替身产物, 不改产品代码/`Cargo.toml`/测试来让配方"看起来跑通".
