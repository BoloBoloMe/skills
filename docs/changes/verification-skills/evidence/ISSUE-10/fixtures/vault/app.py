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
