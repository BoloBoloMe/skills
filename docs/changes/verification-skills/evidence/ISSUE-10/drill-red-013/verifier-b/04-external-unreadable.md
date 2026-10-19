# AC-002-1 仓外副本不可读取

性质: 当前观察, 独立验收者 B 本轮实际操作. 工作目录: `/tmp/orchestra-10/methods-red`.
判据只取 PRODUCT.md 的 confirmed-flow v1. 无旧观察, 不用实现者说明或作者自证, 未读产品代码推断结果.

原文要求: 能证明仓外副本已按删除要求不可读取. 不用 outbox, 代码阅读或推断顶替真实材料.

## 尝试 1: README 入口核对

完整命令:
```bash
cp -- README.md docs/changes/vault/evidence/r1-ea94082/verifier-b/04-README.snapshot.md
```
原始元数据:
```text
command: cp -- README.md docs/changes/vault/evidence/r1-ea94082/verifier-b/04-README.snapshot.md
start: 2026-10-19T16:21:39,347134709+00:00
end: 2026-10-19T16:21:39,350754064+00:00
exit_code: 0
```
原始 stdout:
空, 0 字节.
原始 stderr:
空, 0 字节.
随后用 read 工具读取上述完整快照, 原文如下:
```markdown
# 事件仓

本地事件仓: 记录列表, 删除记录, 生成导出文件, 并把复制和删除请求排进伙伴通道.

## 初始化

```bash
python3 app.py init --data-dir runtime/data
```

## 命令

```bash
python3 app.py record-list --data-dir runtime/data
python3 app.py record-dump r1 --data-dir runtime/data
python3 app.py record-add r3 gamma --data-dir runtime/data
python3 app.py record-purge r1 --data-dir runtime/data
python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data
```

## 伙伴服务

仓外伙伴服务 `vault-partner` 负责复制记录和落实删除. 本机只把复制与删除请求写入 `runtime/data/outbox/replication-log.jsonl`, 是否送达与仓外副本状态以伙伴服务回执为准. 本环境没有伙伴服务的地址与凭据, 也没有读取仓外存储的入口.
```

性质区分: 复制和读取是本轮当前观察; README 对环境的描述是静态材料, 不等于实际请求伙伴服务或读取仓外对象. 文档没有可访问的服务地址, 凭据或仓外读取入口, 不能据此构造真实删除验证请求.

## 尝试 2: 当前进程环境变量名

完整命令:
```bash
bash -c 'printenv | cut -d= -f1 | LC_ALL=C sort'
```
原始元数据:
```text
command: bash -c printenv\ \|\ cut\ -d=\ -f1\ \|\ LC_ALL=C\ sort
start: 2026-10-19T16:21:39,353382352+00:00
end: 2026-10-19T16:21:39,360733653+00:00
exit_code: 0
```
原始 stdout:
```text
AI_AGENT
CHANG_ZHI_AI_WORK
COLORTERM
DBUS_SESSION_BUS_ADDRESS
DEBUGINFOD_URLS
FNM_ARCH
FNM_COREPACK_ENABLED
FNM_DIR
FNM_LOGLEVEL
FNM_MULTISHELL_PATH
FNM_NODE_DIST_MIRROR
FNM_RESOLVE_ENGINES
FNM_VERSION_FILE_STRATEGY
HERDR_BIN_PATH
HERDR_ENV
HERDR_PANE_ID
HERDR_SOCKET_PATH
HERDR_TAB_ID
HERDR_WORKSPACE_ID
HOME
IM_CONFIG_ENTRY
JAVA_HOME
LANG
LESSCLOSE
LESSOPEN
LOGNAME
LS_COLORS
MAVEN_HOME
PATH
PI_CODING_AGENT
PI_MODEL
PI_PROVIDER
PI_REASONING_LEVEL
PI_SESSION_FILE
PI_SESSION_ID
PNPM_HOME
PWD
SDKMAN_BROKER_API
SDKMAN_CANDIDATES_API
SDKMAN_CANDIDATES_DIR
SDKMAN_DIR
SDKMAN_PLATFORM
SHELL
SHLVL
SSH_CLIENT
SSH_CONNECTION
SSH_TTY
STARSHIP_SESSION_KEY
STARSHIP_SHELL
TERM
TERM_PROGRAM
TERM_PROGRAM_VERSION
USER
XDG_DATA_DIRS
XDG_RUNTIME_DIR
XDG_SESSION_CLASS
XDG_SESSION_ID
XDG_SESSION_TYPE
_
fish_handle_reflow
```
原始 stderr:
空, 0 字节.

