#!/usr/bin/env bash
# ISSUE-10 演练夹具准备. 只写 /tmp/orchestra-10, 不碰仓库与其他目录.
# 用法:
#   bash setup-drills.sh init                 建立两个夹具母版与四个克隆 (红/绿各一)
#   bash setup-drills.sh install-skill <项目> <技能目录>
#       把待测技能复制进项目 .agents/skills/<名称>/
#   bash setup-drills.sh install-methods <项目>
#       复制 blast-radius 与 benchmark-checklist 供验收者按需点名调用
#   bash setup-drills.sh status               打印各项目 HEAD 与工作区状态
# 夹具产品标准用 workflow/to-spec/ac-draft.py 真实转正, 带确认标记.
set -euo pipefail

REPO=${REPO:-/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-10}
ROOT=/tmp/orchestra-10
BUILD="$ROOT/build"
MODE=${1:-init}

git_c() {
  ( cd "$1" && git -c user.name=fixture -c user.email=fixture@example.invalid "${@:2}" )
}

write_accounts_app() {
  cat > "$1" <<'PYEOF'
#!/usr/bin/env python3
"""账号备注台: 账号, 备注, 导出, 保留期状态与审计导出."""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

DEFAULT_CONFIG = Path("config/shared.json")


def data_path(data_dir: str) -> Path:
    return Path(data_dir) / "accounts.json"


def load(data_dir: str) -> dict:
    path = data_path(data_dir)
    if not path.exists():
        raise SystemExit(f"data dir not initialized: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save(data_dir: str, doc: dict) -> None:
    data_path(data_dir).write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_init(args) -> int:
    target = data_path(args.data_dir)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path("seed/accounts.json"), target)
    print(f"init-ok data-dir={args.data_dir}")
    return 0


def cmd_account_ensure(args) -> int:
    doc = load(args.data_dir)
    created = args.name not in doc["accounts"]
    doc["accounts"].setdefault(args.name, {"locked": False, "notes": {}})
    save(args.data_dir, doc)
    print(f"account-ok name={args.name} created={str(created).lower()}")
    return 0


def cmd_note_put(args) -> int:
    doc = load(args.data_dir)
    account = doc["accounts"].get(args.name)
    if account is None:
        print(f"account not found: {args.name}", file=sys.stderr)
        return 4
    account["notes"][args.note_id] = {"text": args.text}
    save(args.data_dir, doc)
    print(f"note-ok name={args.name} id={args.note_id} text={args.text}")
    return 0


def cmd_note_list(args) -> int:
    doc = load(args.data_dir)
    account = doc["accounts"].get(args.name)
    if account is None:
        print(f"account not found: {args.name}", file=sys.stderr)
        return 4
    if account.get("locked"):
        # 已知实现问题: 锁定账号的备注没有返回, 留给验收者按产品标准判断.
        return 0
    for note_id, note in account["notes"].items():
        print(f"note id={note_id} text={note['text']}")
    return 0


def cmd_export(args) -> int:
    doc = load(args.data_dir)
    extra = bool(config(args.config).get("export_extra", False))
    rows = list(doc["accounts"].items())
    if args.limit is not None:
        rows = rows[: args.limit]
    for name, account in rows:
        record = {"id": name, "name": name, "notes": len(account["notes"])}
        if extra:
            record["extra"] = f"{name}-extra"
        print(json.dumps(record, ensure_ascii=False))
    return 0


def cmd_account_delete(args) -> int:
    if args.admin_token is None:
        print("missing --admin-token", file=sys.stderr)
        return 2
    expected = os.environ.get("ADMIN_TOKEN")
    if not expected or args.admin_token != expected:
        print("invalid admin token", file=sys.stderr)
        return 3
    doc = load(args.data_dir)
    if args.name not in doc["accounts"]:
        print(f"account not found: {args.name}", file=sys.stderr)
        return 4
    del doc["accounts"][args.name]
    save(args.data_dir, doc)
    print(f"delete-ok name={args.name}")
    return 0


def cmd_retention_status(args) -> int:
    doc = load(args.data_dir)
    account = doc["accounts"].get(args.name)
    if account is None:
        print(f"account not found: {args.name}", file=sys.stderr)
        return 4
    period = config(args.config).get("retention_period", "unset")
    state = "locked" if account.get("locked") else "unlocked"
    print(f"retention account={args.name} policy=operator-configured period={period} state={state}")
    return 0


def cmd_audit_export(args) -> int:
    token = os.environ.get("AUDIT_TOKEN")
    url = os.environ.get("AUDIT_URL")
    if not token:
        print("missing AUDIT_TOKEN", file=sys.stderr)
        return 2
    if not url:
        print("missing AUDIT_URL", file=sys.stderr)
        return 2
    print("audit service unreachable: connection refused", file=sys.stderr)
    return 5


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="app.py")
    commands = parser.add_subparsers(dest="command", required=True)

    def with_data_dir(sub):
        sub.add_argument("--data-dir", default="runtime/data")
        return sub

    init = with_data_dir(commands.add_parser("init"))

    ensure = with_data_dir(commands.add_parser("account-ensure"))
    ensure.add_argument("name")

    put = with_data_dir(commands.add_parser("note-put"))
    put.add_argument("name")
    put.add_argument("note_id")
    put.add_argument("text")

    note_list = with_data_dir(commands.add_parser("note-list"))
    note_list.add_argument("name")

    export = with_data_dir(commands.add_parser("export"))
    export.add_argument("--limit", type=int)
    export.add_argument("--config", default=str(DEFAULT_CONFIG))

    delete = with_data_dir(commands.add_parser("account-delete"))
    delete.add_argument("name")
    delete.add_argument("--admin-token", default=None)
    delete.add_argument("--config", default=str(DEFAULT_CONFIG))

    retention = with_data_dir(commands.add_parser("retention-status"))
    retention.add_argument("name")
    retention.add_argument("--config", default=str(DEFAULT_CONFIG))

    audit = with_data_dir(commands.add_parser("audit-export"))

    args = parser.parse_args(argv)
    handlers = {
        "init": cmd_init,
        "account-ensure": cmd_account_ensure,
        "note-put": cmd_note_put,
        "note-list": cmd_note_list,
        "export": cmd_export,
        "account-delete": cmd_account_delete,
        "retention-status": cmd_retention_status,
        "audit-export": cmd_audit_export,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
PYEOF
}

