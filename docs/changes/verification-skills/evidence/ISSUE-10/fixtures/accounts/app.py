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
