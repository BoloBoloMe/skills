#!/usr/bin/env python3
"""notes-cli: 一个极小的笔记命令行工具."""

import json
import sys
from pathlib import Path

VERSION = "0.3.0"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "notes.json"
INCLUDE_ARCHIVED_IN_SEARCH = False


def load():
    if not DATA.exists():
        return []
    return json.loads(DATA.read_text(encoding="utf-8"))


def save(notes):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def next_id(notes):
    return max((note["id"] for note in notes), default=0) + 1


def main(argv):
    if not argv:
        print("usage: app.py <add|list|search|archive|export|doctor> ...", file=sys.stderr)
        return 2
    command, rest = argv[0], argv[1:]
    notes = load()

    if command == "add":
        if not rest:
            print("缺少笔记正文", file=sys.stderr)
            return 2
        note = {"id": next_id(notes), "text": " ".join(rest), "archived": False}
        notes.append(note)
        save(notes)
        print(f"added {note['id']}: {note['text']}")
        return 0

    if command == "list":
        for note in notes:
            mark = " [archived]" if note["archived"] else ""
            print(f"{note['id']}\t{note['text']}{mark}")
        return 0

    if command == "search":
        if not rest:
            print("缺少关键词", file=sys.stderr)
            return 2
        keyword = rest[0]
        hits = []
        for note in notes:
            if keyword not in note["text"]:
                continue
            if note["archived"] and not INCLUDE_ARCHIVED_IN_SEARCH:
                continue
            hits.append(note)
        for note in hits:
            print(f"{note['id']}\t{note['text']}")
        print(f"matches: {len(hits)}")
        return 0

    if command == "archive":
        if not rest:
            print("缺少笔记编号", file=sys.stderr)
            return 2
        target = int(rest[0])
        for note in notes:
            if note["id"] == target:
                note["archived"] = True
                save(notes)
                print(f"archived {target}")
                return 0
        print(f"note not found: {target}", file=sys.stderr)
        return 1

    if command == "export":
        if not rest:
            print("缺少导出路径", file=sys.stderr)
            return 2
        target = Path(rest[0])
        target.write_text("".join(f"{note['id']}\t{note['text']}\n" for note in notes), encoding="utf-8")
        print(f"exported {len(notes)} notes to {target}")
        return 0

    if command == "doctor":
        print(f"notes-cli {VERSION}")
        print(f"data_path: {DATA}")
        print(f"notes: {len(notes)}")
        return 0

    if command == "--version":
        print(VERSION)
        return 0

    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