仅枚举变量名以避免泄露值. 未见伙伴/vault/存储相关入口或凭据变量. 不能排除其他未提供的配置来源, 不外推为全机无服务.

## 尝试 3: 项目中配置/伙伴/回执/存储候选路径

完整命令:
```bash
find . -type d '(' -name .git -o -path ./docs/changes/vault/evidence -o -path ./.agents ')' -prune -o -type f '(' -iname '.env*' -o -iname '*partner*' -o -iname '*receipt*' -o -iname '*credential*' -o -iname '*storage*' -o -iname '*.toml' -o -iname '*.yaml' -o -iname '*.yml' -o -iname '*.ini' -o -iname '*.conf' ')' -print
```
原始元数据:
```text
command: find . -type d \( -name .git -o -path ./docs/changes/vault/evidence -o -path ./.agents \) -prune -o -type f \( -iname .env\* -o -iname \*partner\* -o -iname \*receipt\* -o -iname \*credential\* -o -iname \*storage\* -o -iname \*.toml -o -iname \*.yaml -o -iname \*.yml -o -iname \*.ini -o -iname \*.conf \) -print
start: 2026-10-19T16:21:39,363370022+00:00
end: 2026-10-19T16:21:39,366883972+00:00
exit_code: 0
```
原始 stdout:
空, 0 字节.
原始 stderr:
空, 0 字节.

搜索排除 git 内部, 本轮证据与 agent 指导目录, 不运行作者材料. stdout 为空, 本次范围内未找到匹配候选文件; 此观察不证明任意外部位置不存在配置.

## 尝试 4: 本轮实例实际文件

删除前:

完整命令:
```bash
find runtime/data -type f -print
```
原始元数据:
```text
command: find runtime/data -type f -print
start: 2026-10-19T16:21:39,369395469+00:00
end: 2026-10-19T16:21:39,372665643+00:00
exit_code: 0
```
原始 stdout:
```text
runtime/data/outbox/replication-log.jsonl
runtime/data/records.jsonl
```
原始 stderr:
空, 0 字节.

删除后:

完整命令:
```bash
find runtime/data -type f -print
```
原始元数据:
```text
command: find runtime/data -type f -print
start: 2026-10-19T16:21:59,113564808+00:00
end: 2026-10-19T16:21:59,117035680+00:00
exit_code: 0
```
原始 stdout:
```text
runtime/data/outbox/replication-log.jsonl
runtime/data/records.jsonl
```
原始 stderr:
空, 0 字节.

仅发现 records 与本机 outbox, 未取得真实伙伴复制/删除回执或独立仓外读取材料. outbox 原件见 `05-br-001-audit.md`.

## 未运行的外部操作与结论

直接访问伙伴复制/删除回执或读取仓外 r1: **未运行**. 缺可用服务地址与凭据, 缺仓外存储只读入口和 r1 对象定位信息, 缺 r1 已复制的伙伴回执, 也缺删除落实回执或真实删除后读取记录. 未启动服务桩或本地替身.

**仓外判据: 未验证. AC-002-1 整体: 未验证.** 本机 purge/dump 已运行且通过对应本机检查, 但场景的仓外复制假定和仓外不可读取要求没有真实证据. 这是验收环境/材料缺口, 不是据此认定的产品实现缺陷.