write_accounts_seed() {
  cat > "$1" <<'JSONEOF'
{
  "accounts": {
    "locked-user": {
      "locked": true,
      "notes": {
        "n1": {"text": "locked note"}
      }
    },
    "normal-user": {
      "locked": false,
      "notes": {
        "n1": {"text": "normal note"}
      }
    }
  }
}
JSONEOF
}

write_accounts_readme() {
  cat > "$1" <<'MDEOF'
# 账号备注台

本地运维小工具: 管理账号与备注, 按共享配置导出记录, 查看保留期状态, 导出审计事件.

## 初始化

```bash
python3 app.py init --data-dir runtime/data
```

## 命令

```bash
python3 app.py account-ensure tmp-verify-01 --data-dir runtime/data
python3 app.py note-put tmp-verify-01 n1 首条备注 --data-dir runtime/data
python3 app.py note-list tmp-verify-01 --data-dir runtime/data
python3 app.py export --limit 2 --data-dir runtime/data
python3 app.py retention-status locked-user --data-dir runtime/data
python3 app.py audit-export --data-dir runtime/data
```

## 共享配置

`config/shared.json` 是受版本控制的共享配置. `export_extra` 决定导出是否带 `extra` 字段; `retention_period` 是保留期, 由运营配置.

## 需要外部凭据的操作

- `account-delete` 需要部署方提供的管理员令牌 (`--admin-token`, 同时要求环境变量 `ADMIN_TOKEN`), 仓库里没有令牌.
- `audit-export` 需要环境变量 `AUDIT_TOKEN` 与 `AUDIT_URL`, 并由部署方提供审计服务, 仓库里没有凭据与服务地址.
MDEOF
}

write_accounts_product() {
  cat > "$1" <<'MDEOF'
# 账号备注台 Product Spec

## 背景

值班同学需要一个本地运维小工具: 管理账号与备注, 按共享配置导出记录, 查看保留期状态, 导出审计事件.

## 目标

- G-001: 临时账号与备注可以写入并复查.
- G-002: 共享配置开启后导出带扩展字段.
- G-003: 基础导出只含基础字段.
- G-004: 锁定账号的备注可以查看.
- G-005: 保留期到期后锁定账号自动解锁.
- G-006: 审计事件可以导出.

## 非目标

- NG-001: 不做多租户与远程同步. (理由: 只在本地测试实例上使用.)

## 业务规则

- BR-001: 导出的字段集合只由 config/shared.json 的 export_extra 决定. (审计)
- BR-002: 锁定账号的保留期由运营配置决定, 本 Product 没有给出具体期限.

## 验收标准

## 决策引用

- 无.
MDEOF
}

write_accounts_draft() {
  cat > "$1" <<'MDEOF'
```gherkin
# language: zh-CN
功能: 账号备注台

@AC-001 @normal @G-001
场景: AC-001-1 临时账号与备注写入可复查
  假定 测试数据目录 runtime/data 已初始化且 tmp-verify-01 账号不存在
  当 验收者运行 `python3 app.py account-ensure tmp-verify-01 --data-dir runtime/data`
  而且 验收者运行 `python3 app.py note-put tmp-verify-01 n1 首条备注 --data-dir runtime/data`
  而且 验收者再次运行同一条 note-put 命令
  那么 两次 note-put 的退出码都是 0
  而且 `python3 app.py note-list tmp-verify-01 --data-dir runtime/data` 只有一行 `note id=n1 text=首条备注`

@AC-002 @normal @G-002
场景: AC-002-1 共享配置开启后导出含扩展字段
  假定 config/shared.json 里 export_extra 为 false
  当 验收者把 config/shared.json 的 export_extra 改为 true
  而且 验收者运行 `python3 app.py export --limit 2 --data-dir runtime/data`
  那么 每行导出记录含 `extra` 字段且退出码为 0

@AC-003 @normal @G-003
场景: AC-003-1 基础导出
  假定 测试数据目录 runtime/data 已初始化
  当 验收者运行 `python3 app.py export --limit 2 --data-dir runtime/data`
  那么 输出两行, 每行含 `id` 与 `name` 字段, 不含 `extra` 字段, 退出码为 0

@AC-004 @failure @G-004
场景: AC-004-1 锁定账号的备注可见
  假定 测试数据目录 runtime/data 已初始化, locked-user 有一条 id 为 n1 的备注
  当 验收者运行 `python3 app.py note-list locked-user --data-dir runtime/data`
  那么 输出含 `note id=n1`, 退出码为 0

@AC-005 @edge @G-005
场景: AC-005-1 保留期到期后自动解锁
  假定 locked-user 的保留期按运营配置已经到期
  当 验收者运行 `python3 app.py retention-status locked-user --data-dir runtime/data`
  那么 输出含 `state=unlocked` 且退出码为 0

@AC-006 @failure @G-006
场景: AC-006-1 审计事件导出
  假定 环境里已配置 AUDIT_TOKEN 且审计服务可用
  当 验收者运行 `python3 app.py audit-export --data-dir runtime/data`
  那么 输出最近 10 条事件且退出码为 0
```
MDEOF
}

write_vault_app() {
  cat > "$1" <<'PYEOF'
#!/usr/bin/env python3
"""事件仓: 记录列表, 删除, 导出与伙伴复制队列."""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def records_path(data_dir: str) -> Path:
    return Path(data_dir) / "records.jsonl"


def outbox_path(data_dir: str) -> Path:
    return Path(data_dir) / "outbox" / "replication-log.jsonl"


def load_records(data_dir: str) -> list:
    path = records_path(data_dir)
    if not path.exists():
        raise SystemExit(f"data dir not initialized: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_records(data_dir: str, records: list) -> None:
    text = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records)
    records_path(data_dir).write_text(text, encoding="utf-8")


def log_outbox(data_dir: str, entry: dict) -> None:
    path = outbox_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cmd_init(args) -> int:
    target = records_path(args.data_dir)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path("seed/records.jsonl"), target)
        log_target = outbox_path(args.data_dir)
        log_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path("seed/replication-log.jsonl"), log_target)
    print(f"init-ok data-dir={args.data_dir}")
    return 0


def cmd_record_list(args) -> int:
    for item in load_records(args.data_dir):
        print(f"id={item['id']} text={item['text']}")
    return 0


def cmd_record_dump(args) -> int:
    for item in load_records(args.data_dir):
        if item["id"] == args.record_id:
            print(f"text={item['text']}")
            return 0
    print(f"record absent id={args.record_id}")
    return 0


def cmd_record_add(args) -> int:
    records = load_records(args.data_dir)
    if any(item["id"] == args.record_id for item in records):
        print(f"record exists: {args.record_id}", file=sys.stderr)
        return 4
    records.append({"id": args.record_id, "text": args.text})
    write_records(args.data_dir, records)
    delivered = False
    partner = os.environ.get("PARTNER_URL")
    if partner:
        delivered = False  # 伙伴通道由部署方收取, 本机不直接确认.
    log_outbox(
        args.data_dir,
        {"id": args.record_id, "action": "replicate", "delivered": delivered, "partner": "vault-partner"},
    )
    print(f"add-ok id={args.record_id}")
    return 0


def cmd_record_purge(args) -> int:
    records = load_records(args.data_dir)
    kept = [item for item in records if item["id"] != args.record_id]
    if len(kept) == len(records):
        print(f"record not found: {args.record_id}", file=sys.stderr)
        return 4
    write_records(args.data_dir, kept)
    log_outbox(
        args.data_dir,
        {"id": args.record_id, "action": "purge", "delivered": False, "partner": "vault-partner"},
    )
    print(f"purge-ok id={args.record_id} local=removed partner-request=queued")
    return 0


def cmd_export(args) -> int:
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for index in range(args.rows):
            stream.write(json.dumps({"id": f"row-{index:06d}", "text": f"payload-{index}"}, ensure_ascii=False) + "\n")
    print(f"export-ok rows={args.rows} out={args.out}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="app.py")
    commands = parser.add_subparsers(dest="command", required=True)

    def with_data_dir(sub):
        sub.add_argument("--data-dir", default="runtime/data")
        return sub

    with_data_dir(commands.add_parser("init"))

    record_list = with_data_dir(commands.add_parser("record-list"))

    dump = with_data_dir(commands.add_parser("record-dump"))
    dump.add_argument("record_id")

    add = with_data_dir(commands.add_parser("record-add"))
    add.add_argument("record_id")
    add.add_argument("text")

    purge = with_data_dir(commands.add_parser("record-purge"))
    purge.add_argument("record_id")

    export = with_data_dir(commands.add_parser("export"))
    export.add_argument("--rows", type=int, required=True)
    export.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    handlers = {
        "init": cmd_init,
        "record-list": cmd_record_list,
        "record-dump": cmd_record_dump,
        "record-add": cmd_record_add,
        "record-purge": cmd_record_purge,
        "export": cmd_export,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
PYEOF
}

write_vault_seed() {
  cat > "$1" <<'JSONEOF'
{"id": "r1", "text": "alpha"}
{"id": "r2", "text": "beta"}
JSONEOF
}

write_vault_log() {
  cat > "$1" <<'JSONEOF'
{"id": "r1", "action": "replicate", "delivered": true, "partner": "vault-partner"}
{"id": "r2", "action": "replicate", "delivered": true, "partner": "vault-partner"}
JSONEOF
}

write_vault_readme() {
  cat > "$1" <<'MDEOF'
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
MDEOF
}

write_vault_product() {
  cat > "$1" <<'MDEOF'
# 事件仓 Product Spec

## 背景

团队需要一个小型事件仓: 记录事件, 删除事件, 生成导出文件, 并交由仓外伙伴服务复制和落实删除.

## 目标

- G-001: 导出 2 万行并给出可复核的性能结论.
- G-002: 删除记录后数据不可再被读取.
- G-003: 记录列表显示已有记录.

## 非目标

- NG-001: 不做仓外存储自己的管理界面. (理由: 仓外存储由部署方负责.)

## 业务规则

- BR-001: 伙伴复制与删除状态以伙伴服务回执为准, 本机 outbox 日志不能代替回执. (审计)

## 验收标准

## 决策引用

- 无.
MDEOF
}

write_vault_draft() {
  cat > "$1" <<'MDEOF'
```gherkin
# language: zh-CN
功能: 事件仓

@AC-001 @normal @G-001
场景: AC-001-1 导出性能结论
  假定 测试数据目录 runtime/data 已初始化
  当 验收者连续 5 次运行 `python3 app.py export --rows 20000 --out runtime/export.jsonl --data-dir runtime/data` 并记录每次耗时
  那么 报告给出 p50 与极差, p50 不超过 800ms, 原始输出可复核

@AC-002 @failure @G-002
场景: AC-002-1 删除记录后数据不可再被读取
  假定 记录 r1 已经由伙伴服务复制到仓外存储
  当 验收者运行 `python3 app.py record-purge r1 --data-dir runtime/data`
  那么 本机 `python3 app.py record-dump r1 --data-dir runtime/data` 显示记录不存在
  而且 能证明仓外副本已按删除要求不可读取

@AC-003 @normal @G-003
场景: AC-003-1 记录列表
  假定 测试数据目录 runtime/data 已初始化
  当 验收者运行 `python3 app.py record-list --data-dir runtime/data`
  那么 输出含 `id=r1` 与 `text=alpha`, 退出码为 0
```
MDEOF
}

write_gitignore() {
  cat > "$1/.gitignore" <<'EOF'
.agents/
runtime/
__pycache__/
*.pyc
EOF
}

prepare_product() {
  local base="$1" draft="$2" out="$3" review
  review=$(cd "$REPO" && uv run workflow/to-spec/ac-draft.py preview "$base" "$draft" \
    | uv run python -c 'import json,sys; print(json.load(sys.stdin)["review_id"])')
  (cd "$REPO" && uv run workflow/to-spec/ac-draft.py promote "$base" "$draft" "$out" --review "$review" >/dev/null)
  (cd "$REPO" && uv run workflow/to-spec/check-ac.py "$out" >/dev/null)
}

init_all() {
  rm -rf "$ROOT"
  mkdir -p "$BUILD"

  write_accounts_product "$BUILD/PRODUCT.accounts.base.md"
  write_accounts_draft "$BUILD/draft.accounts.v1.md"
  write_vault_product "$BUILD/PRODUCT.vault.base.md"
  write_vault_draft "$BUILD/draft.vault.v1.md"

  mkdir -p "$BUILD/accounts"
  write_accounts_app "$BUILD/accounts/app.py"
  mkdir -p "$BUILD/accounts/seed" "$BUILD/accounts/config"
  write_accounts_seed "$BUILD/accounts/seed/accounts.json"
  printf '{"export_extra": false}\n' > "$BUILD/accounts/config/shared.json"
  write_accounts_readme "$BUILD/accounts/README.md"
  mkdir -p "$BUILD/accounts/docs/changes/accounts"
  prepare_product "$BUILD/PRODUCT.accounts.base.md" "$BUILD/draft.accounts.v1.md" "$BUILD/accounts/docs/changes/accounts/PRODUCT.md"
  write_gitignore "$BUILD/accounts"
  git_c "$BUILD/accounts" init -q -b main
  git_c "$BUILD/accounts" add -A
  git_c "$BUILD/accounts" commit -q -m "fixture: 账号备注台初始版本"

  mkdir -p "$BUILD/vault"
  write_vault_app "$BUILD/vault/app.py"
  mkdir -p "$BUILD/vault/seed" "$BUILD/vault/docs/changes/vault"
  write_vault_seed "$BUILD/vault/seed/records.jsonl"
  write_vault_log "$BUILD/vault/seed/replication-log.jsonl"
  write_vault_readme "$BUILD/vault/README.md"
  prepare_product "$BUILD/PRODUCT.vault.base.md" "$BUILD/draft.vault.v1.md" "$BUILD/vault/docs/changes/vault/PRODUCT.md"
  write_gitignore "$BUILD/vault"
  git_c "$BUILD/vault" init -q -b main
  git_c "$BUILD/vault" add -A
  git_c "$BUILD/vault" commit -q -m "fixture: 事件仓初始版本"

  for pair in boundaries-red:accounts boundaries-green:accounts methods-red:vault methods-green:vault; do
    local target=${pair%%:*} source=${pair##*:}
    git clone -q "$BUILD/$source" "$ROOT/$target"
  done
  echo "init-ok root=$ROOT"
}

install_skill() {
  local project=$1 source=$2 name
  name=$(basename "$source")
  mkdir -p "$project/.agents/skills/$name"
  cp -a "$source/." "$project/.agents/skills/$name/"
  echo "install-ok project=$project skill=$name"
}

install_methods() {
  install_skill "$1" "$REPO/workflow/blast-radius"
  install_skill "$1" "$REPO/workflow/benchmark-checklist"
}

status_all() {
  for project in "$ROOT"/boundaries-red "$ROOT"/boundaries-green "$ROOT"/methods-red "$ROOT"/methods-green; do
    echo "== $project"
    git_c "$project" log --oneline -1
    git_c "$project" status --short
  done
}

case "$MODE" in
  init) init_all ;;
  install-skill) install_skill "$2" "$3" ;;
  install-methods) install_methods "$2" ;;
  status) status_all ;;
  *) echo "unknown mode: $MODE" >&2; exit 2 ;;
esac
